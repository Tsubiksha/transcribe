from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent / "dist"
HOST = "127.0.0.1"
PORT = 5173


class FrontendHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        requested = ROOT / self.path.lstrip("/").split("?", 1)[0]
        if self.path.startswith("/assets/") or requested.exists():
            return super().do_GET()
        self.path = "/index.html"
        return super().do_GET()


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), FrontendHandler)
    print(f"Frontend running at http://{HOST}:{PORT}", flush=True)
    server.serve_forever()
