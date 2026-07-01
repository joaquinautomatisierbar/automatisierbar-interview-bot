# Juglans Offerten-Generator — Offline Windows build & delivery runbook

Turns the `offerten-generator/` app into a single **`JuglansOfferten-Setup.exe`** for
a fully **offline** Windows 10 machine (client Busslinger lives in a Funkloch).
Double-click install → desktop icon → the app opens in the browser, no internet.

> **Confirmed target:** Windows 10, **4 GB RAM**. Still get the exact CPU model +
> winver before the final build (see `references`/the specs-check note). 4 GB is
> tight for a local model — read the **4 GB reality** section.

> **What is validated vs. pending (be honest):**
> - ✅ Offline pipeline + grounding guardrail + deterministic engine — unit-tested,
>   36 tests green, incl. a real-pipeline end-to-end AppTest (`tools/test_*`).
> - ⏳ The **live local model** (llama.cpp) has NOT been run yet — the Mac build box
>   can't compile it (cmake 4.x vs llama.cpp). It must be installed from the
>   **prebuilt Windows CPU wheel** and smoke-tested **on a 4 GB Win10 box** before
>   USB delivery. The T1 code path itself is unit-tested with a fake backend.

---

## 0. Build machine

A **Windows 10 (x64)** machine — build on the same OS family you ship to.
- Python **3.11 or 3.12** (64-bit), added to PATH.
- [Inno Setup 6](https://jrsoftware.org/isdl.php) (`iscc` on PATH).
- ~10 GB free disk.

## 1. Get the code + a clean app copy

Copy `offerten-generator/` to the build machine. It is NOT in git (client PII) —
transfer the folder directly. Then **remove build-only files from the app copy**
so they aren't frozen in:

```
del tools\test_*.py
del tools\build_*_deck.py        REM marketing deck generators (pull in python-pptx)
rmdir /s /q tools\__pycache__
```

## 2. Python env + dependencies (incl. the offline LLM engine)

```bat
cd offerten-generator
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -U pip
.venv\Scripts\pip install -r requirements.txt pyinstaller

REM llama-cpp-python: install the PREBUILT CPU wheel (no compiler needed).
.venv\Scripts\pip install llama-cpp-python ^
  --prefer-binary ^
  --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```

Verify: `.venv\Scripts\python -c "import llama_cpp, streamlit, rapidfuzz; print('ok')"`.

## 3. Bundle the local model

Pick by the client's RAM (confirmed 4 GB → the 1.5B, or ship deterministic-only).
All are commercial-OK licences — **do not** use Qwen2.5-**3B** (non-commercial).

| RAM | Model | GGUF (Q4_K_M) | Notes |
|-----|-------|---------------|-------|
| **4 GB** | Qwen2.5-1.5B-Instruct | ~1.0 GB | Apache-2.0. Tight but usable; test it. |
| 4 GB (safest) | *(none)* | — | Ship `JUGLANS_AI_MODE=deterministic`, no model. |
| 8 GB | Qwen2.5-7B-Instruct | ~4.7 GB | Apache-2.0, best German/JSON. |

```bat
mkdir models
REM Download on a machine WITH internet, then copy the .gguf into models\.
REM Example (Qwen2.5-1.5B): from Hugging Face Qwen/Qwen2.5-1.5B-Instruct-GGUF,
REM   file qwen2.5-1.5b-instruct-q4_k_m.gguf  →  models\
```

`run.py` auto-detects `models\*.gguf` and points the engine at it. Ship the
model's `LICENSE` file on the USB too.

## 4. Freeze the app (PyInstaller onedir)

```bat
.venv\Scripts\pyinstaller juglans.spec --noconfirm
```

Produces `dist\JuglansOfferten\` (onedir — **never** onefile: faster start, fewer
AV false-positives). Quick check before packaging:

```bat
dist\JuglansOfferten\JuglansOfferten.exe
```

The browser should open at `http://127.0.0.1:8765` with the app. (Binds to
127.0.0.1 → **no Windows Firewall prompt**.)

## 5. VC++ runtime

