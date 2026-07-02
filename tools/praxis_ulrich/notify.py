"""notify.py — toast + clipboard for Dr. Ulrich. Best-effort by contract.

The pipeline calls doc_success/doc_unrecognized/doc_filing_failed per document;
main calls flush_cycle() once per poll cycle and connection_problem() on
persistent mailbox failures. Nothing here may ever influence filing/flagging —
every method swallows its own errors (the pipeline additionally wraps calls).

Clipboard batching (multi-PDF fix): success summaries collect during the cycle
and flush_cycle() writes ONE clipboard payload. A single document pastes bare
(exactly what DigiSono needs); several documents get a header line each so she
can split them while pasting.

Windows plumbing, each with a fallback:
  toast      winotify (win10toast is dead on Win11) -> PowerShell raw toast
  clipboard  pyperclip -> clip.exe via stdin (UTF-16LE)

Identical error toasts are rate-limited (default 1/h) so a broken sender
domain cannot spam her screen every poll.
"""

from __future__ import annotations

import subprocess
import sys
import time

try:
    from . import config
except ImportError:  # direct-script / test runs
    import config  # type: ignore


class BaseNotifier:
    """Shared batching + rate limiting. Subclasses implement _toast/_clipboard."""

    def __init__(self, cfg: dict | None = None):
        self.cfg = cfg or {}
        self.texts = config.TEXTE
        self._cycle: list[tuple[str, str]] = []   # (header, zusammenfassung)
        self._last_error_toast: dict[str, float] = {}

    # -- pipeline interface -------------------------------------------------

    def doc_success(self, o) -> None:
        header = self.texts["clipboard_doc_header"].format(
            titel=o.dokumenttitel, vorname=o.vorname, nachname=o.nachname)
        if o.zusammenfassung:
            self._cycle.append((header, o.zusammenfassung))
        self._toast_safe(
            self.texts["toast_ok_title"],
            self.texts["toast_ok_body"].format(
                titel=o.dokumenttitel, vorname=o.vorname, nachname=o.nachname,
                geburtsdatum=o.geburtsdatum))

    def doc_unrecognized(self, o, absender: str) -> None:
        self._error_toast(
            self.texts["toast_unrecognized_title"],
            self.texts["toast_unrecognized_body"].format(
                dateiname=o.pdf_name, absender=absender or "unbekannt"))

    def doc_filing_failed(self, o, ziel: str) -> None:
        self._error_toast(
            self.texts["toast_filing_failed_title"],
            self.texts["toast_filing_failed_body"].format(
                dateiname=o.pdf_name, ziel=ziel or "?"))

    def connection_problem(self) -> None:
        self._error_toast(self.texts["toast_connection_title"],
                          self.texts["toast_connection_body"])

    # -- cycle flush ----------------------------------------------------------

    def flush_cycle(self) -> str | None:
        """Write the aggregated clipboard payload. Returns it (for tests/logs)."""
        if not self._cycle:
            return None
        if len(self._cycle) == 1:
            payload = self._cycle[0][1]           # bare 4-Zeiler: direkt einfügbar
        else:
            payload = "\n\n".join(f"{h}\n{z}" for h, z in self._cycle)
        self._cycle = []
        try:
            self._clipboard(payload)
        except Exception as e:
            print(f"[befund-notify] Clipboard fehlgeschlagen: {e!r}", flush=True)
        return payload

    # -- internals -------------------------------------------------------------

    def _toast_safe(self, title: str, body: str) -> None:
        try:
            self._toast(title, body)
        except Exception as e:
            print(f"[befund-notify] Toast fehlgeschlagen: {e!r}", flush=True)

    def _error_toast(self, title: str, body: str) -> None:
        cooldown = int(self.cfg.get("error_toast_cooldown_min", 60)) * 60
        key = title + body
        now = time.time()
        if now - self._last_error_toast.get(key, 0) < cooldown:
            return
        self._last_error_toast[key] = now
        self._toast_safe(title, body)

    def _toast(self, title: str, body: str) -> None:  # pragma: no cover - abstract
        raise NotImplementedError

    def _clipboard(self, text: str) -> None:  # pragma: no cover - abstract
        raise NotImplementedError


class LogNotifier(BaseNotifier):
    """Dev/macOS/harness: print instead of OS integration."""

    def __init__(self, cfg: dict | None = None):
        super().__init__(cfg)
        self.toasts: list[tuple[str, str]] = []
        self.clipboards: list[str] = []

    def _toast(self, title: str, body: str) -> None:
        self.toasts.append((title, body))
        print(f"[TOAST] {title} — {body}", flush=True)

    def _clipboard(self, text: str) -> None:
        self.clipboards.append(text)
        print(f"[CLIPBOARD]\n{text}", flush=True)


class WindowsNotifier(BaseNotifier):
    def _toast(self, title: str, body: str) -> None:
        try:
            from winotify import Notification
            Notification(app_id="Befund-Automat", title=title, msg=body).show()
            return
        except Exception:
            pass
        # PowerShell raw-toast fallback (no module dependency)
        ps = (
            "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, "
            "ContentType=WindowsRuntime] | Out-Null;"
            "$t=[Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent("
            "[Windows.UI.Notifications.ToastTemplateType]::ToastText02);"
            "$n=$t.GetElementsByTagName('text');"
            f"$n.Item(0).AppendChild($t.CreateTextNode('{_ps_escape(title)}'))|Out-Null;"
            f"$n.Item(1).AppendChild($t.CreateTextNode('{_ps_escape(body)}'))|Out-Null;"
            "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("
            "'Befund-Automat').Show([Windows.UI.Notifications.ToastNotification]::new($t))"
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       capture_output=True, timeout=15, check=False)

    def _clipboard(self, text: str) -> None:
        try:
            import pyperclip
            pyperclip.copy(text)
            return
        except Exception:
            pass
        # clip.exe erwartet UTF-16LE für Umlaute. Ein Retry — Clipboard kann
        # kurzzeitig von anderen Apps gesperrt sein.
        for attempt in (1, 2):
            try:
                subprocess.run(["clip.exe"], input=text.encode("utf-16-le"),
                               timeout=10, check=True)
                return
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(1)


def _ps_escape(s: str) -> str:
    return (s or "").replace("'", "''")


def make_notifier(cfg: dict) -> BaseNotifier:
    if sys.platform == "win32":
        return WindowsNotifier(cfg)
    return LogNotifier(cfg)
