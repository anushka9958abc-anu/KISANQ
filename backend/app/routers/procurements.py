from datetime import date, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import (
    STATUS_FLOW,
    Centre,
    Crop,
    Procurement,
    ProcurementStatus,
    Slot,
    StatusEvent,
    User,
    UserRole,
)
from app.schemas import BookSlotIn, TimeEstimateIn
from app.services import estimate_minutes, publish_notification, rebuild_live_queue
from app.services.recommend import centre_snapshot, recommend_centres
from app.services.slots import allocate_best_slot, ensure_slots_for_date

router = APIRouter(prefix="/api", tags=["procurements"])


def serialize_procurement(p: Procurement, extra: dict | None = None) -> dict:
    data = {
        "id": p.id,
        "token_number": p.token_number,
        "status": p.status.value,
        "quantity_quintals": p.quantity_quintals,
        "estimated_minutes": p.estimated_minutes,
        "qr_code": p.qr_code,
        "created_at": p.created_at.isoformat(),
        "crop": {"id": p.crop.id, "name": p.crop.name, "name_hi": p.crop.name_hi},
        "centre": {
            "id": p.centre.id,
            "name": p.centre.name,
            "code": p.centre.code,
            "address": p.centre.address,
            "lat": p.centre.lat,
            "lng": p.centre.lng,
        },
        "slot": None,
        "timeline": [
            {"status": e.status.value, "note": e.note, "at": e.created_at.isoformat()} for e in p.events
        ],
        "status_flow": [s.value for s in STATUS_FLOW],
    }
    if p.slot:
        data["slot"] = {
            "id": p.slot.id,
            "date": p.slot.slot_date.isoformat(),
            "start_time": p.slot.start_time.strftime("%H:%M"),
            "end_time": p.slot.end_time.strftime("%H:%M"),
        }
    if extra:
        data.update(extra)
    return data


@router.post("/estimate-time")
def estimate_time(body: TimeEstimateIn, db: Session = Depends(get_db)):
    crop = db.get(Crop, body.crop_id)
    if not crop:
        raise HTTPException(404, "Crop not found")
    minutes = estimate_minutes(crop.base_minutes, crop.minutes_per_quintal, body.quantity_quintals)
    return {
        "crop": crop.name,
        "quantity_quintals": body.quantity_quintals,
        "estimated_minutes": minutes,
        "message": f"About {minutes} minutes at the weighing bay for {body.quantity_quintals} quintals of {crop.name}.",
    }


@router.post("/slots/book")
def book_slot(body: BookSlotIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    crop = db.get(Crop, body.crop_id)
    preferred = db.get(Centre, body.preferred_centre_id)
    if not crop or not preferred:
        raise HTTPException(404, "Crop or centre not found")

    minutes = estimate_minutes(crop.base_minutes, crop.minutes_per_quintal, body.quantity_quintals)
    lat = body.lat if body.lat is not None else user.lat
    lng = body.lng if body.lng is not None else user.lng

    centres = db.query(Centre).filter(Centre.is_active.is_(True)).all()
    for c in centres:
        ensure_slots_for_date(db, c, body.preferred_date)
    db.flush()

    snapshots = [centre_snapshot(db, c, body.preferred_date, lat, lng) for c in centres]
    ranked = recommend_centres(snapshots, preferred.id)

    assigned_centre = preferred
    slot = allocate_best_slot(db, preferred, body.preferred_date, minutes)
    used_recommendation = False
    preferred_wait = next((s["estimated_wait_minutes"] for s in ranked if s["id"] == preferred.id), 90)
    best_alt = next((s for s in ranked if s["id"] != preferred.id), None)

    if slot is None or (best_alt and preferred_wait >= 90 and best_alt["estimated_wait_minutes"] + 20 < preferred_wait):
        if best_alt:
            alt_centre = db.get(Centre, best_alt["id"])
            alt_slot = allocate_best_slot(db, alt_centre, body.preferred_date, minutes)
            if alt_slot is not None:
                assigned_centre = alt_centre
                slot = alt_slot
                used_recommendation = assigned_centre.id != preferred.id

    if slot is None:
        raise HTTPException(409, "No available slots for this date. Try another centre or date.")

    max_token = (
        db.query(func.max(Procurement.token_number))
        .join(Slot, Procurement.slot_id == Slot.id)
        .filter(Procurement.centre_id == assigned_centre.id, Slot.slot_date == body.preferred_date)
        .scalar()
    ) or 0

    procurement = Procurement(
        token_number=max_token + 1,
        farmer_id=user.id,
        centre_id=assigned_centre.id,
        crop_id=crop.id,
        slot_id=slot.id,
        quantity_quintals=body.quantity_quintals,
        estimated_minutes=minutes,
        status=ProcurementStatus.slot_assigned,
        qr_code=uuid4().hex[:12].upper(),
    )
    slot.booked_count += 1
    slot.reserved_minutes += minutes
    db.add(procurement)
    db.flush()
    db.add(
        StatusEvent(
            procurement_id=procurement.id,
            status=ProcurementStatus.registered,
            note="Farmer registered crop quantity",
        )
    )
    db.add(
        StatusEvent(
            procurement_id=procurement.id,
            status=ProcurementStatus.slot_assigned,
            note=f"Slot {slot.start_time.strftime('%H:%M')} at {assigned_centre.name}",
        )
    )
    db.commit()
    db.refresh(procurement)
    rebuild_live_queue(db, assigned_centre.id, body.preferred_date.isoformat())

    publish_notification(
        {
            "channel": "sms",
            "phone": user.phone,
            "title": "KISANQ slot confirmed",
            "message": (
                f"Your procurement slot is {body.preferred_date.isoformat()} at "
                f"{slot.start_time.strftime('%I:%M %p')} at {assigned_centre.name}. Token #{procurement.token_number}."
            ),
        }
    )
    publish_notification(
        {
            "channel": "whatsapp",
            "phone": user.phone,
            "title": "KISANQ slot confirmed",
            "message": (
                f"Namaste {user.name}, your {crop.name} procurement is booked at {assigned_centre.name} "
                f"on {body.preferred_date.isoformat()} {slot.start_time.strftime('%I:%M %p')}. Token #{procurement.token_number}."
            ),
        }
    )

    preferred_snap = next(s for s in ranked if s["id"] == preferred.id)
    assigned_snap = next(s for s in ranked if s["id"] == assigned_centre.id)
    recommendation_text = None
    if used_recommendation:
        recommendation_text = (
            f"{assigned_centre.name} is {assigned_snap['distance_km']} km away but has an estimated "
            f"{assigned_snap['estimated_wait_minutes']}-minute wait vs {preferred_snap['estimated_wait_minutes']} minutes at {preferred.name}."
        )

    return {
        "procurement": serialize_procurement(procurement),
        "assigned_to_preferred": assigned_centre.id == preferred.id,
        "recommendation": recommendation_text,
        "alternatives": ranked[:4],
        "time_estimate": minutes,
    }


@router.get("/procurements/mine")
def my_procurements(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = (
        db.query(Procurement)
        .filter(Procurement.farmer_id == user.id)
        .order_by(Procurement.created_at.desc())
        .all()
    )
    return [serialize_procurement(p) for p in rows]


@router.get("/procurements/{procurement_id}")
def get_procurement(procurement_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    p = db.get(Procurement, procurement_id)
    if not p:
        raise HTTPException(404, "Not found")
    if user.role == UserRole.farmer and p.farmer_id != user.id:
        raise HTTPException(403, "Not allowed")
    return serialize_procurement(p)
