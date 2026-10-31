"""
Bai 3 - Chuong trinh 2: Light Controller Client
Lenh nhap tu ban phim:
    ON / OFF  -> PUT {"device_id": "light01", "command": "ON|OFF"}
    STATUS    -> GET trang thai hien tai
    EXIT      -> thoat
    (mo rong) <device_id> ON|OFF|STATUS, vd: fan01 ON

Cach chay:
    python light_controller_bai3.py
    python light_controller_bai3.py --non        # (mo rong) gui ban tin Non-confirmable
"""
import argparse
import asyncio
import json

import aiocoap

TIMEOUT = 5
DEFAULT_DEVICE = "light01"
PROMPT = "Nhap lenh (ON/OFF/STATUS/EXIT): "


def make_message(non: bool, **kwargs):
    """Tao Message kieu CON (mac dinh, co ACK) hoac NON (khong can ACK)."""
    if hasattr(aiocoap, "Reliable"):          # aiocoap >= 0.4.17
        kwargs["transport_tuning"] = aiocoap.Unreliable() if non else aiocoap.Reliable()
    else:                                      # aiocoap cu
        kwargs["mtype"] = aiocoap.NON if non else aiocoap.CON
    return aiocoap.Message(**kwargs)


async def request(ctx, msg):
    try:
        return await asyncio.wait_for(ctx.request(msg).response, TIMEOUT)
    except asyncio.TimeoutError:
        print(f"[LOI] Server khong phan hoi sau {TIMEOUT} giay\n")
    except aiocoap.error.NetworkError:
        print("[LOI] Khong ket noi duoc server (server chua chay hoac sai dia chi)\n")
    return None


async def main(server: str, port: int, non: bool):
    ctx = await aiocoap.Context.create_client_context()
    loop = asyncio.get_running_loop()
    print(f"Light Controller - server {server}:{port} - kieu ban tin: {'NON' if non else 'CON'}\n")
    try:
        while True:
            line = (await loop.run_in_executor(None, input, PROMPT)).strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) == 1:
                device, cmd = DEFAULT_DEVICE, parts[0].upper()
            elif len(parts) == 2:
                device, cmd = parts[0], parts[1].upper()
            else:
                print("[LOI] Sai cu phap. Vi du: ON | OFF | STATUS | fan01 ON | EXIT\n")
                continue
            if cmd == "EXIT":
                break
            uri = f"coap://{server}:{port}/iot/lab/{device}/status"

            if cmd == "STATUS":
                print("Sending GET request...")
                resp = await request(ctx, make_message(non, code=aiocoap.GET, uri=uri))
                if resp:
                    print("Response:")
                    print(resp.payload.decode("utf-8", errors="replace") if resp.code.is_successful()
                          else f"Code: {resp.code} - {resp.payload.decode('utf-8', errors='replace')}")
                    print()
                continue

            # ON / OFF (va ca lenh sai) deu gui len server; server tu kiem tra va tra 4.00 neu sai
            body = json.dumps({"device_id": device, "command": cmd}).encode("utf-8")
            print("Sending PUT request...")
            resp = await request(ctx, make_message(non, code=aiocoap.PUT, uri=uri, payload=body))
            if resp is None:
                continue
            print(f"Response Code: {resp.code}")
            if resp.code.is_successful():
                print(f"Da {'bat' if cmd == 'ON' else 'tat'} den {device}" if device.startswith("light")
                      else f"Da {'bat' if cmd == 'ON' else 'tat'} {device}")
            else:
                print(f"Server bao loi: {resp.payload.decode('utf-8', errors='replace')}")
            print()
    except (KeyboardInterrupt, EOFError):
        print()
    finally:
        await ctx.shutdown()
        print("Thoat controller.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Light Controller Client - Bai 3")
    parser.add_argument("--server", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5683)
    parser.add_argument("--non", action="store_true", help="gui ban tin Non-confirmable (NON)")
    args = parser.parse_args()
    try:
        asyncio.run(main(args.server, args.port, args.non))
    except KeyboardInterrupt:
        pass
