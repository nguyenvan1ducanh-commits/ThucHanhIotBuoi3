"""
Bai 3 - Chuong trinh 3: Light Monitoring Client
Dang ky CoAP Observe (GET voi option Observe = 0) toi
    coap://localhost:5683/iot/lab/light01/status
Nhan trang thai ban dau, sau do CHI cho server tu day thong bao khi trang thai doi.
KHONG dung vong lap GET dinh ky.

Cach chay:
    python light_monitor_bai3.py
    python light_monitor_bai3.py --device fan01      # (mo rong) theo doi thiet bi khac
Co the mo nhieu cua so monitor cung luc - tat ca deu nhan thong bao.
"""
import argparse
import asyncio
import json
from datetime import datetime

import aiocoap

TIMEOUT = 5


def show(title: str, payload: bytes):
    try:
        data = json.loads(payload.decode("utf-8"))
        device, status = data["device_id"], data["status"]
    except (json.JSONDecodeError, KeyError, UnicodeDecodeError):
        print(f"[{datetime.now():%H:%M:%S}] [LOI] Payload khong hop le: {payload!r}")
        return
    print(f"[{datetime.now():%H:%M:%S}] {title}")
    print(f"Device: {device}")
    print(f"Status: {status}\n")


async def main(server: str, port: int, device: str):
    uri = f"coap://{server}:{port}/iot/lab/{device}/status"
    ctx = await aiocoap.Context.create_client_context()
    try:
        print("Registering CoAP Observe...")
        print(f"URI: {uri}")
        req = ctx.request(aiocoap.Message(code=aiocoap.GET, uri=uri, observe=0))
        try:
            first = await asyncio.wait_for(req.response, TIMEOUT)
        except (asyncio.TimeoutError, aiocoap.error.NetworkError) as err:
            print(f"[LOI] Khong dang ky duoc Observe: {type(err).__name__} - server co dang chay khong?")
            return
        if not first.code.is_successful():
            print(f"[LOI] Server tra ve {first.code}")
            return
        if first.opt.observe is None:
            print("[CANH BAO] Server khong ho tro Observe cho tai nguyen nay")
        else:
            print("Observe registration successful  (Ctrl+C de dung)\n")
        show("Initial State", first.payload)

        # Moi lan server goi updated_state(), mot thong bao moi den day
        async for notification in req.observation:
            show("State Updated", notification.payload)
        print("Server da ket thuc Observe.")
    finally:
        await ctx.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Light Monitoring Client - Bai 3")
    parser.add_argument("--server", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5683)
    parser.add_argument("--device", default="light01")
    args = parser.parse_args()
    try:
        asyncio.run(main(args.server, args.port, args.device))
    except KeyboardInterrupt:
        print("\nDa dung theo doi.")
