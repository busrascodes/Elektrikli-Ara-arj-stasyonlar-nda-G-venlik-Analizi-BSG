# security_tests.py
import json
import os
from datetime import datetime

from security_validation import (
    SecurityConfig,
    TxState,
    validate_start_transaction,
    validate_stop_transaction,
    validate_remote_start_transaction,
)

# MitM dosyandaki manipülatörü test amaçlı kullanıyoruz (proxy çalıştırmıyoruz).
from mitm_attack import manipulate_message

LOG_DIR = "logs"
REPORT_FILE = os.path.join(LOG_DIR, "security_test_report.txt")


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_report(line: str):
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(REPORT_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{now()}] {line}\n")


def assert_test(name: str, condition: bool, detail: str = "") -> bool:
    status = "PASS" if condition else "FAIL"
    msg = f"{status} | {name}" + (f" | {detail}" if detail else "")
    print(msg)
    write_report(msg)
    return condition


def build_call(action: str, payload: dict, unique_id: str = "uid-1") -> str:
    return json.dumps([2, unique_id, action, payload])


def parse_call(message: str):
    data = json.loads(message)
    msg_type, uid, action = data[0], data[1], data[2]
    payload = data[3] if len(data) > 3 else {}
    return msg_type, uid, action, payload


def test_id_tag_manipulation(cfg: SecurityConfig):
    baseline = build_call(
        "StartTransaction",
        {"connector_id": 1, "id_tag": "USER001", "meter_start": 0, "timestamp": "2026-01-17T00:00:00Z"},
        unique_id="uid-start",
    )
    tampered = manipulate_message(baseline)

    _, _, _, base_payload = parse_call(baseline)
    _, _, _, tam_payload = parse_call(tampered)

    ok_base, msg_base = validate_start_transaction(base_payload, cfg)
    ok_tam, msg_tam = validate_start_transaction(tam_payload, cfg)

    assert_test("StartTransaction baseline accepted", ok_base, msg_base)
    assert_test("StartTransaction tampering detected (id_tag)", (not ok_tam), msg_tam)


def test_meter_stop_manipulation(tx_state: TxState):
    tx_id = 12345
    meter_start = 1000
    meter_stop_ok = 1500

    tx_state.set_meter_start(tx_id, meter_start)

    baseline = build_call(
        "StopTransaction",
        {"meter_stop": meter_stop_ok, "timestamp": "2026-01-17T00:00:10Z", "transaction_id": tx_id},
        unique_id="uid-stop",
    )
    tampered = manipulate_message(baseline)

    _, _, _, base_payload = parse_call(baseline)
    _, _, _, tam_payload = parse_call(tampered)

    ok_base, msg_base = validate_stop_transaction(base_payload, tx_state)
    ok_tam, msg_tam = validate_stop_transaction(tam_payload, tx_state)

    assert_test("StopTransaction baseline accepted", ok_base, msg_base)
    assert_test("StopTransaction tampering detected (meter_stop)", (not ok_tam), msg_tam)


def test_max_current_manipulation(cfg: SecurityConfig):
    baseline = build_call(
        "RemoteStartTransaction",
        {"id_tag": "USER001", "charging_profile": {"max_current": 32}},
        unique_id="uid-remote",
    )
    tampered = manipulate_message(baseline)

    _, _, _, base_payload = parse_call(baseline)
    _, _, _, tam_payload = parse_call(tampered)

    ok_base, msg_base = validate_remote_start_transaction(base_payload, cfg)
    ok_tam, msg_tam = validate_remote_start_transaction(tam_payload, cfg)

    assert_test("RemoteStartTransaction baseline accepted", ok_base, msg_base)
    assert_test("RemoteStartTransaction tampering detected (max_current)", (not ok_tam), msg_tam)


def main():
    cfg = SecurityConfig(allowed_id_tags={"USER001"}, max_current_limit=32)
    tx_state = TxState()

    print("=== Security Tests (Offline, PASS/FAIL) ===")
    write_report("=== Security Tests Started ===")

    test_id_tag_manipulation(cfg)
    test_meter_stop_manipulation(tx_state)
    test_max_current_manipulation(cfg)

    write_report("=== Security Tests Finished ===")
    print(f"\nRapor: {REPORT_FILE}")


if __name__ == "__main__":
    main()
