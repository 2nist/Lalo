#!/usr/bin/env python3
"""
LALO Section Detector — feature-logged multi-signal boundary scorer.

Architecture: Consumes ChordMini (BTC-SL) chord output as one signal.
Does NOT modify chord detection — chords flow in, sections flow out.

Five signals per candidate boundary:
  flux_peak        — spectral novelty (positive mel-flux delta)
  chord_novelty    — fraction of chords that changed in +/-4-beat window
  cadence_score    — chord sequence match to V7->I templates
  repetition_break — self-similarity drop (SSM checkerboard)
  duration_prior   — how likely are the resulting section lengths

Every candidate boundary stores its feature vector regardless of whether
it is kept, enabling weight tuning or a learned scorer later.

Output:
  <slug>.sections.json    — same format as section_prototype.py + sectionType
  <slug>.candidates.json  — full candidate log for analysis / weight tuning

Usage:
  python scripts/analysis/section_detector.py \\
    --audio data/audio/mysong.mp3 \\
    --chords data/output/mysong.chords.json \\
    --out-dir data/output --slug mysong
"""

from __future__ import annotations

import argparse
import json
import joblib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import librosa
import numpy as np
import warnings
from scipy.signal import find_peaks


# ---------------------------------------------------------------------------
# Signal weights (tune against Harmonix benchmark)
# ---------------------------------------------------------------------------
DEFAULT_WEIGHTS: Dict[str, float] = {
    # Tuned by grid_search_weights.py over 47 Beatles songs (3121 combos).
    # flux_peak + duration_prior dominate; musical signals contribute weakly.
    "flux_peak":         0.4118,
    "chord_novelty":     0.0588,
    "cadence_score":     0.0588,
    "repetition_break":  0.0588,
    "duration_prior":    0.4118,
    "msaf_vote":         0.15,
    "chord_ngram_rep":   0.0,
    # Additional candidate features (small defaults)
    "chroma_change": 0.05,
    "spec_contrast": 0.05,
    "onset_density": 0.05,
    "rms_energy": 0.05,
}
    # Default NMS strategy: 'score' (greedy by score) or 'time' (left-to-right time order)
NMS_STRATEGY = 'time'

MIN_SECTION_SEC = 4.0
MAX_SECTION_SEC = 90.0
NMS_DISTANCE_SEC = 8.0
SSM_BAR_BEATS = 2
SSM_WINDOW_BARS = 8
SCORER_MODEL_PATH = Path("data/training/scorer_gbt.pkl")
_SCORER_CACHE: Dict[str, Optional[Any]] = {}
SCORER_FEATURE_ORDER = (
    "flux_peak",
    "chord_novelty",
    "cadence_score",
    "repetition_break",
    "duration_prior",
    "chroma_change",
    "spec_contrast",
    "onset_density",
    "rms_energy",
    "msaf_vote",
    "chord_ngram_rep",
)

_SEMITONES = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
    "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11,
}


# ---------------------------------------------------------------------------
# Stage 1 — Audio loading + mel-flux novelty
# ---------------------------------------------------------------------------

def _load_and_flux(
    audio_path: Path,
    sr: int = 16000,
    hop: int = 512,
    n_mels: int = 128,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, int]:
    """Load audio and compute positive mel-flux novelty curve.

    Returns (y, flux, log_mel_S, sr).
    """
    y, sr = librosa.load(str(audio_path), sr=sr, mono=True)
    S = librosa.feature.melspectrogram(
        y=y, sr=sr, n_fft=2048, hop_length=hop,
        n_mels=n_mels, power=2.0,
    )
    log_S = librosa.power_to_db(S, ref=np.max)
    delta = np.diff(log_S, axis=1)
    flux = np.maximum(delta, 0.0).sum(axis=0)
    flux = np.concatenate([[0.0], flux])
    return y, flux, log_S, sr


def _compute_additional_frame_features(y: np.ndarray, sr: int, hop: int, n_fft: int = 2048):
    """Compute frame-level features used for richer candidate descriptors.

    Returns a dict with keys: chroma (12 x T), spec_contrast (n_bands x T), onset_env (T,), rms (T,)
    """
    # chroma
    try:
        chroma = librosa.feature.chroma_stft(
            y=y,
            sr=sr,
            hop_length=hop,
            n_fft=n_fft,
            tuning=0.0,
        )
    except Exception:
        chroma = None

    # spectral contrast
    try:
        spec_contrast = librosa.feature.spectral_contrast(y=y, sr=sr, hop_length=hop, n_fft=n_fft)
    except Exception:
        spec_contrast = None

    # onset envelope
    try:
        onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    except Exception:
        onset_env = None

    # rms
    try:
        rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    except Exception:
        rms = None

    return {
        "chroma": chroma,
        "spec_contrast": spec_contrast,
        "onset_env": onset_env,
        "rms": rms,
    }


def _smooth(x: np.ndarray, win: int = 7) -> np.ndarray:
    if win <= 1:
        return x
    pad = win // 2
    padded = np.pad(x, (pad, pad), mode="edge")
    cs = np.cumsum(padded, dtype=float)
    return (cs[win:] - cs[:-win]) / win


# ---------------------------------------------------------------------------
# Stage 2 — Beat tracking (madmom preferred, librosa fallback)
# ---------------------------------------------------------------------------

def _patch_compat() -> None:
    """Apply Python 3.10 / NumPy 1.24 compatibility patches for madmom."""
    import collections
    import collections.abc
    for _a in (
        "MutableSequence", "MutableMapping", "MutableSet",
        "Callable", "Iterable", "Iterator",
    ):
        if not hasattr(collections, _a):
            setattr(collections, _a, getattr(collections.abc, _a))
    for _a, _v in (
        ("float", float), ("int", int),
        ("complex", complex), ("bool", bool),
    ):
        if not hasattr(np, _a):
            setattr(np, _a, _v)


