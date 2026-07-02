# Befund-Automat — Windows-Build-Runbook

Mirror of the proven Juglans offline-build flow (`deploy/juglans-offline-build.md`),
adapted for the Praxis-Ulrich tray app. Target: one `BefundAutomat-Setup.exe`.

## Prerequisites (Windows build machine, 10/11)

1. Python 3.12 (python.org, "Add to PATH")
2. Inno Setup 6 (jrsoftware.org)
3. Repo copy of `tools/praxis_ulrich/` (the package is self-contained; the rest
   of the repo is not needed on the build machine)

## Build

```powershell
cd tools\praxis_ulrich\packaging
python -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r requirements-win.txt pyinstaller
pyinstaller befund.spec --noconfirm       # -> dist\BefundAutomat\
iscc befund.iss                           # -> BefundAutomat-Setup.exe
```

## Build-Smoke-Test (MANDATORY before the install appointment)

The spec/iss were authored on macOS and are untested until this passes once:

1. Run `BefundAutomat-Setup.exe` on a clean Windows VM (SmartScreen: "Weitere
   Informationen" → "Trotzdem ausführen" — unsigned MVP, same call as Juglans).
2. Tray icon appears; `%LOCALAPPDATA%\BefundAutomat\logs\befund.log` is written.
3. `BefundAutomat.exe` refuses a second instance (single-instance lock).
4. Set test creds (env or Credential Locker) → point profile `test` at the
   Infomaniak test mailbox → seed via `seed_test_mailbox.py` from the dev Mac →
   verify: toast appears, clipboard filled, files land in a temp hotfolder,
   flags set on the test mailbox.
5. Reinstall Setup.exe over the running app (`CloseApplications=yes`) → state.db
   survives (data dir is outside `{app}`).

## Update delivery

New build → send Setup.exe (download link) → doctor selftest → done. State,
config and secrets survive reinstalls. No auto-update in MVP.

## Secrets on the practice machine

Never in files. `doctor.py`/install step writes them to the Windows Credential
Locker via keyring: `imap_password` (HIN Mail Token), `llm_api_key` (provider
key per Datenschutz-Entscheid).
