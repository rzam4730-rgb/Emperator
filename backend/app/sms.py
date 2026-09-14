"""Provider-neutral SMS service for Emperator."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
import os
import urllib.parse
import urllib.request


@dataclass
class SMSResult:
    success: bool
    message_id: str | None = None
    message: str = ""


class SMSProvider(ABC):
    code = "abstract"

    @abstractmethod
    def send(self, receptor: str, message: str, sender: str | None = None) -> SMSResult:
        raise NotImplementedError


class MockSMSProvider(SMSProvider):
    code = "mock"

    def send(self, receptor: str, message: str, sender: str | None = None) -> SMSResult:
        return SMSResult(True, "mock-" + receptor[-6:], "ارسال آزمایشی موفق بود")


class KavenegarProvider(SMSProvider):
    """Kavenegar REST API adapter.

    Credentials are read only from environment variables; never store the API key
    in source control or send it from the browser.
    """

    code = "kavenegar"

    def __init__(self):
        self.api_key = os.getenv("KAVENEGAR_API_KEY", "").strip()
        self.sender = os.getenv("KAVENEGAR_SENDER", "").strip()
        self.base_url = os.getenv(
            "KAVENEGAR_API_BASE", "https://api.kavenegar.com/v1"
        ).rstrip("/")

    @staticmethod
    def _normalize_entries(data: dict) -> list[dict]:
        entries = (data or {}).get("entries") or []
        if isinstance(entries, dict):
            return [entries]
        return entries if isinstance(entries, list) else []

    def send(self, receptor: str, message: str, sender: str | None = None) -> SMSResult:
        if not self.api_key:
            return SMSResult(False, None, "KAVENEGAR_API_KEY تنظیم نشده است")

        effective_sender = (sender or self.sender).strip()
        if not effective_sender:
            return SMSResult(False, None, "KAVENEGAR_SENDER تنظیم نشده است")

        payload = urllib.parse.urlencode(
            {
                "receptor": receptor,
                "sender": effective_sender,
                "message": message,
            }
        ).encode("utf-8")
        url = f"{self.base_url}/{self.api_key}/sms/send.json"

        try:
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded; charset=utf-8"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=20) as response:
                raw = response.read().decode("utf-8")
                data = json.loads(raw)

            result = (data or {}).get("return") or {}
            api_status = int(result.get("status", 0) or 0)
            entries = self._normalize_entries(data)
            first = entries[0] if entries else {}
            success = api_status in {200, 201}
            message_id = first.get("messageid")
            return SMSResult(
                success,
                str(message_id) if message_id is not None else None,
                str(result.get("message", "ارسال پیامک انجام شد" if success else "ارسال پیامک ناموفق بود")),
            )
        except urllib.error.HTTPError as exc:
            try:
                body = exc.read().decode("utf-8", errors="replace")
                data = json.loads(body)
                result = (data or {}).get("return") or {}
                msg = str(result.get("message") or f"خطای HTTP کاوه‌نگار: {exc.code}")
            except Exception:
                msg = f"خطای HTTP کاوه‌نگار: {exc.code}"
            return SMSResult(False, None, msg)
        except (urllib.error.URLError, TimeoutError) as exc:
            return SMSResult(False, None, f"عدم دسترسی به سرویس کاوه‌نگار: {exc}")
        except (ValueError, json.JSONDecodeError) as exc:
            return SMSResult(False, None, f"پاسخ نامعتبر از کاوه‌نگار: {exc}")
        except Exception as exc:
            return SMSResult(False, None, f"خطا در سرویس پیامک: {exc}")


# Always register the provider class; credentials are checked when it is used.
PROVIDERS = {
    MockSMSProvider.code: MockSMSProvider(),
    KavenegarProvider.code: KavenegarProvider(),
}


def get_sms_provider(code: str | None = None) -> SMSProvider:
    selected = (code or os.getenv("EMPERATOR_SMS_PROVIDER", "mock")).strip().lower()
    if selected not in PROVIDERS:
        raise ValueError(f"SMS provider unavailable: {selected}")
    return PROVIDERS[selected]