def _detect_beats(
    y: np.ndarray, sr: int
) -> Tuple[np.ndarray, np.ndarray]:
    """Return (beat_times, downbeat_times) in seconds."""
    try:
        _patch_compat()
        from madmom.features.beats import (
            RNNBeatProcessor,
            DBNBeatTrackingProcessor,
        )
        beats = DBNBeatTrackingProcessor(fps=100)(RNNBeatProcessor()(y))
        try:
            from madmom.features.downbeats import (
                RNNDownBeatProcessor,
                DBNDownBeatTrackingProcessor,
            )
            db_res = DBNDownBeatTrackingProcessor(
                beats_per_bar=[3, 4], fps=100
            )(RNNDownBeatProcessor()(y))
            downbeats = db_res[db_res[:, 1] == 1, 0]
        except Exception:
            downbeats = beats[::4] if len(beats) >= 4 else beats[:1]
        return beats, downbeats
    except Exception:
        pass

    except Exception:
        pass

    warnings.warn(
        "madmom beat tracker unavailable; using uniform fallback beats",
        category=UserWarning,
        stacklevel=2,
    )
    duration = len(y) / sr if sr else 0.0
    if duration <= 0.0:
        return np.array([]), np.array([])
    beat_interval = 0.5
    beats = np.arange(0.0, duration, beat_interval)
    if beats.size == 0:
        beats = np.array([0.0])
    downbeats = beats[::4] if beats.size >= 4 else beats[:1]
    return beats, downbeats


# ---------------------------------------------------------------------------
# Stage 3 — Chord novelty (reads ChordMini output, does not modify it)
# ---------------------------------------------------------------------------

def _chord_novelty_at_candidates(
    candidate_times: np.ndarray,
    chords: List[Dict],
    window_sec: float = 2.0,
) -> np.ndarray:
    """Fraction of chord changes in +/- window around each candidate."""
    if not chords:
        return np.zeros(len(candidate_times))
    novelty = np.zeros(len(candidate_times))
    for i, t in enumerate(candidate_times):
        lo, hi = t - window_sec, t + window_sec
        labels = [
            c["chord"]
            for c in chords
            if lo <= float(c.get("start", c.get("time", 0))) < hi
        ]
        if len(labels) < 2:
            continue
        changes = sum(1 for a, b in zip(labels, labels[1:]) if a != b)
        novelty[i] = min(1.0, changes / (len(labels) - 1))
    return novelty


# ---------------------------------------------------------------------------
# Stage 4 — Cadence score (V7 -> I detection)
# ---------------------------------------------------------------------------

def _chord_root(label: str) -> Optional[int]:
    if not label or label in ("N", "X"):
        return None
    root = label.split(":")[0].split("/")[0]
    return _SEMITONES.get(root)


def _cadence_score_at_candidates(
    candidate_times: np.ndarray,
    chords: List[Dict],
    lookback_sec: float = 4.0,
) -> np.ndarray:
    """Score V->I cadential motion before each boundary."""
    if not chords:
        return np.zeros(len(candidate_times))
    scores = np.zeros(len(candidate_times))
    for i, t in enumerate(candidate_times):
        window = [
            c for c in chords
            if t - lookback_sec
            <= float(c.get("start", c.get("time", 0))) < t
        ]
        if not window:
            continue
        distinct = [window[0]]
        for c in window[1:]:
            if c["chord"] != distinct[-1]["chord"]:
                distinct.append(c)
        if len(distinct) < 2:
            scores[i] = 0.1
            continue
        r1 = _chord_root(distinct[-2].get("chord", ""))
        r2 = _chord_root(distinct[-1].get("chord", ""))
        if r1 is None or r2 is None:
            scores[i] = 0.1
            continue
        interval = (r1 - r2) % 12
        if interval == 7:
            scores[i] = 1.0
        elif interval in (5, 2, 10):
            scores[i] = 0.6
        elif r1 != r2:
            scores[i] = 0.3
        else:
            scores[i] = 0.05
    return scores


# ---------------------------------------------------------------------------
# Stage 5 — SSM repetition structure (Foote checkerboard)
# ---------------------------------------------------------------------------

def _build_ssm(
    log_S: np.ndarray,
    beat_times: np.ndarray,
    sr: int,
    hop: int,
    beats_per_vector: int = 2,
) -> Tuple[np.ndarray, np.ndarray]:
    """Beat-synchronise log-mel then build cosine SSM."""
    n_frames = log_S.shape[1]
    beat_frames = np.clip(
        librosa.time_to_frames(beat_times, sr=sr, hop_length=hop),
        0, n_frames - 1,
    )
    groups, group_times = [], []
    for i in range(0, len(beat_frames) - beats_per_vector, beats_per_vector):
        lo = beat_frames[i]
        hi = beat_frames[
            min(i + beats_per_vector, len(beat_frames) - 1)
        ]
        if hi <= lo:
            continue
        groups.append(log_S[:, lo:hi].mean(axis=1))
        group_times.append(beat_times[i])

    if len(groups) < 4:
        n = max(len(groups), 1)
        return np.eye(n), np.array(group_times[:n])

    G = np.stack(groups)
    try:
        import librosa.segment as lseg

        R = lseg.recurrence_matrix(
            G.T,
            metric="cosine",
            mode="affinity",
            sparse=False,
            sym=True,
        )
        R = lseg.path_enhance(R, n=9)
    except Exception:
        G_norm = G / (np.linalg.norm(G, axis=1, keepdims=True) + 1e-8)
        R = G_norm @ G_norm.T
    return R, np.array(group_times)


def _msaf_boundary_votes(
    audio_path: Path,
    candidate_times: np.ndarray,
    tolerance_sec: float = 4.0,
    msaf_algo: str = "scluster",
) -> np.ndarray:
    """Return MSaf boundary proximity votes for candidate times."""
    votes = np.zeros(len(candidate_times))
    if len(candidate_times) == 0:
        return votes
    try:
        import msaf
        import warnings

        warnings.filterwarnings("ignore")
        results = msaf.process(
            str(audio_path),
            boundaries_id=msaf_algo,
            feature="pcp",
            labels_id=None,
            annot_beats=False,
        )
        msaf_times = np.array([float(t) for t in results[0]], dtype=float)
        if msaf_times.size == 0:
            return votes
        for i, ct in enumerate(candidate_times):
            if np.min(np.abs(msaf_times - ct)) <= tolerance_sec:
                votes[i] = 1.0
    except Exception:
        pass
    return votes


