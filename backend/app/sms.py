"""Provider-neutral SMS service for Emperator."""
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
    code = "kavenegar"

    def __init__(self):
        self.api_key = os.getenv("KAVENEGAR_API_KEY", "").strip()
        self.sender = os.getenv("KAVENEGAR_SENDER", "").strip()
        self.base_url = os.getenv("KAVENEGAR_API_BASE", "https://api.kavenegar.com/v1").rstrip("/")

    def send(self, receptor: str, message: str, sender: str | None = None) -> SMSResult:
        if not self.api_key:
            return SMSResult(False, None, "KAVENEGAR_API_KEY تنظیم نشده است")
        payload = urllib.parse.urlencode({
            "receptor": receptor,
            "message": message,
            **({"sender": sender or self.sender} if sender or self.sender else {}),
        }).encode("utf-8")
        url = f"{self.base_url}/{self.api_key}/sms/send.json"
        try:
            req = urllib.request.Request(url, data=payload, method="POST")
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))
            entries = (((data or {}).get("entries")) or [])
            first = entries[0] if entries else {}
            success = int(((data or {}).get("return") or {}).get("status", 0)) in {200, 201}
            return SMSResult(success, str(first.get("messageid")) if first.get("messageid") else None,
                             str(((data or {}).get("return") or {}).get("message", "")))
        except Exception as exc:
            return SMSResult(False, None, f"خطا در سرویس پیامک: {exc}")


PROVIDERS = {MockSMSProvider.code: MockSMSProvider()}
if os.getenv("KAVENEGAR_API_KEY"):
    PROVIDERS[KavenegarProvider.code] = KavenegarProvider()


def get_sms_provider(code: str | None = None) -> SMSProvider:
    selected = (code or os.getenv("EMPERATOR_SMS_PROVIDER", "mock")).strip().lower()
    if selected not in PROVIDERS:
        raise ValueError(f"SMS provider unavailable: {selected}")
    return PROVIDERS[selected]
