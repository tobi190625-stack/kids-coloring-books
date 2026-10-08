#!/usr/bin/env python3
"""Run with the Chatterbox environment (C:/Users/tobi1/cbvenv, or set CB_PYTHON): makes many voice lines with one
model load. Input: a JSON file {"out.wav": {"text": ..., "exaggeration": .., "cfg": .., "seed": ..}, ...}.
Works on CPU (slow, about 10-40 s per line) or on an NVIDIA GPU (fast) automatically."""
import json
import sys

import torch
import torchaudio
from chatterbox.tts import ChatterboxTTS

jobs = json.load(open(sys.argv[1], encoding="utf-8"))
device = "cuda" if torch.cuda.is_available() else "cpu"
model = ChatterboxTTS.from_pretrained(device=device)
for i, (path, j) in enumerate(jobs.items(), 1):
    torch.manual_seed(int(j.get("seed", 7)))
    wav = model.generate(j["text"], exaggeration=j.get("exaggeration", 0.6), cfg_weight=j.get("cfg", 0.35),
                         temperature=0.8)
    torchaudio.save(path, wav, model.sr)
    print(f"[{i}/{len(jobs)}] {j['text'][:50]}", flush=True)
