"""Provider-neutral payment core for Emperator.

The module creates payment intents and verifies a gateway result through a
small adapter interface. A real Iranian gateway can be plugged in later
without changing subscription/business logic.
"""
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
    def create(self, amount: int, description: str, callback_url: str, metadata: dict[str, Any] | None = None) -> PaymentStart:
        raise NotImplementedError

    @abstractmethod
    def verify(self, amount: int, authority: str) -> PaymentVerify:
        raise NotImplementedError


class MockGateway(PaymentGateway):
    """Development gateway; never use it for production money collection."""
    code = "mock"

    def create(self, amount: int, description: str, callback_url: str, metadata=None) -> PaymentStart:
        import secrets
        authority = "MOCK-" + secrets.token_urlsafe(18)
        return PaymentStart(authority=authority, payment_url=f"/api/payments/mock/{authority}")

    def verify(self, amount: int, authority: str) -> PaymentVerify:
        return PaymentVerify(success=True, transaction_id=authority, message="Mock payment verified")


GATEWAYS = {MockGateway.code: MockGateway()}


def get_gateway(code: str) -> PaymentGateway:
    gateway = GATEWAYS.get(code)
    if not gateway:
        raise ValueError(f"Unsupported payment gateway: {code}")
    return gateway
