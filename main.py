from datetime import datetime
import json
import mimetypes
import socket
from pathlib import Path
from urllib.parse import unquote_plus

from jinja2 import Environment, FileSystemLoader, select_autoescape

HOST = "0.0.0.0"
PORT = 3000
BUFFER_SIZE = 1024

BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = BASE_DIR / "storage"
DATA_FILE = STORAGE_DIR / "data.json"

jinja_env = Environment(
    loader=FileSystemLoader(BASE_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)


def ensure_storage() -> None:
    STORAGE_DIR.mkdir(exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text("{}", encoding="utf-8")


def read_messages() -> dict:
    ensure_storage()
    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        return {}


def save_message(data: dict) -> None:
    messages = read_messages()
    messages[str(datetime.now())] = {
        "username": data.get("username", ""),
        "message": data.get("message", ""),
    }

    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(messages, file, ensure_ascii=False, indent=2)


def parse_form_data(body: bytes) -> dict:
    """Convert POST request byte string into a Python dictionary."""
    decoded_body = body.decode("utf-8")
    result = {}

    for item in decoded_body.split("&"):
        if not item:
            continue
        key, value = item.split("=", 1)
        result[unquote_plus(key)] = unquote_plus(value)

    return result


def get_full_request(client_socket: socket.socket, first_part: bytes) -> bytes:
    request = first_part
    headers = request.split(b"\r\n\r\n", 1)[0]
    content_length = 0

    for line in headers.split(b"\r\n"):
        if line.lower().startswith(b"content-length:"):
            content_length = int(line.split(b":", 1)[1].strip())
            break

    if content_length:
        body = request.split(b"\r\n\r\n", 1)[1] if b"\r\n\r\n" in request else b""
        while len(body) < content_length:
            chunk = client_socket.recv(BUFFER_SIZE)
            if not chunk:
                break
            request += chunk
            body = request.split(b"\r\n\r\n", 1)[1]

    return request


def build_response(status: str, content: bytes, content_type: str = "text/html; charset=utf-8") -> bytes:
    return (
        f"HTTP/1.1 {status}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(content)}\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).encode("utf-8") + content


def redirect_response(location: str) -> bytes:
    return (
        "HTTP/1.1 302 Found\r\n"
        f"Location: {location}\r\n"
        "Content-Length: 0\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).encode("utf-8")


def read_file_response(file_name: str, status: str = "200 OK") -> bytes:
    file_path = BASE_DIR / file_name
    if not file_path.exists():
        return error_404_response()

    content = file_path.read_bytes()
    content_type = mimetypes.guess_type(file_path.name)[0] or "text/plain"
    if content_type.startswith("text/"):
        content_type += "; charset=utf-8"

    return build_response(status, content, content_type)


def read_page_response() -> bytes:
    template = jinja_env.get_template("read.html")
    html = template.render(messages=read_messages()).encode("utf-8")
    return build_response("200 OK", html)


def error_404_response() -> bytes:
    return read_file_response("error.html", "404 Not Found")


def route_request(request: bytes) -> bytes:
    request_line = request.split(b"\r\n", 1)[0].decode("utf-8")
    method, path, *_ = request_line.split()

    if method == "GET":
        if path in ("/", "/index.html"):
            return read_file_response("index.html")
        if path == "/message.html":
            return read_file_response("message.html")
        if path == "/read":
            return read_page_response()
        if path == "/style.css":
            return read_file_response("style.css")
        if path == "/logo.png":
            return read_file_response("logo.png")
        return error_404_response()

    if method == "POST" and path == "/message":
        body = request.split(b"\r\n\r\n", 1)[1]
        form_data = parse_form_data(body)
        save_message(form_data)
        return redirect_response("/read")

    return error_404_response()


def run_server() -> None:
    ensure_storage()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"Server started at http://localhost:{PORT}")

        while True:
            client_socket, address = server_socket.accept()
            with client_socket:
                first_part = client_socket.recv(BUFFER_SIZE)
                if not first_part:
                    continue
                request = get_full_request(client_socket, first_part)
                response = route_request(request)
                client_socket.sendall(response)


if __name__ == "__main__":
    run_server()
