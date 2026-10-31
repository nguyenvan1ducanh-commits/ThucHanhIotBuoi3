"""
Bai 3 - Chuong trinh 1: Smart Light CoAP Server
Tai nguyen: coap://localhost:5683/iot/lab/light01/status
    GET     -> {"device_id": "light01", "status": "ON|OFF", "timestamp": ...}
    PUT     -> nhan {"device_id": "light01", "command": "ON|OFF"}, tra ve 2.04 Changed
    Observe -> client dang ky theo doi; server tu gui thong bao khi trang thai THAT SU thay doi
Lenh sai / JSON sai / sai device_id -> 4.00 Bad Request.

Cach chay:
    python light_server_bai3.py                                  # chi light01
    python light_server_bai3.py --devices light01 fan01 pump01   # (mo rong) nhieu thiet bi
"""
import argparse
import asyncio
import json
from datetime import datetime

import aiocoap
import aiocoap.resource as resource
from aiocoap.numbers import ContentFormat

VALID_COMMANDS = ("ON", "OFF")
LOG_FILE = "light_log.txt"


def write_log(line: str):
    """(Mo rong) ghi nhat ky thay doi trang thai ra file."""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {line}\n")


class DeviceStatusResource(resource.ObservableResource):
    """Tai nguyen /iot/lab/<device_id>/status ho tro GET, PUT va Observe."""

    def __init__(self, device_id: str):
        super().__init__()
        self.device_id = device_id
        self.status = "OFF"                       # trang thai ban dau
        self.changed_at = datetime.now()

    def _payload(self) -> bytes:
        data = {"device_id": self.device_id, "status": self.status,
                "timestamp": self.changed_at.isoformat(timespec="seconds")}
        return json.dumps(data, separators=(",", ":")).encode("utf-8")

    async def add_observation(self, request, serverobservation):
        print("New Observe registration received")
        await super().add_observation(request, serverobservation)

    def update_observation_count(self, count):
        print(f"So client dang Observe {self.device_id}: {count}")

    async def render_get(self, request):
        # render_get duoc goi ca khi client GET lan khi server gui thong bao Observe
        return aiocoap.Message(code=aiocoap.CONTENT, payload=self._payload(),
                               content_format=ContentFormat.JSON)

    async def render_put(self, request):
        try:
            data = json.loads(request.payload.decode("utf-8"))
            device_id = data["device_id"]
            command = str(data["command"]).strip().upper()
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError):
            print("PUT request bi tu choi: payload khong phai JSON hop le")
            return aiocoap.Message(code=aiocoap.BAD_REQUEST,
                                   payload=b'Payload phai la JSON {"device_id":..., "command":...}')

        print("PUT request received:")
        print(f"Device: {device_id}")
        print(f"Command: {command}")

        if device_id != self.device_id:
            print(f"  [LOI] device_id '{device_id}' khong khop tai nguyen {self.device_id}\n")
            return aiocoap.Message(code=aiocoap.BAD_REQUEST, payload=b"device_id khong khop")
        if command not in VALID_COMMANDS:
            print(f"  [LOI] Lenh khong hop le: {command} -> tra ve 4.00 Bad Request\n")
            return aiocoap.Message(code=aiocoap.BAD_REQUEST,
                                   payload=b"Lenh khong hop le, chi chap nhan ON hoac OFF")

        if command == self.status:
            print(f"Trang thai khong doi ({self.status}), khong gui thong bao\n")
        else:
            old, self.status = self.status, command
            self.changed_at = datetime.now()
            print(f"Light state changed: {old} -> {self.status}")
            print(f"Notify observers: {self.status}\n")
            write_log(f"{self.device_id}: {old} -> {self.status}")
            self.updated_state()          # gui thong bao toi moi client dang Observe
        return aiocoap.Message(code=aiocoap.CHANGED, payload=self._payload(),
                               content_format=ContentFormat.JSON)


async def main(host: str, port: int, devices):
    root = resource.Site()
    for device_id in devices:
        root.add_resource(["iot", "lab", device_id, "status"], DeviceStatusResource(device_id))
    await aiocoap.Context.create_server_context(root, bind=(host, port))
    print("CoAP Smart Light Server started...")
    for device_id in devices:
        print(f"Resource: /iot/lab/{device_id}/status   (coap://{host}:{port}/iot/lab/{device_id}/status)")
    print()
    await asyncio.get_running_loop().create_future()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smart Light CoAP Server - Bai 3")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5683)
    parser.add_argument("--devices", nargs="+", default=["light01"])
    args = parser.parse_args()
    try:
        asyncio.run(main(args.host, args.port, args.devices))
    except KeyboardInterrupt:
        print("\nServer da dung.")
