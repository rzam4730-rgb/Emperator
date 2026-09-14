"""Local thermal-printer bridge for Emperator desktop builds."""
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = "127.0.0.1"
PORT = int(os.getenv("EMPERATOR_PRINTER_PORT", "8765"))

class Handler(BaseHTTPRequestHandler):
    def _json(self, code, body):
        raw = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/health":
            self._json(200, '{"ok":true,"service":"emperator-printer-bridge"}')
        else:
            self._json(404, '{"ok":false}')

    def do_POST(self):
        if self.path != "/print":
            self._json(404, '{"ok":false}')
            return
        length = int(self.headers.get("Content-Length", "0"))
        data = self.rfile.read(length)
        try:
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
            self._json(200, '{"ok":true}')
        except Exception as exc:
            self._json(500, '{"ok":false,"error":' + repr(str(exc)).replace("'", '"') + '}')

    def log_message(self, fmt, *args):
        return

if __name__ == "__main__":
    HTTPServer((HOST, PORT), Handler).serve_forever()
