## Inbox — Machine B compatibility questions

Context:
- I ran the dev heuristic benchmark and attempted to install runtime deps for the detector.
- Attempts to install `librosa`/`numba` failed due to `llvmlite` build issues on macOS/Python 3.14.
- I tried creating a Python 3.11 venv; `llvmlite` still failed to build from source.

Please answer the following so I can proceed with a full detector run:

1. Preferred interpreter: do you want me to use Python 3.11, 3.10, or a Conda environment? (reply: `3.11` / `3.10` / `conda`)
2. Conda availability: is Miniconda/Conda available on this machine and OK to use? (reply: `yes` / `no`)
3. Build toolchain: are Xcode command-line tools and Homebrew available so I can install system deps (e.g. LLVM) if needed? (reply: `yes` / `no`)
4. Permission to install: is it acceptable to install Python packages into a repo-local virtualenv (`.venv`) or create a separate venv? (reply: `yes` / `no`)
5. CI option: would you prefer I run the full detector on a CI runner (GitHub Actions) with prebuilt wheels instead? (reply: `yes` / `no`)

Reproduction commands I ran (for review):

```
git checkout machine-b/worker-wave1
python3 -m venv .venv
.venv/bin/python3 -m pip install librosa madmom msaf
# attempted python3.11 venv:
python3.11 -m venv .venv311
.venv311/bin/python3 -m pip install librosa soundfile numpy scipy
```

Please reply in this file with the short answers to 1–5. Once you reply, I'll proceed and push any changes.
