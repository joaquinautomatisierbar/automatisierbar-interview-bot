#!/usr/bin/env python3
"""main.py — Befund-Automat poll loop + tray icon.

Runtime shape (decisions/log.md): windowed tray app in the interactive user
session (toast + clipboard need it), autostarted via Startup-folder shortcut.
The tray icon is the "it is running" signal; right-click Beenden is the
rollback story. A crash is fail-safe: mails stay unflagged = manual process.

Loop per poll cycle:
    connect -> UIDVALIDITY -> new UIDs (state.last_uid, + rescan window on the
    first cycle after start) -> per UID fetch + pipeline.process_message ->
    advance last_uid -> notifier.flush_cycle() -> weekly state backup.

Fetch errors do NOT advance last_uid (retried next cycle). Pipeline outcomes
are terminal (state.py). Persistent connection failures raise one daily
"Verbindung gestört" toast instead of dying silently.

CLI:
  python3 tools/praxis_ulrich/main.py --once --dry-run     # harness: no writes at all
  python3 tools/praxis_ulrich/main.py --once --max-per-run 3   # supervised live run
  python3 tools/praxis_ulrich/main.py --profile hin            # production loop
"""

from __future__ import annotations

import argparse
import logging
import logging.handlers
import os
import sys
import threading
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))   # tools/ auf den Pfad (Paket-Import)

from praxis_ulrich import config, filing, mailbox, notify, pipeline, secrets_store, state  # noqa: E402

log = logging.getLogger("befund")


class InMemoryState:
    """--dry-run darf den echten Zustand NICHT anfassen: sonst gälten Mails als
    verarbeitet und der echte Lauf würde sie überspringen."""

    def __init__(self):
        self.records = []
        self._done = set()
        self._seen = set()

    def already_processed(self, uv, uid, idx):
        return (uv, uid, idx) in self._done

    def seen_attachment(self, mid, sha):
        return (mid, sha) in self._seen

    def record_attachment(self, **kw):
        self.records.append(kw)
        self._done.add((kw["uidvalidity"], kw["uid"], kw["attachment_index"]))
        self._seen.add((kw["message_id"], kw["attachment_sha256"]))

    def get_last_uid(self, uv):
        return 0

    def set_last_uid(self, uv, uid):
        pass


