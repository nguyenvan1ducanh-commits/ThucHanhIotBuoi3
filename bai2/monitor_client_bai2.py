"""
Bai 2 - Chuong trinh 2: Monitoring CoAP Client
Gui GET moi 3 giay toi coap://localhost:5683/iot/lab/<device_id>/data,
phan tich JSON va canh bao:
    - temperature > 35 -> "CANH BAO: Nhiet do cao"
    - humidity    < 40 -> "CANH BAO: Do am thap"
Chay den khi nhan Ctrl+C; khi thoat in so lan GET va thoi gian phan hoi trung binh.

Cach chay:
    python monitor_client_bai2.py                          # giam sat sensor01
    python monitor_client_bai2.py --device sensor02        # (mo rong) chon thiet bi
    python monitor_client_bai2.py --csv sensor_log.csv     # (mo rong) ghi du lieu ra CSV
"""
import argparse
import asyncio
import csv
import json
import os
import time
from datetime import datetime

import aiocoap

INTERVAL = 3      # giay
TIMEOUT = 5       # giay
TEMP_MAX = 35.0
HUMIDITY_MIN = 40.0


def check_alerts(temperature: float, humidity: float) -> list:
    alerts = []
    if temperature > TEMP_MAX:
        alerts.append("CANH BAO: Nhiet do cao")
    if humidity < HUMIDITY_MIN:
        alerts.append("CANH BAO: Do am thap")
    return alerts


async def main(server: str, port: int, device: str, csv_path):
    uri = f"coap://{server}:{port}/iot/lab/{device}/data"
    ctx = await aiocoap.Context.create_client_context()
    stats = {"ok": 0, "fail": 0, "total_ms": 0.0}

    csv_file = writer = None
    if csv_path:
        new_file = not os.path.exists(csv_path)
        csv_file = open(csv_path, "a", newline="", encoding="utf-8")
        writer = csv.writer(csv_file)
        if new_file:
            writer.writerow(["received_at", "device_id", "temperature", "humidity", "alerts"])

    print(f"Monitoring {uri} moi {INTERVAL} giay  (Ctrl+C de dung)\n")
    try:
        while True:
            request = aiocoap.Message(code=aiocoap.GET, uri=uri)
            start = time.perf_counter()
            try:
                response = await asyncio.wait_for(ctx.request(request).response, TIMEOUT)
            except (asyncio.TimeoutError, aiocoap.error.NetworkError) as err:
                stats["fail"] += 1
                print(f"[{datetime.now():%H:%M:%S}] [LOI] Server khong phan hoi ({type(err).__name__}), thu lai sau {INTERVAL}s")
                print("-" * 30)
                await asyncio.sleep(INTERVAL)
                continue
            elapsed_ms = (time.perf_counter() - start) * 1000

            if not response.code.is_successful():
                stats["fail"] += 1
                print(f"[{datetime.now():%H:%M:%S}] [LOI] Server tra ve {response.code}")
                print("-" * 30)
                await asyncio.sleep(INTERVAL)
                continue

            try:
                data = json.loads(response.payload.decode("utf-8"))
                temperature = float(data["temperature"])
                humidity = float(data["humidity"])
            except (json.JSONDecodeError, KeyError, ValueError, TypeError):
                print(f"[LOI] Payload khong hop le: {response.payload!r}")
                await asyncio.sleep(INTERVAL)
                continue

            stats["ok"] += 1
            stats["total_ms"] += elapsed_ms
            now = datetime.now()
            alerts = check_alerts(temperature, humidity)
            print(f"[{now:%H:%M:%S}] Received sensor data  ({elapsed_ms:.1f} ms)")
            print(f"Device: {data['device_id']}")
            print(f"Temperature: {temperature} C")
            print(f"Humidity: {humidity} %")
            for alert in alerts:
                print(alert)
            if not alerts:
                print("Trang thai: Binh thuong")
            print("-" * 30)

            if writer:
                writer.writerow([now.isoformat(timespec="seconds"), data["device_id"],
                                 temperature, humidity, "; ".join(alerts)])
                csv_file.flush()
            await asyncio.sleep(INTERVAL)
    finally:
        if csv_file:
            csv_file.close()
        await ctx.shutdown()
        avg = stats["total_ms"] / stats["ok"] if stats["ok"] else 0
        print(f"\nSo lan GET thanh cong: {stats['ok']}, that bai: {stats['fail']}, "
              f"thoi gian phan hoi trung binh: {avg:.1f} ms")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitoring CoAP Client - Bai 2")
    parser.add_argument("--server", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5683)
    parser.add_argument("--device", default="sensor01", help="ma thiet bi can giam sat")
    parser.add_argument("--csv", default=None, help="duong dan file CSV de ghi du lieu")
    args = parser.parse_args()
    try:
        asyncio.run(main(args.server, args.port, args.device, args.csv))
    except KeyboardInterrupt:
        pass
