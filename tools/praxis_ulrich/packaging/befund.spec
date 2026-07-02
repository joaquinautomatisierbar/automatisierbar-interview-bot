# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Befund-Automat (Windows onedir, windowed).

Mirrors the proven Juglans pattern (offerten-generator/juglans.spec): build on
a WINDOWS machine matching the target OS family, onedir (never onefile — slower
start and more AV false positives), then wrap with Inno Setup (befund.iss).

Build (Windows, venv active):
    pip install -r requirements-win.txt pyinstaller
    pyinstaller befund.spec --noconfirm

Output: dist/BefundAutomat/ -> input for installer/befund.iss.

UNTESTED-ON-WINDOWS marker: this spec is authored on macOS and must be smoke-
tested on the Windows build VM before the install appointment (see
deploy/befund-automat-build.md, step "Build-Smoke-Test").
"""
from PyInstaller.utils.hooks import collect_all, copy_metadata

datas, binaries, hiddenimports = [], [], []

# Runtime third-party deps: code + data + native libs + metadata.
for pkg in ("fitz", "pymupdf", "anthropic", "winotify", "pystray", "PIL",
            "pyperclip", "keyring"):
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

for dist in ("anthropic", "pymupdf"):
    try:
        datas += copy_metadata(dist)
    except Exception:
        pass

# Windows Credential Locker backend is loaded dynamically by keyring.
hiddenimports += ["keyring.backends.Windows", "win32ctypes.pywin32"]

# The package itself ships as source so config.py stays a readable edit point.
datas += [("..", "praxis_ulrich")]

a = Analysis(
    ["../main.py"],
    pathex=["..", "../.."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["tkinter", "pytest", "test_praxis_state", "make_corpus",
              "seed_test_mailbox", "eval_extraction"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="BefundAutomat",
    console=False,          # windowed: tray app, kein Konsolenfenster
    icon=None,              # TODO: praxis icon before install appointment
)
coll = COLLECT(
    exe, a.binaries, a.datas,
    name="BefundAutomat",
)
