"""Local thermal-printer bridge for Emperator desktop builds."""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = "127.0.0.1"
PORT = int(os.getenv("EMPERATOR_PRINTER_PORT", "8765"))


class Handler(BaseHTTPRequestHandler):
    def _headers(self, content_type="application/json; charset=utf-8"):
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code, payload):
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self._headers()
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self):
        self.send_response(204)
        self._headers()
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self._json(200, {"ok": True, "service": "emperator-printer-bridge"})
        elif self.path == "/printers":
            try:
                import win32print
                flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
                printers = [p[2] for p in win32print.EnumPrinters(flags)]
                self._json(200, {"ok": True, "printers": printers, "default": win32print.GetDefaultPrinter()})
            except Exception as exc:
                self._json(500, {"ok": False, "error": str(exc)})
        else:
            self._json(404, {"ok": False})

    def do_POST(self):
        if self.path != "/print":
            self._json(404, {"ok": False})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = self.rfile.read(length)
            if not data:
                self._json(400, {"ok": False, "error": "داده چاپ خالی است"})
                return
            import win32print
            printer = os.getenv("EMPERATOR_PRINTER_NAME") or win32print.GetDefaultPrinter()
            handle = win32print.OpenPrinter(printer)
            try:
                win32print.StartDocPrinter(handle, 1, ("Emperator Receipt", None, "RAW"))
                win32print.StartPagePrinter(handle)
                win32print.WritePrinter(handle, data)
                win32print.EndPagePrinter(handle)
                win32print.EndDocPrinter(handle)
            finally:
                win32print.ClosePrinter(handle)
            self._json(200, {"ok": True, "printer": printer})
        except Exception as exc:
            self._json(500, {"ok": False, "error": str(exc)})

    def log_message(self, fmt, *args):
        return


if __name__ == "__main__":
    HTTPServer((HOST, PORT), Handler).serve_forever()