def _load_scorer_model(
    path: Path = SCORER_MODEL_PATH,
) -> Tuple[Optional[Any], str]:
    """Lazy-load the gradient-boosted scorer and cache the result."""
    key = str(path)
    if key in _SCORER_CACHE:
        model = _SCORER_CACHE[key]
        status = "loaded" if model is not None else "missing"
        return model, status
    if not path.exists():
        _SCORER_CACHE[key] = None
        return None, "missing"
    try:
        model = joblib.load(str(path))
    except Exception:
        _SCORER_CACHE[key] = None
        return None, "load_error"
    _SCORER_CACHE[key] = model
    return model, "loaded"


def _checkerboard_novelty(ssm: np.ndarray, kernel_size: int = 8) -> np.ndarray:
    """Foote-style checkerboard kernel applied along the SSM diagonal."""
    n = ssm.shape[0]
    novelty = np.zeros(n)
    k = kernel_size
    half = k // 2
    kernel = np.ones((k, k))
    kernel[:half, half:] = -1
    kernel[half:, :half] = -1
    for i in range(half, n - half):
        patch = ssm[i - half: i + half, i - half: i + half]
        if patch.shape == kernel.shape:
            novelty[i] = float(np.sum(patch * kernel))
    mn, mx = novelty.min(), novelty.max()
    if mx > mn:
        novelty = (novelty - mn) / (mx - mn)
    return novelty


