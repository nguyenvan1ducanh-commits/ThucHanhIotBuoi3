"""
Bai 2 - Chuong trinh 1: Sensor CoAP Server
Mo phong cam bien nhiet do / do am. Moi cam bien la 1 tai nguyen:
    coap://localhost:5683/iot/lab/<device_id>/data
Du lieu duoc cap nhat tu dong moi 3 giay; GET tra ve gia tri moi nhat dang JSON
(Content-Format: application/json).

Cach chay:
    python sensor_server_bai2.py                                       # chi sensor01
    python sensor_server_bai2.py --devices sensor01 sensor02 sensor03  # (mo rong) 3 cam bien
"""
import argparse
import asyncio
import json
import random
from datetime import datetime

import aiocoap
import aiocoap.resource as resource
from aiocoap.numbers import ContentFormat

UPDATE_INTERVAL = 3  # giay


class SensorResource(resource.Resource):
    """Tai nguyen /iot/lab/<device_id>/data."""

    def __init__(self, device_id: str):
        super().__init__()
        self.device_id = device_id
        self.data = {}
        self.update()

    def update(self):
        """Sinh gia tri ngau nhien; khoang gia tri cho phep thinh thoang vuot nguong."""
        self.data = {
            "device_id": self.device_id,
            "temperature": round(random.uniform(24.0, 38.0), 1),
            "humidity": round(random.uniform(35.0, 85.0), 1),
            "timestamp": datetime.now().isoformat(timespec="seconds"),  # (mo rong)
        }

    async def render_get(self, request):
        print(f"[{datetime.now():%H:%M:%S}] GET /iot/lab/{self.device_id}/data -> "
              f"{self.data['temperature']} C, {self.data['humidity']} %")
        return aiocoap.Message(code=aiocoap.CONTENT,
                               payload=json.dumps(self.data).encode("utf-8"),
                               content_format=ContentFormat.JSON)


async def update_loop(sensors):
    """Cap nhat du lieu cam bien moi 3 giay."""
    while True:
        await asyncio.sleep(UPDATE_INTERVAL)
        for s in sensors:
            s.update()


async def main(host: str, port: int, devices):
    root = resource.Site()
    sensors = []
    for device_id in devices:
        res = SensorResource(device_id)
        root.add_resource(["iot", "lab", device_id, "data"], res)
        sensors.append(res)
    await aiocoap.Context.create_server_context(root, bind=(host, port))
    print(f"CoAP Sensor Server started on port {port}")
    for device_id in devices:
        print(f"Resource: coap://{host}:{port}/iot/lab/{device_id}/data")
    print(f"Du lieu cap nhat moi {UPDATE_INTERVAL} giay  (Ctrl+C de dung)\n")
    await update_loop(sensors)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sensor CoAP Server - Bai 2")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5683)
    parser.add_argument("--devices", nargs="+", default=["sensor01"])
    args = parser.parse_args()
    try:
        asyncio.run(main(args.host, args.port, args.devices))
    except KeyboardInterrupt:
        print("\nServer da dung.")
