import importlib
import sys
from pathlib import Path

import torch

from .config import get_inference_device, load_btc_config, load_checkpoint
from .features import audio_file_to_features, ensure_numpy_compat
from .labels import idx2voca_chord
from .reference_runtime import get_reference_runtime_root


def is_available() -> bool:
    return get_reference_runtime_root().exists()


def is_preferred() -> bool:
    return False


def recognize_chords(
    audio_path: str,
    model_path: Path,
    checkpoint_path: Path,
) -> list:
    ensure_numpy_compat()
    btc_root = get_reference_runtime_root()
    if not btc_root.exists():
        raise FileNotFoundError(f"BTC-ISMIR19 source not found: {btc_root}")

    config_path = model_path / "config" / "btc_config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"BTC config not found: {config_path}")

    sys.path.insert(0, str(btc_root))
    try:
        BTC_model = importlib.import_module("btc_model").BTC_model

        config = load_btc_config(config_path)
        device = get_inference_device()
        model = BTC_model(config=config["model"]).to(device)

        checkpoint, mean, std = load_checkpoint(checkpoint_path, device)
        model.load_state_dict(checkpoint["model"])
        model.eval()

        feature, feature_per_second, _ = audio_file_to_features(
            audio_path,
            config,
        )
        feature = feature.T
        feature = (feature - mean) / std

        n_timestep = int(config["model"]["timestep"])
        if feature.shape[0] == 0:
            return []

        num_pad = (n_timestep - (feature.shape[0] % n_timestep)) % n_timestep
        if num_pad > 0:
            feature = _pad_features(feature, num_pad)

        num_instance = feature.shape[0] // n_timestep
        label_map = idx2voca_chord()
        time_unit = float(feature_per_second)

        return _run_inference(
            model,
            feature,
            n_timestep,
            num_instance,
            num_pad,
            time_unit,
            label_map,
            device,
        )
    finally:
        try:
            sys.path.remove(str(btc_root))
        except ValueError:
            pass


def _pad_features(feature, num_pad: int):
    import numpy as np

    return np.pad(
        feature,
        ((0, num_pad), (0, 0)),
        mode="constant",
        constant_values=0,
    )


def _run_inference(
    model,
    feature,
    n_timestep: int,
    num_instance: int,
    num_pad: int,
    time_unit: float,
    label_map: dict[int, str],
    device: torch.device,
) -> list:
    lines = []
    start_time = 0.0

    with torch.no_grad():
        feature_tensor = torch.tensor(
            feature,
            dtype=torch.float32,
        ).unsqueeze(0).to(device)
        prev_chord = None
        for index in range(num_instance):
            self_attn_output, _ = model.self_attn_layers(
                feature_tensor[
                    :,
                    n_timestep * index:n_timestep * (index + 1),
                    :,
                ]
            )
            output = model.output_layer(self_attn_output)

            # Compute per-timestep predictions and confidences when logits are available
            try:
                logits = output[0] if isinstance(output, tuple) else output
                probs_tensor = None
                if torch.is_floating_point(logits):
                    probs_tensor = torch.softmax(logits, dim=-1)
                    pred_tensor = torch.argmax(probs_tensor, dim=-1)
                else:
                    pred_tensor = logits
                prediction = pred_tensor.squeeze()
            except Exception:
                if isinstance(output, tuple):
                    prediction = output[0].squeeze()
                else:
                    prediction = torch.argmax(output, dim=-1).squeeze()

            for timestep in range(n_timestep):
                try:
                    chord_idx = int(prediction[timestep].item())
                except Exception:
                    chord_idx = int(prediction[timestep])

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
                    lines.append(
                        (start_time, change_time, label_map[prev_chord], float(prev_conf))
                    )
                    start_time = change_time
                    prev_chord = chord_idx
                    prev_conf = conf

                if (
                    index == num_instance - 1
                    and timestep + num_pad == n_timestep
                ):
                    end_time = time_unit * (n_timestep * index + timestep)
                    if start_time != end_time:
                        lines.append(
                            (start_time, end_time, label_map[prev_chord], float(prev_conf))
                        )
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
