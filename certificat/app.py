#!/usr/bin/env python3
"""
Completely fixed Markov server.
Pure Python. Safe HTML template.
"""

import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from markov_gen import MarkovChain, tokenize
from datetime import datetime

HOST = "127.0.0.1"
PORT = 8000
MODEL_PATH = "model.json"

def html_page(output):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>Markov Generator</title>

<style>
    body {{
        margin: 0;
        padding: 40px;
        font-family: 'Inter', system-ui, sans-serif;
        background: #f5f5f5;
        color: #222;
        display: flex;
        justify-content: center;
    }}

    .container {{
        width: 100%;
        max-width: 780px;
    }}

    h2 {{
        text-align: center;
        font-weight: 600;
        margin-bottom: 30px;
    }}

    .card {{
        background: #fff;
        padding: 24px;
        border-radius: 14px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        margin-bottom: 22px;
    }}

    label {{
        font-size: 14px;
        font-weight: 500;
        display: block;
        margin-bottom: 6px;
        color: #444;
    }}

    input[type=text], textarea {{
        width: 100%;
        padding: 12px;
        border-radius: 10px;
        border: 1px solid #ddd;
        background: #fafafa;
        font-size: 14px;
        transition: 0.2s ease;
        outline: none;
    }}

    input[type=text]:focus, textarea:focus {{
        border-color: #000;
        background: #fff;
    }}

    textarea {{
        height: 150px;
        resize: vertical;
    }}

    button {{
        padding: 12px 22px;
        border: none;
        border-radius: 10px;
        background: #000;
        color: #fff;
        font-size: 14px;
        cursor: pointer;
        transition: 0.2s ease;
        margin-top: 10px;
    }}

    button:hover {{
        background: #333;
    }}

    pre {{
        background: #111;
        color: #fff;
        padding: 18px;
        border-radius: 10px;
        white-space: pre-wrap;
        font-size: 14px;
        overflow-x: auto;
    }}

    footer {{
        margin-top: 30px;
        text-align: center;
        color: #888;
        font-size: 13px;
    }}
</style>

</head>
<body>
<div class="container">

    <h2>Markov Text Generator</h2>

    <div class="card">
        <h3 style="margin-top:0; font-weight:600;">Train Model</h3>
        <form method="POST" action="/train">
            <label>Order (context size)</label>
            <input type="text" name="order" value="2">

            <label style="margin-top:14px;">Training Corpus</label>
            <textarea name="corpus">The sun rose. The sun set. The cat slept.</textarea>

            <button type="submit">Train Model</button>
        </form>
    </div>

    <div class="card">
        <h3 style="margin-top:0; font-weight:600;">Generate Text</h3>
        <form method="POST" action="/generate">
            <label>Start phrase (optional)</label>
            <input type="text" name="start" placeholder="Once upon a time">

            <label style="margin-top:14px;">Max words</label>
            <input type="text" name="length" value="80">

            <button type="submit">Generate</button>
        </form>
    </div>

    <div class="card">
        <h3 style="margin-top:0; font-weight:600;">Output</h3>
        {output}
    </div>

    <footer>
        Server time: {datetime.now()}
    </footer>

</div>
</body>
</html>"""



class Handler(BaseHTTPRequestHandler):

    def _send(self, text):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(text.encode())))
        self.end_headers()
        self.wfile.write(text.encode())

    def _post(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode()
        return urllib.parse.parse_qs(body)

    def do_GET(self):
        print(f"GET {self.path}")
        self._send(html_page("<em>No output yet</em>"))

    def do_POST(self):
        print(f"POST {self.path}")

        if self.path == "/train":
            data = self._post()
            order = int(data.get("order", ["2"])[0])
            corpus = data.get("corpus", [""])[0]

            tokens = tokenize(corpus)
            mc = MarkovChain(order)
            mc.train(tokens)
            mc.save(MODEL_PATH)

            self._send(html_page(f"<pre>Model trained.\nTokens: {len(tokens)}</pre>"))
            return

        if self.path == "/generate":
            data = self._post()

            start = data.get("start", [""])[0].split()
            length = int(data.get("length", ["80"])[0])

            mc = MarkovChain.load(MODEL_PATH)
            text = mc.generate(max_words=length, start=start if start else None)

            self._send(html_page(f"<pre>{text}</pre>"))
            return

        self._send(html_page("<pre>Unknown route</pre>"))


def run():
    print(f"\nRunning server on http://127.0.0.1:{PORT}")
    print("Press Ctrl+C to stop\n")
    HTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    run()
