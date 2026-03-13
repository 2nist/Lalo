#!/usr/bin/env python3
"""
FastAPI shim exposing the broad-strokes sectioner.

Run locally:
  uvicorn scripts.api.app:app --reload --port 8001

POST /analyze
Body:
{
  "key": "G major",
  "bpm": 94.0,           # optional
  "chords": [ { "time": 0.0, "label": "C" }, ... ],
  "audio_path": "path"   # optional, used only if bpm missing and librosa available
}
"""
from __future__ import annotations
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from scripts.analysis.broad_sections import analyze, estimate_bpm


class ChordEvent(BaseModel):
    time: float
    label: str


class AnalyzeRequest(BaseModel):
    key: str = "C major"
    bpm: Optional[float] = None
    audio_path: Optional[str] = None
    chords: List[ChordEvent]


app = FastAPI(title="LALO Broad Sections API")


@app.post("/analyze")
def post_analyze(req: AnalyzeRequest):
    if not req.chords and not req.audio_path:
        raise HTTPException(status_code=400, detail="Provide chords or audio_path")
    bpm = req.bpm
    if bpm is None:
        if req.audio_path:
            audio = Path(req.audio_path)
            if not audio.exists():
                raise HTTPException(status_code=404, detail=f"Audio not found: {audio}")
            bpm = estimate_bpm(audio)
        else:
            bpm = 120.0
    chords = [c.dict() for c in req.chords]
    result = analyze(chords, req.key, bpm)
    return result
