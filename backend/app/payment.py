"""Provider-neutral payment core for Emperator."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

@dataclass
class PaymentStart:
    authority: str
    payment_url: str

@dataclass
class PaymentVerify:
    success: bool
    transaction_id: str | None = None
    message: str = ""

class PaymentGateway(ABC):
    code = "abstract"
    @abstractmethod
    def create(self, amount: int, description: str, callback_url: str, metadata: dict[str, Any] | None = None) -> PaymentStart: ...
    @abstractmethod
    def verify(self, amount: int, authority: str) -> PaymentVerify: ...

class MockGateway(PaymentGateway):
    code = "mock"
    def create(self, amount, description, callback_url, metadata=None):
        import secrets
        authority = "MOCK-" + secrets.token_urlsafe(18)
        return PaymentStart(authority, f"/api/payments/mock/{authority}")
    def verify(self, amount, authority):
        return PaymentVerify(True, authority, "Mock payment verified")

GATEWAYS = {MockGateway.code: MockGateway()}
try:
    from .gateway_zarinpal import ZarinPalGateway
    GATEWAYS["zarinpal"] = ZarinPalGateway()
except Exception:
    pass

def get_gateway(code: str) -> PaymentGateway:
    gateway = GATEWAYS.get(code)
    if not gateway:
        raise ValueError(f"Unsupported payment gateway: {code}")
    return gateway
