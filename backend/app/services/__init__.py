import json
from math import atan2, cos, radians, sin, sqrt

from sqlalchemy.orm import Session

from app.config import settings
from app.models import CrowdLevel, Procurement, ProcurementStatus, Slot

try:
    import redis

    redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    redis_client.ping()
except Exception:
    class MemoryRedis:
        def __init__(self):
            self.store = {}
            self.lists = {}

        def publish(self, _channel, payload):
            print("[notify]", payload)

        def delete(self, key):
            self.lists.pop(key, None)
            self.store.pop(key, None)

        def rpush(self, key, *values):
            self.lists.setdefault(key, []).extend(values)

        def lrange(self, key, start, end):
            data = self.lists.get(key, [])
            if end == -1:
                end = len(data)
            else:
                end = end + 1
            return data[start:end]

        def set(self, key, value):
            self.store[key] = str(value)

        def get(self, key):
            return self.store.get(key)

    redis_client = MemoryRedis()


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return round(r * 2 * atan2(sqrt(a), sqrt(1 - a)), 1)


def estimate_minutes(base_minutes: int, minutes_per_quintal: float, quantity: float) -> int:
    return max(5, int(round(base_minutes + quantity * minutes_per_quintal)))


def crowd_level(booked: int, capacity: int) -> CrowdLevel:
    if capacity <= 0:
        return CrowdLevel.high
    ratio = booked / capacity
    if ratio < 0.4:
        return CrowdLevel.low
    if ratio < 0.75:
        return CrowdLevel.moderate
    return CrowdLevel.high


def travel_minutes(km: float) -> int:
    return max(5, int(round((km / 30.0) * 60)))


def publish_notification(payload: dict) -> None:
    redis_client.publish(settings.notify_channel, json.dumps(payload))


def queue_key(centre_id: int, slot_date: str) -> str:
    return f"queue:{centre_id}:{slot_date}"


def current_token_key(centre_id: int, slot_date: str) -> str:
    return f"current_token:{centre_id}:{slot_date}"


def rebuild_live_queue(db: Session, centre_id: int, slot_date: str) -> None:
    rows = (
        db.query(Procurement)
        .join(Slot, Procurement.slot_id == Slot.id)
        .filter(
            Procurement.centre_id == centre_id,
            Slot.slot_date == slot_date,
            Procurement.status.in_(
                [
                    ProcurementStatus.slot_assigned,
                    ProcurementStatus.arrived,
                    ProcurementStatus.weighing,
                    ProcurementStatus.quality_check,
                ]
            ),
        )
        .order_by(Procurement.token_number)
        .all()
    )
    key = queue_key(centre_id, slot_date)
    redis_client.delete(key)
    if rows:
        redis_client.rpush(key, *[str(r.id) for r in rows])
    serving = next((r for r in rows if r.status != ProcurementStatus.slot_assigned), None)
    if serving:
        redis_client.set(current_token_key(centre_id, slot_date), serving.token_number)
    elif rows:
        redis_client.set(current_token_key(centre_id, slot_date), rows[0].token_number)
    else:
        redis_client.set(current_token_key(centre_id, slot_date), 0)
