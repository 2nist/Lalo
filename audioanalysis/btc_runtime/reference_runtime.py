import os
import sys
from pathlib import Path

import numpy as np
import torch
import yaml


def _ensure_numpy_compat() -> None:
    if not hasattr(np, "float"):
        np.float = float  # type: ignore[attr-defined]
    if not hasattr(np, "int"):
        np.int = int  # type: ignore[attr-defined]
    if not hasattr(np, "complex"):
        np.complex = complex  # type: ignore[attr-defined]


def get_reference_runtime_root() -> Path:
    return Path(__file__).resolve().parents[2] / "third_party" / "BTC-ISMIR19"


def load_reference_config(config_path: Path) -> dict:
    with open(config_path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def recognize_chords(
    audio_path: str,
    model_path: Path,
    checkpoint_path: Path,
) -> list:
    _ensure_numpy_compat()
    btc_root = get_reference_runtime_root()
    if not btc_root.exists():
        raise FileNotFoundError(f"BTC-ISMIR19 source not found: {btc_root}")

    config_path = model_path / "config" / "btc_config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"BTC config not found: {config_path}")

    sys.path.insert(0, str(btc_root))
    try:
        from btc_model import BTC_model
        from utils.mir_eval_modules import audio_file_to_features, idx2voca_chord

        config = load_reference_config(config_path)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = BTC_model(config=config["model"]).to(device)

        checkpoint = torch.load(
            str(checkpoint_path),
            map_location=device,
            weights_only=False,
        )
        mean = checkpoint["mean"]
        std = checkpoint["std"]
        model.load_state_dict(checkpoint["model"])
        model.eval()

        feature, feature_per_second, _ = audio_file_to_features(audio_path, _DictAsObj(config))
        feature = feature.T
        feature = (feature - mean) / std

        n_timestep = int(config["model"]["timestep"])
        if feature.shape[0] == 0:
            return []

        num_pad = (n_timestep - (feature.shape[0] % n_timestep)) % n_timestep
        if num_pad > 0:
            feature = np.pad(feature, ((0, num_pad), (0, 0)), mode="constant", constant_values=0)

        num_instance = feature.shape[0] // n_timestep
        idx_to_chord = idx2voca_chord()
        time_unit = float(feature_per_second)

        lines = []
        start_time = 0.0
        with torch.no_grad():
            feature_tensor = torch.tensor(feature, dtype=torch.float32).unsqueeze(0).to(device)
            prev_chord = None
            for index in range(num_instance):
                self_attn_output, _ = model.self_attn_layers(
                    feature_tensor[:, n_timestep * index:n_timestep * (index + 1), :]
                )
                output = model.output_layer(self_attn_output)

                # Normalize output handling: some models return logits (floats), others
                # already return argmax indices. Compute per-timestep prediction and
                # probability (confidence) when possible.
                try:
                    logits = output[0] if isinstance(output, tuple) else output
                    probs_tensor = None
                    if torch.is_floating_point(logits):
                        # logits shape: (n_timestep, num_classes)
                        probs_tensor = torch.softmax(logits, dim=-1)
                        pred_tensor = torch.argmax(probs_tensor, dim=-1)
                    else:
                        # non-floating (already indices)
                        pred_tensor = logits
                    prediction = pred_tensor.squeeze()
                except Exception:
                    # Fallback to previous behavior
                    if isinstance(output, tuple):
                        prediction = output[0].squeeze()
                    else:
                        prediction = torch.argmax(output, dim=-1).squeeze()

                for timestep in range(n_timestep):
                    try:
                        chord_idx = int(prediction[timestep].item())
                    except Exception:
                        chord_idx = int(prediction[timestep])

                    # determine confidence for this timestep
                    conf = 1.0
                    if 'probs_tensor' in locals() and probs_tensor is not None:
                        try:
                            conf = float(probs_tensor[timestep, chord_idx].cpu().item())
                        except Exception:
                            conf = 1.0

                    if prev_chord is None:
                        prev_chord = chord_idx
                        prev_conf = conf
                        continue

                    if chord_idx != prev_chord:
                        change_time = time_unit * (n_timestep * index + timestep)
                        lines.append((start_time, change_time, idx_to_chord[prev_chord], float(prev_conf)))
                        start_time = change_time
                        prev_chord = chord_idx
                        prev_conf = conf

                    if index == num_instance - 1 and timestep + num_pad == n_timestep:
                        end_time = time_unit * (n_timestep * index + timestep)
                        if start_time != end_time:
                            lines.append((start_time, end_time, idx_to_chord[prev_chord], float(prev_conf)))
                        break

        return [
            {
                "start": float(start),
                "end": float(end),
                "chord": chord,
                "confidence": float(conf) if len(item) > 3 else 1.0,
            }
            for item in lines for (start, end, chord, *rest) in [item] for conf in ([rest[0]] if rest else [1.0])
        ]
    finally:
        try:
            sys.path.remove(str(btc_root))
        except ValueError:
            pass


class _DictAsObj:
    def __init__(self, data: dict):
        for key, value in data.items():
            if isinstance(value, dict):
                value = _DictAsObj(value)
            setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)