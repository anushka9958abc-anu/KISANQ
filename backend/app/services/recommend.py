from datetime import date

from sqlalchemy.orm import Session

from app.models import Centre, HistoricalStat, Slot
from app.services import crowd_level, haversine_km, travel_minutes


def centre_snapshot(db: Session, centre: Centre, slot_date: date, lat: float | None, lng: float | None) -> dict:
    slots = db.query(Slot).filter(Slot.centre_id == centre.id, Slot.slot_date == slot_date).all()
    booked = sum(s.booked_count for s in slots)
    capacity = sum(s.max_farmers for s in slots) or (centre.farmers_per_slot * 18)
    remaining = max(capacity - booked, 0)
    wait = 0
    if slots:
        wait = int(sum(s.reserved_minutes for s in slots) / max(centre.processing_bays, 1))
    hist = (
        db.query(HistoricalStat)
        .filter(HistoricalStat.centre_id == centre.id, HistoricalStat.weekday == slot_date.weekday())
        .first()
    )
    predicted = hist.expected_farmers if hist else booked
    predicted_wait = hist.avg_wait_minutes if hist else wait
    km = None
    if lat is not None and lng is not None:
        km = haversine_km(lat, lng, centre.lat, centre.lng)
    level = crowd_level(max(booked, predicted // 2), capacity)
    return {
        "id": centre.id,
        "code": centre.code,
        "name": centre.name,
        "address": centre.address,
        "district": centre.district,
        "state": centre.state,
        "lat": centre.lat,
        "lng": centre.lng,
        "distance_km": km,
        "travel_minutes": travel_minutes(km) if km is not None else None,
        "booked_farmers": booked,
        "capacity_farmers": capacity,
        "available_slots": remaining,
        "queue_length": booked,
        "estimated_wait_minutes": max(wait, predicted_wait // 3) if booked else predicted_wait // 4,
        "crowd": level.value,
        "predicted_arrivals": predicted,
        "daily_capacity_quintals": centre.daily_capacity_quintals,
        "processing_bays": centre.processing_bays,
        "open_time": centre.open_time.strftime("%H:%M"),
        "close_time": centre.close_time.strftime("%H:%M"),
    }


def recommend_centres(snapshots: list[dict], preferred_id: int) -> list[dict]:
    ranked = []
    for s in snapshots:
        dist = s["distance_km"] if s["distance_km"] is not None else 20
        wait = s["estimated_wait_minutes"]
        crowd_penalty = {"low": 0, "moderate": 25, "high": 70}[s["crowd"]]
        score = wait * 0.55 + travel_minutes(dist) * 0.3 + crowd_penalty * 0.15
        ranked.append({**s, "score": round(score, 2), "is_preferred": s["id"] == preferred_id})
    ranked.sort(key=lambda x: x["score"])
    return ranked
