"""
Bai 1 - Chuong trinh 2: CoAP Client
    1. GET  coap://<server>:5683/iot/lab/message  -> in Code va Payload
    2. POST thong diep chua thong tin sinh vien   -> in Code va Payload
    3. (mo rong) GET tai nguyen khong ton tai      -> nhan 4.04 Not Found

Cach chay:
    python coap_client_bai1.py
    python coap_client_bai1.py -n 3               # (mo rong) gui 3 thong diep POST lien tiep
    python coap_client_bai1.py --server 192.168.1.10
"""
import argparse
import asyncio

import aiocoap

STUDENT_NAME = "Nguyen Van Duc Anh"   # Nguyễn Văn Đức Anh
STUDENT_ID = "B23DCCN040"
GREETING = "Xin chao tu CoAP Client"
TIMEOUT = 5  # giay


async def send(ctx, code, uri, payload=b""):
    """Gui 1 request, in ket qua. Tra ve response hoac None neu loi."""
    request = aiocoap.Message(code=code, uri=uri, payload=payload)
    try:
        response = await asyncio.wait_for(ctx.request(request).response, TIMEOUT)
    except asyncio.TimeoutError:
        print(f"[LOI] Server khong phan hoi sau {TIMEOUT} giay (server co dang chay khong?)\n")
        return None
    except aiocoap.error.NetworkError:
        print("[LOI] Khong ket noi duoc server (server chua chay hoac sai dia chi)\n")
        return None
    print("Response:")
    print(f"Code: {response.code}")
    text = response.payload.decode("utf-8", errors="replace")
    print(f"Payload: {text if text else '(trong)'}\n")
    return response


async def main(server: str, port: int, count: int):
    base = f"coap://{server}:{port}"
    uri = f"{base}/iot/lab/message"
    ctx = await aiocoap.Context.create_client_context()
    try:
        print("Sending GET request...")
        print(f"URI: {uri}")
        if await send(ctx, aiocoap.GET, uri) is None:
            return

        for i in range(1, count + 1):
            message = f"{GREETING} - {STUDENT_ID} - {STUDENT_NAME}"
            if count > 1:
                message += f" (#{i})"
            print("Sending POST request...")
            print(f"Payload: {message}")
            await send(ctx, aiocoap.POST, uri, message.encode("utf-8"))

        # (mo rong) GET lai de thay server tra ve thong diep POST gan nhat
        print("Sending GET request (sau khi POST)...")
        await send(ctx, aiocoap.GET, uri)

        # (mo rong) truy cap tai nguyen khong ton tai
        bad_uri = f"{base}/iot/lab/khong_ton_tai"
        print("Sending GET request toi tai nguyen khong ton tai...")
        print(f"URI: {bad_uri}")
        await send(ctx, aiocoap.GET, bad_uri)
    finally:
        await ctx.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CoAP Client - Bai 1")
    parser.add_argument("--server", default="127.0.0.1", help="dia chi IP cua CoAP Server")
    parser.add_argument("--port", type=int, default=5683)
    parser.add_argument("-n", "--count", type=int, default=1, help="so thong diep POST")
    args = parser.parse_args()
    print("CoAP Client\n")
    asyncio.run(main(args.server, args.port, args.count))
