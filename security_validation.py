# security_validation.py

from dataclasses import dataclass
from typing import Dict, Optional, Set, Tuple, Any


@dataclass
class SecurityConfig:
    allowed_id_tags: Set[str]
    max_current_limit: int = 32  # Amper


class TxState:
    def __init__(self):
        self.meter_start_by_tx: Dict[int, int] = {}

    def set_meter_start(self, transaction_id: int, meter_start: int):
        self.meter_start_by_tx[int(transaction_id)] = int(meter_start)

    def get_meter_start(self, transaction_id: int) -> Optional[int]:
        return self.meter_start_by_tx.get(int(transaction_id))


def validate_start_transaction(payload: Dict[str, Any], cfg: SecurityConfig) -> Tuple[bool, str]:
    id_tag = payload.get("id_tag") or payload.get("idTag")
    if not id_tag:
        return False, "StartTransaction: id_tag missing"
    if id_tag not in cfg.allowed_id_tags:
        return False, f"StartTransaction: id_tag not allowed ({id_tag})"
    return True, "StartTransaction: OK"


def validate_stop_transaction(payload: Dict[str, Any], tx_state: TxState) -> Tuple[bool, str]:
    tx_id = payload.get("transaction_id") or payload.get("transactionId")

    meter_stop = payload.get("meter_stop")
    if meter_stop is None:
        meter_stop = payload.get("meterStop")

    if tx_id is None:
        return False, "StopTransaction: transaction_id missing"
    if meter_stop is None:
        return False, "StopTransaction: meter_stop missing"

    meter_stop = int(meter_stop)
    meter_start = tx_state.get_meter_start(int(tx_id))

    if meter_start is None:
        if meter_stop < 0:
            return False, "StopTransaction: meter_stop negative"
        return True, "StopTransaction: OK (no meter_start known)"

    if meter_stop < meter_start:
        return False, f"StopTransaction: meter_stop decreased ({meter_stop} < {meter_start})"

    return True, "StopTransaction: OK"


def validate_remote_start_transaction(payload: Dict[str, Any], cfg: SecurityConfig) -> Tuple[bool, str]:
    charging_profile = payload.get("charging_profile") or payload.get("chargingProfile") or {}

    max_current = charging_profile.get("max_current")
    if max_current is None:
        max_current = charging_profile.get("maxCurrent")

    if max_current is None:
        return True, "RemoteStartTransaction: OK (no max_current provided)"

    max_current = int(max_current)
    if max_current > cfg.max_current_limit:
        return False, f"RemoteStartTransaction: max_current too high ({max_current}A > {cfg.max_current_limit}A)"

    return True, "RemoteStartTransaction: OK"