def _setup_logging() -> None:
    logdir = config.data_dir() / "logs"
    logdir.mkdir(parents=True, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(
        logdir / "befund.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(handler)
    log.addHandler(logging.StreamHandler(sys.stdout))
    log.setLevel(logging.INFO)


def _acquire_single_instance_lock() -> bool:
    """Ein Automat pro Maschine (Doppel-Poller = Doppel-Ablage)."""
    lock = config.data_dir() / "befund.lock"
    try:
        if lock.exists():
            old_pid = int(lock.read_text().strip() or "0")
            if old_pid and _pid_alive(old_pid):
                return False
        lock.write_text(str(os.getpid()))
        return True
    except Exception:
        return True  # Lock-Probleme dürfen den Start nicht verhindern


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False
    except Exception:
        return True


def poll_cycle(cfg: dict, sink, notifier, state_api, *, rescan: bool,
               dry_run: bool, max_per_run: int = 0) -> dict:
    """One poll. Returns {'processed': n, 'error': str|None}."""
    settings = config.imap_settings(cfg)
    password = secrets_store.get_secret("imap_password")
    if not password:
        return {"processed": 0, "error": "kein IMAP-Passwort/Token konfiguriert"}

    try:
        with mailbox.MailboxClient(settings["host"], settings["port"],
                                   settings["user"], password,
                                   folder=settings["folder"]) as client:
            uv = client.uidvalidity
            last = state_api.get_last_uid(uv)
            rescan_days = int(cfg.get("rescan_window_days", 3)) if (rescan or last == 0) else 0
            uids = client.new_uids(last, rescan_days=rescan_days)
            if max_per_run:
                uids = uids[:max_per_run]

            processed = 0
            for uid in uids:
                try:
                    raw, internal = client.fetch_raw(uid)
                except mailbox.MailboxError as e:
                    log.warning("FETCH UID %s fehlgeschlagen (%s) — nächster Zyklus", uid, e)
                    break  # last_uid NICHT vorrücken -> retry
                flagger = (lambda _uid: True) if dry_run else client.flag_red
                res = pipeline.process_message(
                    raw, uid=uid, uidvalidity=uv, internal_date=internal,
                    cfg=cfg, sink=sink, flagger=flagger, notifier=notifier,
                    state_api=state_api)
                if not dry_run:
                    state_api.set_last_uid(uv, uid)
                processed += 1
                if res.pdf_count:
                    log.info("UID %s: %s PDF(s) -> %s%s", uid, res.pdf_count,
                             [o.status for o in res.outcomes],
                             " 🚩" if res.flagged else "")
            notifier.flush_cycle()
            return {"processed": processed, "error": None}
    except Exception as e:
        log.warning("Poll-Zyklus fehlgeschlagen: %r", e)
        return {"processed": 0, "error": str(e)}


def run_loop(cfg: dict, *, dry_run: bool, once: bool, max_per_run: int,
             stop_event: threading.Event) -> None:
    state.init_db()
    state_api = InMemoryState() if dry_run else state
    sink = filing.DryRunSink() if dry_run else filing.make_sink(cfg)
    notifier = notify.make_notifier(cfg)

    consecutive_failures = 0
    last_conn_toast = 0.0
    first_cycle = True

    while not stop_event.is_set():
        result = poll_cycle(cfg, sink, notifier, state_api,
                            rescan=first_cycle, dry_run=dry_run,
                            max_per_run=max_per_run)
        first_cycle = False
        if result["error"]:
            consecutive_failures += 1
            if (consecutive_failures >= int(cfg.get("consecutive_poll_failures_alert", 5))
                    and time.time() - last_conn_toast > 86400):
                notifier.connection_problem()
                last_conn_toast = time.time()
        else:
            consecutive_failures = 0
            if not dry_run:
                state.backup_if_due()
        if once:
            break
        stop_event.wait(int(cfg.get("poll_interval_sec", 180)))


def _run_tray(stop_event: threading.Event) -> None:  # pragma: no cover - UI
    """Tray icon (pystray). Fällt ohne pystray auf headless zurück."""
    try:
        import pystray
        from PIL import Image, ImageDraw
    except Exception:
        log.info("pystray/PIL nicht verfügbar — laufe headless (Ctrl+C zum Beenden)")
        try:
            while not stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            stop_event.set()
        return

    img = Image.new("RGB", (64, 64), (16, 90, 60))
    d = ImageDraw.Draw(img)
    d.rectangle([18, 14, 46, 50], fill=(240, 240, 240))
    d.text((24, 22), "B", fill=(16, 90, 60))

    def _quit(icon, item):
        stop_event.set()
        icon.stop()

    def _open_log(icon, item):
        logfile = config.data_dir() / "logs" / "befund.log"
        if sys.platform == "win32":
            os.startfile(logfile)  # type: ignore[attr-defined]
        else:
            print(f"Log: {logfile}")

    menu = pystray.Menu(
        pystray.MenuItem(config.TEXTE["tray_open_log"], _open_log),
        pystray.MenuItem(config.TEXTE["tray_quit"], _quit),
    )
    pystray.Icon("befund-automat", img, "Befund-Automat", menu).run()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Befund-Automat — Praxis Tina Ulrich")
    ap.add_argument("--once", action="store_true", help="ein Poll-Zyklus, dann Ende")
    ap.add_argument("--dry-run", action="store_true",
                    help="keine Ablage, kein Flag, kein State — nur zeigen was passieren würde")
    ap.add_argument("--max-per-run", type=int, default=0, help="max. Mails pro Zyklus")
    ap.add_argument("--profile", choices=["hin", "test"], default=None)
    args = ap.parse_args(argv)

    _setup_logging()
    cfg = config.load()
    if args.profile:
        cfg["profile"] = args.profile

    if not _acquire_single_instance_lock():
        log.error("Befund-Automat läuft bereits (befund.lock) — zweite Instanz beendet sich.")
        return 1

    log.info("Start: Profil=%s Sink=%s dry_run=%s once=%s",
             cfg["profile"], "dryrun" if args.dry_run else cfg["sink"],
             args.dry_run, args.once)

    stop_event = threading.Event()
    if args.once:
        run_loop(cfg, dry_run=args.dry_run, once=True,
                 max_per_run=args.max_per_run, stop_event=stop_event)
        return 0

    worker = threading.Thread(
        target=run_loop, daemon=True,
        kwargs=dict(cfg=cfg, dry_run=args.dry_run, once=False,
                    max_per_run=args.max_per_run, stop_event=stop_event))
    worker.start()
    _run_tray(stop_event)   # blockiert bis Beenden
    stop_event.set()
    worker.join(timeout=10)
    return 0


if __name__ == "__main__":
    sys.exit(main())
