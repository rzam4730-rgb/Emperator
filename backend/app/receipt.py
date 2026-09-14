"""ESC/POS receipt rendering for 58mm/80mm thermal printers."""
from __future__ import annotations

WIDTHS = {58: 32, 80: 48}

def _line(text: str, width: int) -> str:
    return text[:width].ljust(width)

def render_receipt(order: dict, items: list[dict], paper_mm: int = 58) -> bytes:
    width = WIDTHS.get(int(paper_mm), 32)
    out = bytearray(b'\x1b@')
    out += b'\x1b\x61\x01' + 'امپراتور\n'.encode('utf-8') + b'\x1b\x61\x00'
    out += ('-' * width + '\n').encode('ascii')
    for item in items:
        name = str(item.get('name', ''))
        qty = int(item.get('quantity', 1))
        price = int(item.get('price', 0))
        total = qty * price
        left = f'{qty}x {name}'[:width-12]
        right = f'{total:,}'
        out += (_line(left, width-len(right)) + right + '\n').encode('utf-8')
    out += ('-' * width + '\n').encode('ascii')
    total = int(order.get('total', 0))
    label = 'جمع کل'
    right = f'{total:,}'
    out += (_line(label, width-len(right)) + right + '\n').encode('utf-8')
    out += b'\n\n\x1d\x56\x00'
    return bytes(out)
