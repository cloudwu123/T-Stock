from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import Request, urlopen
import json

ALLOWED_PATHS = {
    "/rwd/zh/afterTrading/FMTQIK",
    "/rwd/zh/TAIEX/MI_5MINS_HIST",
    "/rwd/zh/marginTrading/MI_MARGN",
}


class Handler(SimpleHTTPRequestHandler):
    def send_json(self, status, body):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlsplit(self.path)

        if parsed.path != "/api/twse":
            return super().do_GET()

        query = parse_qs(parsed.query)
        api_path = query.pop("path", [""])[0]

        if api_path not in ALLOWED_PATHS:
            body = json.dumps(
                {"error": "TWSE endpoint not allowed"},
                ensure_ascii=False
            ).encode("utf-8")
            return self.send_json(400, body)

        params = {key: values[-1] for key, values in query.items() if values}
        target = "https://www.twse.com.tw" + api_path + "?" + urlencode(params)

        request = Request(
            target,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://www.twse.com.tw/",
                "Accept": "application/json, text/plain, */*",
            },
        )

        try:
            with urlopen(request, timeout=30) as response:
                self.send_json(200, response.read())
        except HTTPError as error:
            self.send_json(
                error.code,
                error.read() or json.dumps(
                    {"error": f"TWSE HTTP {error.code}"},
                    ensure_ascii=False
                ).encode("utf-8")
            )
        except (URLError, TimeoutError) as error:
            body = json.dumps(
                {"error": f"無法連線證交所：{error}"},
                ensure_ascii=False
            ).encode("utf-8")
            self.send_json(502, body)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    print("請用瀏覽器開啟 http://127.0.0.1:8000/dashboard.html")
    server.serve_forever()