Download **VC_redist.x64.exe** (Microsoft VC++ 2015-2022) into `redist\`. The
installer chain-installs it silently (harmless no-op if already present).

## 6. Build the installer

```bat
iscc installer\juglans.iss
```

→ `installer\Output\JuglansOfferten-Setup.exe`. This is the only file the client
needs.

## 7. USB delivery

Put on an **8 GB+ USB stick**:
- `JuglansOfferten-Setup.exe`
- `INSTALL-ANLEITUNG.pdf` (the printed one-pager — see `installer/INSTALL-GUIDE.md`)
- the model `LICENSE` file

Install footprint ≈ 1.5–2.5 GB with the 1.5B model. First launch loads the model
once (slower), then it stays warm for the session.

---

## 4 GB reality (read before shipping the model)

On 4 GB: Windows (~2 GB) + Python/Streamlit (~0.4 GB) + a 1.5B Q4 model (~1.3–1.8 GB
resident) is at the edge — expect paging and slow first suggestions. Mitigations
already built in:
- **The deterministic engine always renders the full menu** even if the model is
  slow/absent — correctness never depends on the model.
- Weights are mmap'd; `JUGLANS_MODEL_CTX` defaults to 4096 to keep the KV cache small.
- On timeout (`JUGLANS_AI_TIMEOUT`, default 90 s) the app falls back to the
  deterministic result.

**Decision after the smoke test (Step 8):**
- Fast enough → ship hybrid with the 1.5B.
- Too slow / OOM → set `JUGLANS_AI_MODE=deterministic` (edit `run.py`'s
  `setdefault`, rebuild) and ship without the model. Still a smart, grounded menu
  (fuzzy + historical co-occurrence), just no model-written reasoning/quantities.
- Client wants full AI quality → a ~CHF 200 16 GB mini-PC runs the 7B fast and
  removes the squeeze entirely.

## 8. Smoke test on a 4 GB Win10 box (non-negotiable before delivery)

- [ ] Setup.exe installs; desktop icon appears; double-click opens the app.
- [ ] SmartScreen path works: **More info → Run anyway** (unsigned — see below).
- [ ] Questionnaire → **🧠 Intelligente Vorschläge** returns a menu. Measure the
      wait. Confirm no crash / no out-of-memory.
- [ ] Pull the model file aside and re-run → deterministic fallback still returns
      a menu (mode `deterministic_no_model`).
- [ ] The 🔍 search box (st_keyup_local) renders — not a blank iframe (frozen-bundle
      component check).
- [ ] Build a quote, save a draft, close & reopen → draft persists (in
      `%LOCALAPPDATA%\JuglansOfferten`).
- [ ] Download the Excel and open it in Excel/LibreOffice — layout intact.
- [ ] Feedback form → "gespeichert" and a line lands in
      `%LOCALAPPDATA%\JuglansOfferten\feedback_outbox.jsonl`.

## Config / env reference

| Env var | Default | Purpose |
|---------|---------|---------|
| `JUGLANS_AI_MODE` | `hybrid` | `hybrid` = deterministic + model; `deterministic` = no model |
| `JUGLANS_MODEL_PATH` | bundled `models\*.gguf` | Explicit GGUF path |
| `JUGLANS_MODEL_CTX` | `4096` | llama.cpp context window |
| `JUGLANS_MODEL_THREADS` | CPU count | inference threads |
| `JUGLANS_AI_TIMEOUT` | `90` | seconds before falling back to deterministic |
| `DATA_DIR` | `%LOCALAPPDATA%\JuglansOfferten` | drafts, feedback outbox |
| `TMP_DIR` | bundled `appdata\` | historical corpus (read-only) |

## SmartScreen / antivirus (unsigned build)

Unsigned Setup.exe → SmartScreen "Windows protected your PC". The printed guide
tells the user: **More info → Run anyway**. To remove the prompt, buy an OV/EV
code-signing cert (a few hundred CHF/yr) and sign `JuglansOfferten.exe` +
`JuglansOfferten-Setup.exe` — worth it only if more clients follow.

## Shipping an update (v2) later

Rebuild → new Setup.exe on a new USB. Because user data lives in
`%LOCALAPPDATA%\JuglansOfferten` (outside `{app}`), reinstalling **preserves his
saved drafts**. Collect his `feedback_outbox.jsonl` from that folder on the visit.
