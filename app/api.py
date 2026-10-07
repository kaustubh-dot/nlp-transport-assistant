"""Local JSON application endpoint for the production T3 assistant."""

from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

from src.nlp_v2.assistant import AssistantReply, T3Assistant


MAX_REQUEST_BYTES = 8192
SOCKET_TIMEOUT_SECONDS = 5


class RequestTimeout(TimeoutError):
    """The client did not complete its request body within the socket timeout."""


def read_body(stream, length: int) -> bytes:
    try:
        return stream.read(length)
    except TimeoutError as exc:
        raise RequestTimeout("Request body timed out") from exc


def public_reply(reply: AssistantReply) -> dict:
    """Expose the stable frontend contract without model or raw-text internals."""
    return {
        "status": reply.status,
        'outcome_reason': reply.outcome_reason,
        "response_text": reply.response_text,
        "intent": reply.intent,
        "operation": reply.operation,
        "slots": reply.slots,
        "data": reply.data,
        "missing_slots": list(reply.missing_slots),
        "clarification_reason": reply.clarification_reason,
        "candidate_entities": list(reply.candidate_entities),
        "candidate_intents": list(reply.candidate_intents),
    }


def handle_request(method: str, path: str, headers: dict, body: bytes, assistant: T3Assistant) -> tuple[int, dict]:
    """Validate one request independently of the socket adapter."""
    def error(status: HTTPStatus, message: str) -> tuple[int, dict]:
        return status, {"status": "error", "response_text": message,
                        'outcome_reason': 'temporary_service_unavailability' if status == HTTPStatus.SERVICE_UNAVAILABLE else 'malformed_request'}

    headers = {key.lower(): value for key, value in headers.items()}
    if method == "GET":
        if path == "/health":
            return HTTPStatus.OK, {"status": "ok", "taxonomy": "T3"}
        return error(HTTPStatus.NOT_FOUND, "Endpoint not found.")
    if method != "POST" or path != "/api/v2/query":
        return error(HTTPStatus.NOT_FOUND, "Endpoint not found.")
    media_type = headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if media_type != "application/json":
        return error(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "Send application/json.")
    try:
        length = int(headers.get("content-length", ""))
    except ValueError:
        return error(HTTPStatus.LENGTH_REQUIRED, "Content-Length is required.")
    if length < 0 or length > MAX_REQUEST_BYTES:
        return error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "Query body is too large.")
    if len(body) != length:
        return error(HTTPStatus.BAD_REQUEST, "Incomplete JSON request.")
    try:
        data = json.loads(body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return error(HTTPStatus.BAD_REQUEST, "Invalid JSON request.")
    if not isinstance(data, dict) or not isinstance(data.get("query"), str) or not data["query"].strip():
        return error(HTTPStatus.UNPROCESSABLE_ENTITY, "Provide a nonempty query string.")
    try:
        reply = assistant.process_query(data["query"])
        status = HTTPStatus.OK
        if reply.status == 'error':
            status = HTTPStatus.UNPROCESSABLE_ENTITY if reply.outcome_reason == 'malformed_request' else HTTPStatus.SERVICE_UNAVAILABLE
        return status, public_reply(reply)
    except Exception:
        return error(HTTPStatus.SERVICE_UNAVAILABLE, "The assistant is temporarily unavailable.")


def make_server(host: str, port: int, assistant: T3Assistant) -> HTTPServer:
    """Build a local HTTP server with an injectable assistant for API tests."""

    class Handler(BaseHTTPRequestHandler):
        def setup(self) -> None:
            self.request.settimeout(SOCKET_TIMEOUT_SECONDS)
            super().setup()

        def log_message(self, format: str, *args) -> None:
            pass

        def _json(self, status: HTTPStatus, body: dict) -> None:
            payload = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self) -> None:
            status, response = handle_request("GET", self.path, dict(self.headers), b"", assistant)
            self._json(status, response)

        def do_POST(self) -> None:
            try:
                length = int(self.headers.get("Content-Length", ""))
            except ValueError:
                length = 0
            try:
                body = read_body(self.rfile, length) if 0 <= length <= MAX_REQUEST_BYTES else b""
            except RequestTimeout:
                self.close_connection = True
                self._json(HTTPStatus.REQUEST_TIMEOUT, {
                    "status": "error", "response_text": "Request body timed out.",
                    'outcome_reason': 'malformed_request',
                })
                return
            status, response = handle_request("POST", self.path, dict(self.headers), body, assistant)
            self._json(status, response)

    return HTTPServer((host, port), Handler)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    assistant = T3Assistant()
    server = make_server(args.host, args.port, assistant)
    print(f"T3 assistant API listening at http://{args.host}:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