def _repetition_break_at_candidates(
    candidate_times: np.ndarray,
    ssm: np.ndarray,
    ssm_times: np.ndarray,
) -> np.ndarray:
    if ssm.shape[0] < 4:
        return np.zeros(len(candidate_times))
    k = min(SSM_WINDOW_BARS, ssm.shape[0] // 4)
    curve = _checkerboard_novelty(ssm, kernel_size=k)
    scores = np.zeros(len(candidate_times))
    for i, t in enumerate(candidate_times):
        idx = int(np.argmin(np.abs(ssm_times - t)))
        scores[i] = float(curve[idx])
    return scores


def _chord_ngram_rep_at_candidates(
    candidate_times: np.ndarray,
    chords: List[Dict],
    n: int = 4,
) -> np.ndarray:
    """Lightweight chord n-gram repetition signal.

    For each candidate, find the n-chord sequence ending at or before the
    candidate time and count how many identical sequences appear elsewhere
    in the song. Normalize to 0-1 by dividing by max repeats (>=1).
    """
    if not chords or len(chords) < 2:
        return np.zeros(len(candidate_times))
    # Build list of chord labels with start times
    chord_times = [float(c.get("start", c.get("time", 0))) for c in chords]
    chord_labels = [c.get("chord") for c in chords]

    # Build n-gram map: tuple(labels) -> list of start indices
    ngrams = {}
    for i in range(0, len(chord_labels) - n + 1):
        key = tuple(chord_labels[i : i + n])
        ngrams.setdefault(key, []).append(i)

    reps = np.zeros(len(candidate_times))
    for i, t in enumerate(candidate_times):
        # find chord index at or just before t
        idx = max(0, max([j for j, ct in enumerate(chord_times) if ct <= t], default=0))
        start = max(0, idx - n + 1)
        key = tuple(chord_labels[start : start + n])
        locs = ngrams.get(key, [])
        count = len(locs) if locs else 0
        # If the same sequence occurs at least twice (repeat), count as signal
        reps[i] = float(max(0, count - 1))
    if reps.max() <= 0:
        return np.zeros_like(reps)
    return reps / float(reps.max())


# ---------------------------------------------------------------------------
# Stage 6 — Duration prior
# ---------------------------------------------------------------------------

def _duration_prior_score(
    candidate_times: np.ndarray,
    song_duration_sec: float,
    min_sec: float = MIN_SECTION_SEC,
    max_sec: float = MAX_SECTION_SEC,
    ideal_sec: float = 24.0,
) -> np.ndarray:
    boundaries = np.concatenate([[0.0], candidate_times, [song_duration_sec]])
    durations = np.diff(boundaries)
    scores = np.zeros(len(candidate_times))

    def _prior(d: float) -> float:
        if d < min_sec or d > max_sec:
            return 0.05
        if d <= ideal_sec:
            return 0.3 + 0.7 * (d - min_sec) / max(1, ideal_sec - min_sec)
        return 0.3 + 0.7 * (max_sec - d) / max(1, max_sec - ideal_sec)

    for i in range(len(candidate_times)):
        scores[i] = (_prior(durations[i]) + _prior(durations[i + 1])) / 2.0
    return scores


# ---------------------------------------------------------------------------
# Stage 7 — Candidate generation
# ---------------------------------------------------------------------------

def _generate_candidates(
    flux: np.ndarray,
    sr: int,
    hop: int,
    min_sec: float = NMS_DISTANCE_SEC,
    prominence: float = 0.18,
    sub_prominence: float = 0.3,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (frames, times, normalised_flux_scores) for all candidates.

    Two-scale peak picking:
      Primary   — height >= prominence*σ,     distance >= min_sec  (strong flux)
      Secondary — height >= sub_prominence*σ, distance >= min_sec/2 (medium flux;
                  gives chord/repetition signals a chance to elevate non-flux
                  boundaries without drowning in noise)
    """
    flux_s = _smooth(flux, win=7)
    mean_f, std_f = float(flux_s.mean()), float(flux_s.std()) + 1e-8
    thr = mean_f + prominence * std_f
    dist = int(min_sec * sr / hop)
    peaks, _ = find_peaks(flux_s, height=thr, distance=dist)
    sub_thr = mean_f + sub_prominence * std_f
    sub_peaks, _ = find_peaks(flux_s, height=sub_thr, distance=dist // 2)
    all_frames = np.unique(np.concatenate([peaks, sub_peaks]))
    times = librosa.frames_to_time(all_frames, sr=sr, hop_length=hop)
    vals = flux_s[all_frames]
    mn, mx = vals.min() if vals.size else 0.0, vals.max() if vals.size else 1.0
    norm = (vals - mn) / (mx - mn + 1e-8)
    return all_frames, times, norm


# ---------------------------------------------------------------------------
# Stage 8 — NMS + beat-snapping
# ---------------------------------------------------------------------------

def _nms_by_score(
    candidate_times: np.ndarray,
    scores: np.ndarray,
    min_gap_sec: float = NMS_DISTANCE_SEC,
) -> np.ndarray:
    """Greedy NMS: keep highest-scoring with minimum gap between kept."""
    if len(candidate_times) == 0:
        return np.array([], dtype=bool)
    # Deterministic ordering: primary = descending score, tie-break = ascending index
    order = np.lexsort((np.arange(len(scores)), -scores))
    kept = np.zeros(len(candidate_times), dtype=bool)
    kept_times: List[float] = []
    for idx in order:
        t = float(candidate_times[idx])
        if all(abs(t - k) >= min_gap_sec for k in kept_times):
            kept[idx] = True
            kept_times.append(t)
    return kept


def _nms_time_first(candidate_times: np.ndarray, min_gap_sec: float = NMS_DISTANCE_SEC) -> np.ndarray:
    """Left-to-right time-ordered NMS: keep first candidate then skip within gap."""
    if len(candidate_times) == 0:
        return np.array([], dtype=bool)
    order = np.argsort(candidate_times)
    kept = np.zeros(len(candidate_times), dtype=bool)
    kept_times: List[float] = []
    for idx in order:
        t = float(candidate_times[idx])
        if all(abs(t - k) >= min_gap_sec for k in kept_times):
            kept[idx] = True
            kept_times.append(t)
    return kept


def _apply_nms(candidate_times: np.ndarray, scores: np.ndarray, min_gap_sec: float = NMS_DISTANCE_SEC, strategy: str = NMS_STRATEGY) -> np.ndarray:
    """Dispatch NMS according to strategy. Keeps API consistent with previous _nms_by_score."""
    if strategy == 'time':
        return _nms_time_first(candidate_times, min_gap_sec=min_gap_sec)
    # default/backwards-compatible
    return _nms_by_score(candidate_times, scores, min_gap_sec=min_gap_sec)


def _snap_to_beats(
    times: List[float],
    downbeats: np.ndarray,
    beats: np.ndarray,
    tolerance_sec: float = 2.0,
) -> List[float]:
    """Snap each boundary to nearest downbeat (preferred) or beat."""
    if not len(downbeats) and not len(beats):
        return times
    snapped = []
    for t in times:
        best_t, best_d = t, tolerance_sec + 1.0
        if len(downbeats):
            dists = np.abs(downbeats - t)
            idx = int(np.argmin(dists))
            if dists[idx] <= tolerance_sec:
                best_t, best_d = float(downbeats[idx]), float(dists[idx])
        if best_d > tolerance_sec and len(beats):
            dists = np.abs(beats - t)
            idx = int(np.argmin(dists))
            if dists[idx] < best_d:
                best_t = float(beats[idx])
        snapped.append(best_t)
    return snapped


def _reason_string(
    features: Dict[str, float], weights: Dict[str, float]
) -> str:
    contribs = {k: features[k] * weights.get(k, 0) for k in features}
    top = sorted(contribs, key=contribs.get, reverse=True)[:2]
    return "+".join(top)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def detect_sections(
    audio_path: Path,
    chords: Optional[List[Dict]] = None,
    weights: Optional[Dict[str, float]] = None,
    min_section_sec: float = MIN_SECTION_SEC,
    max_section_sec: float = MAX_SECTION_SEC,
    nms_gap_sec: float = NMS_DISTANCE_SEC,
    beat_snap_sec: float = 0.0,
    algorithm: str = "msaf_scluster",
    prob_threshold: float = 0.0,
    downbeat_confidence_thresh: float = 0.0,
    random_seed: Optional[int] = None,
    trace_path: Optional[Path] = None,
    cand_prominence: Optional[float] = None,
    cand_sub_prominence: Optional[float] = None,
    lyrics: Optional[List[Dict]] = None,
) -> Dict:
    """Run the section detector.

    algorithm:
      "auto"         — try msaf_scluster first; fall back to heuristic if unavailable
      "heuristic"    — weighted multi-signal approach (always available)
      "msaf"         — msaf with default algorithm (scluster)
      "msaf_sf"      — MSAF Structural Features (fast, good all-round)
      "msaf_scluster"— MSAF Laplacian segmentation (slower, often best)
      "msaf_olda"    — MSAF OLDA
    """
    requested_algorithm = algorithm
    use_scorer = False
    scorer_status = "disabled"
    scorer_model: Optional[Any] = None
    if requested_algorithm == "scored":
        scorer_model, scorer_status = _load_scorer_model()
        use_scorer = scorer_model is not None
        if not use_scorer:
            algorithm = "heuristic"

    # Deterministic seed (helps reproduce candidate ordering / tie-breaks)
    if random_seed is not None:
        try:
            np.random.seed(int(random_seed))
        except Exception:
            pass

    # ── MSAF dispatch ─────────────────────────────────────────────────────
    if algorithm == "auto":
        result = _detect_sections_msaf(audio_path, msaf_algorithm="scluster")
        if result is not None:
            result.setdefault("meta", {})[
                "requested_algorithm"
            ] = requested_algorithm
            return result
        # fall through to heuristic
    elif algorithm.startswith("msaf"):
        msaf_algo = (
            algorithm.split("_", 1)[1]
            if "_" in algorithm else "scluster"
        )
        result = _detect_sections_msaf(audio_path, msaf_algorithm=msaf_algo)
        if result is not None:
            result.setdefault("meta", {})[
                "requested_algorithm"
            ] = requested_algorithm
            return result
        # fall through to heuristic on failure
    weights = {**DEFAULT_WEIGHTS, **(weights or {})}
    sr, hop = 16000, 512

    y, flux, log_S, sr = _load_and_flux(audio_path, sr=sr, hop=hop)
    song_dur = librosa.frames_to_time(len(flux) - 1, sr=sr, hop_length=hop)

    beat_times, downbeat_times = _detect_beats(y, sr)

    # Build SSM early so we can propose SSM-based peaks as candidates
    ssm, ssm_times = _build_ssm(
        log_S, beat_times, sr, hop, beats_per_vector=SSM_BAR_BEATS
    )

    # Initial flux-based candidates (primary + secondary peaks)
    frames_flux, times_flux, flux_scores_flux = _generate_candidates(
        flux, sr, hop, min_sec=max(2.0, nms_gap_sec / 2),
        prominence=(cand_prominence if cand_prominence is not None else 0.18),
        sub_prominence=(cand_sub_prominence if cand_sub_prominence is not None else 0.3),
    )

    # SSM checkerboard novelty peaks -> candidate times
    ssm_novelty = _checkerboard_novelty(ssm) if ssm is not None else np.array([])
    ssm_peak_times = np.array([])
    try:
        if ssm_novelty.size:
            sp, _ = find_peaks(ssm_novelty, height=0.2, distance=1)
            if sp.size:
                ssm_peak_times = ssm_times[sp]
    except Exception:
        ssm_peak_times = np.array([])

    # Chord-change times: any chord start where label differs from previous
    chord_change_times = np.array([])
    try:
        if chords:
            times_list = []
            prev_label = None
            for c in chords:
                t = float(c.get("start", c.get("time", 0)))
                lab = c.get("chord")
                if prev_label is None or lab != prev_label:
                    times_list.append(t)
                prev_label = lab
            if times_list:
                chord_change_times = np.array(times_list, dtype=float)
    except Exception:
        chord_change_times = np.array([])

    # Union candidate times: flux peaks ∪ SSM peaks ∪ chord-change times
    all_times = np.unique(
        np.concatenate([times_flux, ssm_peak_times, chord_change_times])
    )
    # Convert to frames for sampling
    frames = librosa.time_to_frames(all_times, sr=sr, hop_length=hop)

    # Sample smoothed flux for these union candidates and normalise
    flux_s = _smooth(flux, win=7)
    vals = flux_s[frames.clip(0, len(flux_s) - 1)] if frames.size else np.array([])
    if vals.size:
        mn, mx = float(vals.min()), float(vals.max())
        flux_scores = (vals - mn) / (mx - mn + 1e-8)
    else:
        flux_scores = np.zeros(len(all_times))

    # Replace times variable used downstream with unioned times
    times = all_times

    if len(times) == 0:
        return {
            "sections": [{
                "label": "Section 1",
                "start_ms": 0,
                "duration_ms": int(song_dur * 1000),
                "sectionType": "Detected",
            }],
            "candidates": [],
            "meta": {
                "algorithm": "heuristic",
                "requested_algorithm": requested_algorithm,
                "duration_s": round(song_dur, 2),
                "beat_count": len(beat_times),
                "candidate_count": 0,
                "kept_count": 0,
            },
        }

    chord_novelty = _chord_novelty_at_candidates(
        times, chords or [], window_sec=2.0
    )
    cadence = _cadence_score_at_candidates(
        times, chords or [], lookback_sec=4.0
    )
    rep_break = _repetition_break_at_candidates(times, ssm, ssm_times)
    chord_ngram_rep = _chord_ngram_rep_at_candidates(times, chords or [], n=4)
    msaf_vote = _msaf_boundary_votes(audio_path, times)
    dur_prior = _duration_prior_score(
        times, song_dur,
        min_sec=min_section_sec, max_sec=max_section_sec,
    )

    # Additional frame-level derived features
    frame_feats = _compute_additional_frame_features(y, sr, hop)
    chroma = frame_feats.get("chroma")
    spec_contrast = frame_feats.get("spec_contrast")
    onset_env = frame_feats.get("onset_env")
    rms = frame_feats.get("rms")

    # Compute per-candidate derived features
    n = len(times)
    chroma_change = np.zeros(n)
    spec_contrast_val = np.zeros(n)
    onset_density = np.zeros(n)
    rms_energy = np.zeros(n)

    # helper to map time -> frame index
    def _time_to_frame(t):
        return int(librosa.time_to_frames(t, sr=sr, hop_length=hop))

    for i, t in enumerate(times):
        fidx = _time_to_frame(t)
        # chroma change: L2 difference to 4 frames prior (approx 0.13s at hop=512 sr=16k)
        if chroma is not None and fidx >= 4 and fidx < chroma.shape[1]:
            cnow = chroma[:, fidx]
            cprev = chroma[:, max(0, fidx - 4)]
            chroma_change[i] = float(np.linalg.norm(cnow - cprev))
        else:
            chroma_change[i] = 0.0

        # spectral contrast: mean across bands at frame
        if spec_contrast is not None and fidx < spec_contrast.shape[1]:
            spec_contrast_val[i] = float(np.mean(spec_contrast[:, fidx]))
        else:
            spec_contrast_val[i] = 0.0

        # onset density: count onsets in +/- 2.0s window using onset_env peaks
        if onset_env is not None:
            # convert window to frames
            w = int(round(2.0 * sr / hop))
            lo = max(0, fidx - w)
            hi = min(len(onset_env) - 1, fidx + w)
            # simple density: sum onset_env in window normalized
            onset_density[i] = float(np.sum(onset_env[lo:hi + 1]) / (hi - lo + 1 + 1e-8))
        else:
            onset_density[i] = 0.0

        # rms energy at frame
        if rms is not None and fidx < len(rms):
            rms_energy[i] = float(rms[fidx])
        else:
            rms_energy[i] = 0.0

    # normalize some derived features to 0-1 range for stability
    def _norm(x):
        if x.size == 0:
            return x
        mn, mx = float(x.min()), float(x.max())
        if mx <= mn:
            return np.zeros_like(x)
        return (x - mn) / (mx - mn)

    chroma_change = _norm(chroma_change)
    spec_contrast_val = _norm(spec_contrast_val)
    onset_density = _norm(onset_density)
    rms_energy = _norm(rms_energy)

    feature_arrays = {
        "flux_peak": flux_scores,
        "chord_novelty": chord_novelty,
        "cadence_score": cadence,
        "repetition_break": rep_break,
        "chord_ngram_rep": chord_ngram_rep,
        "duration_prior": dur_prior,
        "chroma_change": chroma_change,
        "spec_contrast": spec_contrast_val,
        "onset_density": onset_density,
        "rms_energy": rms_energy,
        "msaf_vote": msaf_vote,
    }
    feature_matrix = np.column_stack(
        [feature_arrays[name] for name in SCORER_FEATURE_ORDER]
    )

    scored_probs: Optional[np.ndarray] = None
    if requested_algorithm == "scored" and use_scorer and scorer_model is not None:
        try:
            scored_probs = scorer_model.predict_proba(feature_matrix)[:, 1].astype(float)
        except Exception:
            scored_probs = None
            use_scorer = False
            scorer_status = "predict_error"
    if requested_algorithm == "scored" and use_scorer and scored_probs is not None:
        scores = scored_probs
    else:
        scores = (
            weights["flux_peak"] * flux_scores
            + weights["chord_novelty"] * chord_novelty
            + weights["cadence_score"] * cadence
            + weights["repetition_break"] * rep_break
            + weights.get("chord_ngram_rep", 0.0) * chord_ngram_rep
            + weights["duration_prior"] * dur_prior
            + weights.get("msaf_vote", 0.0) * msaf_vote
            + weights.get("chroma_change", 0.0) * chroma_change
            + weights.get("spec_contrast", 0.0) * spec_contrast_val
            + weights.get("onset_density", 0.0) * onset_density
            + weights.get("rms_energy", 0.0) * rms_energy
        )

    # Apply an optional probability/score threshold before NMS.
    # Pre-filter to only candidates at or above threshold so that sub-threshold
    # candidates cannot "win" NMS slots just because every sub-threshold score
    # is equal (-1e6 trick would still keep them greedily).
    if prob_threshold and prob_threshold > 0.0:
        thresh_mask = scores >= prob_threshold
        if thresh_mask.any():
            kept_sub = _apply_nms(times[thresh_mask], scores[thresh_mask], min_gap_sec=nms_gap_sec)
            kept_mask = np.zeros(len(scores), dtype=bool)
            sub_indices = np.where(thresh_mask)[0]
            kept_mask[sub_indices[kept_sub]] = True
        else:
            # nothing clears threshold — fall back to unfiltered NMS
            kept_mask = _apply_nms(times, scores, min_gap_sec=nms_gap_sec)
    else:
        kept_mask = _apply_nms(times, scores, min_gap_sec=nms_gap_sec)

    # Lyric gap post-hoc confidence adjustment: if lyrics provided, boost
    # candidates near lyric gaps and penalize those that fall inside lyric lines.
    # This operates as an additive adjustment to scores after initial NMS
    # selection so that beat-snapping / final dedupe can reflect lyric priors.
    if lyrics:
        try:
            # Build lyric intervals
            lyric_intervals = [
                (float(l.get("start", l.get("time", 0))), float(l.get("end", l.get("time", 0))))
                for l in lyrics if l.get("start") is not None and l.get("end") is not None
            ]
            lyric_intervals.sort()
            # gaps: (end_i, start_{i+1}) where gap>0
            gaps = []
            for a, b in zip(lyric_intervals, lyric_intervals[1:]):
                gap_start = a[1]
                gap_end = b[0]
                if gap_end - gap_start > 0.05:
                    gaps.append((gap_start, gap_end))

            # Adjust score for kept candidates only (post-NMS)
            for i, t in enumerate(times):
                if not kept_mask[i]:
                    continue
                adjusted = 0.0
                # penalize if inside lyric line
                inside = any(s <= t <= e for s, e in lyric_intervals)
                if inside:
                    adjusted -= 0.1
                else:
                    # boost if within ±2s of a gap center
                    for gs, ge in gaps:
                        center = (gs + ge) / 2.0
                        if abs(t - center) <= 2.0:
                            adjusted += 0.15
                            break
                scores[i] = max(0.0, scores[i] + adjusted)
            # Re-run NMS on adjusted scores to reflect lyric priors
            kept_mask = _apply_nms(times, scores, min_gap_sec=nms_gap_sec)
        except Exception:
            pass

    kept_sorted = sorted(float(t) for t in times[kept_mask])
    final: List[float] = []
    for t in kept_sorted:
        prev = final[-1] if final else 0.0
        if t - prev >= min_section_sec:
            final.append(t)

    if beat_snap_sec > 0 and (len(downbeat_times) or len(beat_times)):
        # Conditional beat-snapping: only snap to a downbeat when the
        # downbeat's local onset-strength confidence exceeds
        # `downbeat_confidence_thresh`. If `downbeat_confidence_thresh` is
        # 0.0 or `onset_env` is unavailable, fall back to the original
        # snapping behaviour (prefer downbeats, then beats).
        db_conf_map = None
        if downbeat_confidence_thresh > 0.0 and onset_env is not None:
            try:
                db_frames = librosa.time_to_frames(downbeat_times, sr=sr, hop_length=hop)
                max_onset = float(onset_env.max()) if onset_env is not None and onset_env.size else 0.0
                db_conf_map = {}
                for db_t, f in zip(downbeat_times, db_frames):
                    lo = max(0, int(f) - 2)
                    hi = min(len(onset_env) - 1, int(f) + 2)
                    val = float(np.mean(onset_env[lo:hi + 1])) if max_onset > 0 else 0.0
                    norm = val / max_onset if max_onset > 0 else 0.0
                    db_conf_map[round(float(db_t), 6)] = norm
            except Exception:
                db_conf_map = None

        snapped = []
        for t in final:
            best_t, best_d = t, beat_snap_sec + 1.0
            chosen = None
            # Try downbeats first (preferred) but only if confidence is high enough
            if len(downbeat_times):
                dists = np.abs(downbeat_times - t)
                idx = int(np.argmin(dists))
                if dists[idx] <= beat_snap_sec:
                    db_t = float(downbeat_times[idx])
                    db_ok = True
                    if db_conf_map is not None:
                        conf = db_conf_map.get(round(db_t, 6), 0.0)
                        db_ok = conf >= float(downbeat_confidence_thresh)
                    if db_ok:
                        best_t, best_d = db_t, float(dists[idx])
                        chosen = best_t
            # If we didn't accept a downbeat, consider regular beats
            if chosen is None and len(beat_times):
                dists = np.abs(beat_times - t)
                idx = int(np.argmin(dists))
                if dists[idx] <= beat_snap_sec and dists[idx] < best_d:
                    best_t = float(beat_times[idx])
                    chosen = best_t
            # If neither matched, keep original t
            snapped.append(chosen if chosen is not None else float(t))

        # Deduplicate and enforce min_section_sec
        deduped: List[float] = []
        for t in sorted(snapped):
            prev = deduped[-1] if deduped else 0.0
            if t - prev >= min_section_sec:
                deduped.append(t)
        final = deduped

    final_set = {round(t, 4) for t in final}

    candidates = []
    for i, (t, frame) in enumerate(zip(times, frames)):
        feats = {
            "flux_peak": round(float(flux_scores[i]), 4),
            "chord_novelty": round(float(chord_novelty[i]), 4),
            "cadence_score": round(float(cadence[i]), 4),
            "repetition_break": round(float(rep_break[i]), 4),
        "duration_prior": round(float(dur_prior[i]), 4),
        "chroma_change": round(float(chroma_change[i]), 4),
        "spec_contrast": round(float(spec_contrast_val[i]), 4),
        "onset_density": round(float(onset_density[i]), 4),
        "rms_energy": round(float(rms_energy[i]), 4),
        "msaf_vote": round(float(msaf_vote[i]), 4),
        }
        is_kept = round(float(t), 4) in final_set
        candidates.append({
            "time_s": round(float(t), 3),
            "beat_idx": (
                int(np.argmin(np.abs(beat_times - t)))
                if len(beat_times) else 0
            ),
            "features": feats,
            "score": round(float(scores[i]), 4),
            "kept": is_kept,
            "reason": _reason_string(feats, weights) if is_kept else "",
        })

    # Optional trace dump for debugging / parity analysis
    if trace_path is not None:
        try:
            tp = Path(trace_path)
            tp.parent.mkdir(parents=True, exist_ok=True)
            with tp.open("w", encoding="utf-8") as fh:
                json.dump({
                    "meta": {"seed": int(random_seed) if random_seed is not None else None},
                    "candidates": candidates,
                }, fh, indent=2)
        except Exception:
            pass

    boundary_times = [0.0] + sorted(final) + [song_dur]
    sections = []
    for idx in range(len(boundary_times) - 1):
        start_s = boundary_times[idx]
        dur_s = boundary_times[idx + 1] - start_s
        if dur_s < 1.0:
            continue
        sections.append({
            "label": f"Section {idx + 1}",
            "start_ms": int(round(start_s * 1000)),
            "duration_ms": int(round(dur_s * 1000)),
            "sectionType": "Detected",
        })

    meta_algorithm = "scored" if requested_algorithm == "scored" else "heuristic"
    scorer_meta_status = scorer_status if requested_algorithm == "scored" else "disabled"

    return {
        "sections": sections,
        "candidates": candidates,
        "meta": {
            "algorithm": meta_algorithm,
            "requested_algorithm": requested_algorithm,
            "duration_s": round(song_dur, 2),
            "beat_count": len(beat_times),
            "downbeat_count": len(downbeat_times),
            "candidate_count": len(candidates),
            "kept_count": len(final),
            "beat_snap_sec": beat_snap_sec,
            "scorer_model_path": (
                str(SCORER_MODEL_PATH) if requested_algorithm == "scored" else None
            ),
            "scorer_status": scorer_meta_status,
            "weights_used": weights,
        },
    }


# ---------------------------------------------------------------------------
# MSAF backend
# ---------------------------------------------------------------------------

def _detect_sections_msaf(
    audio_path: Path,
    msaf_algorithm: str = "scluster",
    feature: str = "pcp",
) -> Optional[Dict]:
    """Run an MSAF boundary algorithm and return in LALO section format.

    Returns None on any failure so callers can fall back to heuristic.

    Supported msaf_algorithm values: 'sf', 'scluster', 'olda', 'cnmf', 'vmo'
    Supported features: 'pcp', 'mfcc', 'cqt', 'tonnetz', 'tempogram'
    """
    try:
        import warnings
        import msaf  # type: ignore
        warnings.filterwarnings("ignore")

        results = msaf.process(
            str(audio_path),
            boundaries_id=msaf_algorithm,
            feature=feature,
            labels_id=None,
            annot_beats=False,
        )
        est_times = results[0]  # numpy array of boundary times in seconds

        # Get duration cheaply — msaf includes song end as last boundary,
        # fall back to librosa header read (no full decode needed)
        song_dur = float(est_times[-1]) if len(est_times) > 0 and float(est_times[-1]) > 1.0 \
                   else librosa.get_duration(path=str(audio_path))

        # Convert to LALO sections (filter out 0 and song-end boundaries)
        interior = [float(t) for t in est_times if 0.3 < float(t) < song_dur - 0.3]
        boundary_times = [0.0] + sorted(interior) + [song_dur]

        sections = []
        for idx in range(len(boundary_times) - 1):
            start_s = boundary_times[idx]
            dur_s   = boundary_times[idx + 1] - start_s
            if dur_s < 1.0:
                continue
            sections.append({
                "label":       f"Section {idx + 1}",
                "start_ms":    int(round(start_s * 1000)),
                "duration_ms": int(round(dur_s   * 1000)),
                "sectionType": "Detected",
            })

        return {
            "sections":   sections,
            "candidates": [],
            "meta": {
                "duration_s":      round(song_dur, 2),
                "beat_count":      0,
                "candidate_count": len(interior),
                "kept_count":      len(interior),
                "algorithm":       f"msaf_{msaf_algorithm}",
            },
        }
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("msaf failed (%s): %s", msaf_algorithm, exc)
        return None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        description="LALO multi-signal section detector"
    )
    ap.add_argument("--audio", required=True, help="Path to audio file")
    ap.add_argument(
        "--chords", default=None,
        help="ChordMini output JSON ({chords:[...]})",
    )
    ap.add_argument(
        "--out-dir", default="data/output", help="Output directory"
    )
    ap.add_argument(
        "--slug", default=None,
        help="Output filename stem (default: audio stem)",
    )
    ap.add_argument(
        "--min-section-sec", type=float, default=MIN_SECTION_SEC
    )
    ap.add_argument(
        "--max-section-sec", type=float, default=MAX_SECTION_SEC
    )
    ap.add_argument(
        "--beat-snap-sec", type=float, default=0.0,
        help="Snap boundaries to nearest beat within this window (0=off)",
    )
    ap.add_argument(
        "--algorithm",
        default="msaf_scluster",
        help=(
            "Section detection backend: auto|heuristic|msaf|msaf_sf|"
            "msaf_scluster|msaf_olda"
        ),
    )
    ap.add_argument(
        "--log-candidates", action="store_true", default=True,
        help="Write candidates JSON alongside sections (default: on)",
    )
    ap.add_argument(
        "--weight-flux", type=float,
        default=DEFAULT_WEIGHTS["flux_peak"],
    )
    ap.add_argument(
        "--weight-chord", type=float,
        default=DEFAULT_WEIGHTS["chord_novelty"],
    )
    ap.add_argument(
        "--weight-cadence", type=float,
        default=DEFAULT_WEIGHTS["cadence_score"],
    )
    ap.add_argument(
        "--weight-repetition", type=float,
        default=DEFAULT_WEIGHTS["repetition_break"],
    )
    ap.add_argument(
        "--weight-duration", type=float,
        default=DEFAULT_WEIGHTS["duration_prior"],
    )
    ap.add_argument(
        "--weight-chroma", type=float,
        default=DEFAULT_WEIGHTS.get("chroma_change", 0.0),
        help="Weight for chroma_change feature",
    )
    ap.add_argument(
        "--weight-spec-contrast", type=float,
        default=DEFAULT_WEIGHTS.get("spec_contrast", 0.0),
        help="Weight for spec_contrast feature",
    )
    ap.add_argument(
        "--weight-onset-density", type=float,
        default=DEFAULT_WEIGHTS.get("onset_density", 0.0),
        help="Weight for onset_density feature",
    )
    ap.add_argument(
        "--weight-rms", type=float,
        default=DEFAULT_WEIGHTS.get("rms_energy", 0.0),
        help="Weight for rms_energy feature",
    )
    ap.add_argument(
        "--random-seed", type=int, default=None,
        help="Optional RNG seed to make candidate ordering deterministic",
    )
    ap.add_argument(
        "--trace-path", default=None,
        help="Optional path to write candidate trace JSON for debugging",
    )
    ap.add_argument(
        "--prob-threshold", type=float, default=0.0,
        help="Score threshold (0-1). Candidates below this are suppressed before NMS",
    )
    ap.add_argument(
        "--lyrics", default=None,
        help="Optional JSON file with lyrics [{start:..., end:..., text:...}, ...]",
    )
    args = ap.parse_args()

    audio_path = Path(args.audio)
    slug = args.slug or audio_path.stem
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    chords = None
    if args.chords:
        raw = json.loads(Path(args.chords).read_text(encoding="utf-8"))
        chords = raw.get("chords", raw) if isinstance(raw, dict) else raw

    lyrics = None
    if args.lyrics:
        try:
            lyrics = json.loads(Path(args.lyrics).read_text(encoding="utf-8"))
        except Exception:
            lyrics = None

    weights = {
        "flux_peak": args.weight_flux,
        "chord_novelty": args.weight_chord,
        "cadence_score": args.weight_cadence,
        "repetition_break": args.weight_repetition,
        "duration_prior": args.weight_duration,
        "chroma_change": args.weight_chroma,
        "spec_contrast": args.weight_spec_contrast,
        "onset_density": args.weight_onset_density,
        "rms_energy": args.weight_rms,
    }

    result = detect_sections(
        audio_path,
        chords=chords,
        lyrics=lyrics,
        weights=weights,
        min_section_sec=args.min_section_sec,
        max_section_sec=args.max_section_sec,
        beat_snap_sec=args.beat_snap_sec,
        algorithm=args.algorithm,
        prob_threshold=args.prob_threshold,
        random_seed=args.random_seed,
        trace_path=Path(args.trace_path) if args.trace_path else None,
    )

    sec_path = out_dir / f"{slug}.sections.json"
    sec_path.write_text(
        json.dumps({"sections": result["sections"]}, indent=2),
        encoding="utf-8",
    )
    print(f"Sections   -> {sec_path}  ({len(result['sections'])} sections)")

    if args.log_candidates:
        cand_path = out_dir / f"{slug}.candidates.json"
        cand_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        kept = result["meta"]["kept_count"]
        total = result["meta"]["candidate_count"]
        print(f"Candidates -> {cand_path}  ({kept}/{total} kept)")

    print(f"Meta: {result['meta']}")


if __name__ == "__main__":
    main()
