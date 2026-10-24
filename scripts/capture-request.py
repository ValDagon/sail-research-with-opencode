#!/usr/bin/env python3
"""Local OpenAI-compatible sink for inspecting what OpenCode sends to Sail.

Usage:
    python3 capture-request.py --port 8765 --log /tmp/sail-request.jsonl

It records one JSON object per request (method, path, headers, body) and
answers with a minimal Chat Completions response, so an OpenCode run can
finish normally. Authorization headers are redacted before logging.
"""

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--log", default="/tmp/sail-request.jsonl")
    return parser.parse_args()


ARGS = parse_args()


def redact(headers):
    out = {}
    for key, value in headers.items():
        lowered = key.lower()
        if lowered in ("authorization", "x-api-key"):
            out[lowered] = "<redacted>"
        else:
            out[lowered] = value
    return out


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            body = json.loads(raw)
        except Exception:
            body = raw.decode("utf-8", "replace")

        record = {
            "method": self.command,
            "path": self.path,
            "headers": redact(self.headers),
            "body": body,
        }
        with open(ARGS.log, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        model = body.get("model", "sink") if isinstance(body, dict) else "sink"
        print(f"{self.path} model={model}", flush=True)

        if isinstance(body, dict) and body.get("stream"):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            for event in (
                {
                    "id": "chatcmpl-sink",
                    "object": "chat.completion.chunk",
                    "created": 0,
                    "model": model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"role": "assistant", "content": "OK"},
                            "finish_reason": None,
                        }
                    ],
                },
                {
                    "id": "chatcmpl-sink",
                    "object": "chat.completion.chunk",
                    "created": 0,
                    "model": model,
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                    "usage": {
                        "prompt_tokens": 1,
                        "completion_tokens": 1,
                        "total_tokens": 2,
                        "completion_tokens_details": {"reasoning_tokens": 0},
                    },
                },
            ):
                self.wfile.write(("data: " + json.dumps(event) + "\n\n").encode())
            self.wfile.write(b"data: [DONE]\n\n")
            return

        payload = {
            "id": "chatcmpl-sink",
            "object": "chat.completion",
            "created": 0,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "OK"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 1,
                "completion_tokens": 1,
                "total_tokens": 2,
                "completion_tokens_details": {"reasoning_tokens": 0},
            },
        }
        data = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", ARGS.port), Handler)
    print(f"listening on http://127.0.0.1:{ARGS.port}/v1 -> {ARGS.log}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
