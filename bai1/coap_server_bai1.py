"""
Bai 1 - Chuong trinh 1: CoAP Server
Tai nguyen: coap://localhost:5683/iot/lab/message
    GET  -> tra ve thong diep chao mung (kem thong diep POST gan nhat - mo rong)
    POST -> nhan thong diep tu Client, in noi dung + thoi diem nhan, tra ve 2.04 Changed

Cach chay:
    python coap_server_bai1.py
    python coap_server_bai1.py --host 0.0.0.0     # cho phep may khac trong LAN truy cap
"""
import argparse
import asyncio
from datetime import datetime

import aiocoap
import aiocoap.resource as resource

WELCOME = "Xin chao tu CoAP Server"


class MessageResource(resource.Resource):
    """Tai nguyen /iot/lab/message."""

    def __init__(self):
        super().__init__()
        self.last_message = None  # (mo rong) luu thong diep POST gan nhat

    async def render_get(self, request):
        print(f"GET request received: /iot/lab/message   ({datetime.now():%H:%M:%S})")
        text = WELCOME
        if self.last_message:
            text += f" | Thong diep gan nhat: {self.last_message}"
        return aiocoap.Message(code=aiocoap.CONTENT, payload=text.encode("utf-8"))

    async def render_post(self, request):
        message = request.payload.decode("utf-8", errors="replace").strip()
        if not message:
            return aiocoap.Message(code=aiocoap.BAD_REQUEST, payload=b"Payload rong")
        self.last_message = message
        print("POST request received:")
        print(f"Payload: {message}")
        print(f"Time: {datetime.now():%H:%M:%S}")
        print("-" * 50)
        return aiocoap.Message(code=aiocoap.CHANGED, payload=b"Server da nhan thong diep")


async def main(host: str, port: int):
    root = resource.Site()
    root.add_resource(["iot", "lab", "message"], MessageResource())
    await aiocoap.Context.create_server_context(root, bind=(host, port))
    print(f"CoAP Server started on port {port}")
    print(f"Resource: coap://{host}:{port}/iot/lab/message  (Ctrl+C de dung)\n")
    await asyncio.get_running_loop().create_future()  # chay mai mai


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CoAP Server - Bai 1")
    parser.add_argument("--host", default="127.0.0.1", help="dia chi lang nghe (mac dinh 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5683)
    args = parser.parse_args()
    try:
        asyncio.run(main(args.host, args.port))
    except KeyboardInterrupt:
        print("\nServer da dung.")
