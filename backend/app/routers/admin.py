from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.auth import require_roles
from app.database import get_db
from app.models import (
    STATUS_FLOW,
    Centre,
    HistoricalStat,
    Procurement,
    ProcurementStatus,
    Slot,
    StatusEvent,
    User,
    UserRole,
)
from app.schemas import StatusAdvanceIn
from app.services import publish_notification, rebuild_live_queue
from app.routers.procurements import serialize_procurement

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/dashboard")
def dashboard(
    centre_id: int | None = None,
    slot_date: date = Query(default_factory=date.today),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin, UserRole.officer)),
):
    q = (
        db.query(Procurement)
        .join(Slot, Procurement.slot_id == Slot.id)
        .filter(Slot.slot_date == slot_date)
    )
    if centre_id:
        q = q.filter(Procurement.centre_id == centre_id)
    rows = q.options(joinedload(Procurement.farmer), joinedload(Procurement.crop), joinedload(Procurement.centre), joinedload(Procurement.slot)).all()

    active = [
        p
        for p in rows
        if p.status
        in (
            ProcurementStatus.slot_assigned,
            ProcurementStatus.arrived,
            ProcurementStatus.weighing,
            ProcurementStatus.quality_check,
        )
    ]
    completed = [p for p in rows if p.status in (ProcurementStatus.procurement_completed, ProcurementStatus.payment_initiated, ProcurementStatus.paid)]
    pending = [p for p in rows if p.status not in (ProcurementStatus.paid,)]
    times = [p.estimated_minutes for p in rows]
    avg = int(sum(times) / len(times)) if times else 0
    centres = db.query(Centre).filter(Centre.is_active.is_(True)).all()
    centre_capacity = sum(c.daily_capacity_quintals for c in centres if not centre_id or c.id == centre_id)
    volume = sum(p.quantity_quintals for p in rows)

    return {
        "date": slot_date.isoformat(),
        "todays_farmers": len(rows),
        "queue_length": len(active),
        "pending_procurements": len(pending),
        "completed_procurements": len(completed),
        "average_processing_time": avg,
        "centre_capacity_quintals": centre_capacity,
        "expected_crop_volume": volume,
        "utilization": round(min(100, (volume / centre_capacity) * 100), 1) if centre_capacity else 0,
        "farmers": [
            {**serialize_procurement(p), "farmer_name": p.farmer.name, "farmer_phone": p.farmer.phone}
            for p in rows
        ],
    }


@router.post("/procurements/{procurement_id}/advance")
def advance(
    procurement_id: int,
    body: StatusAdvanceIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin, UserRole.officer)),
):
    p = db.get(Procurement, procurement_id)
    if not p:
        raise HTTPException(404, "Not found")
    idx = STATUS_FLOW.index(p.status)
    if idx >= len(STATUS_FLOW) - 1:
        raise HTTPException(400, "Already paid")
    nxt = STATUS_FLOW[idx + 1]
    p.status = nxt
    if nxt == ProcurementStatus.arrived:
        p.arrived_at = datetime.utcnow()
    if nxt in (ProcurementStatus.procurement_completed, ProcurementStatus.paid):
        p.completed_at = datetime.utcnow()
    db.add(StatusEvent(procurement_id=p.id, status=nxt, note=body.note))
    db.commit()
    if p.slot:
        rebuild_live_queue(db, p.centre_id, p.slot.slot_date.isoformat())
    if nxt == ProcurementStatus.arrived:
        publish_notification(
            {
                "channel": "sms",
                "phone": p.farmer.phone,
                "title": "KISANQ check-in",
                "message": f"Token #{p.token_number} checked in at {p.centre.name}. Please proceed to weighing.",
            }
        )
    if nxt == ProcurementStatus.paid:
        publish_notification(
            {
                "channel": "whatsapp",
                "phone": p.farmer.phone,
                "title": "KISANQ payment",
                "message": f"Payment initiated/completed for token #{p.token_number}. {p.quantity_quintals} quintals of {p.crop.name}.",
            }
        )
    db.refresh(p)
    return serialize_procurement(p)


@router.get("/analytics")
def analytics(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin, UserRole.officer)),
):
    centres = db.query(Centre).filter(Centre.is_active.is_(True)).all()
    weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    by_day = []
    for wd in range(7):
        stats = db.query(HistoricalStat).filter(HistoricalStat.weekday == wd).all()
        by_day.append(
            {
                "weekday": weekday_names[wd],
                "expected_farmers": sum(s.expected_farmers for s in stats),
                "expected_quintals": sum(s.expected_quintals for s in stats),
                "avg_wait_minutes": int(sum(s.avg_wait_minutes for s in stats) / len(stats)) if stats else 0,
            }
        )
    busiest = max(by_day, key=lambda d: d["expected_farmers"])
    centre_util = []
    today = date.today()
    for c in centres:
        booked = (
            db.query(func.coalesce(func.sum(Slot.booked_count), 0))
            .filter(Slot.centre_id == c.id, Slot.slot_date == today)
            .scalar()
        )
        cap = (
            db.query(func.coalesce(func.sum(Slot.max_farmers), 0))
            .filter(Slot.centre_id == c.id, Slot.slot_date == today)
            .scalar()
        )
        centre_util.append(
            {
                "centre": c.name,
                "code": c.code,
                "booked": int(booked or 0),
                "capacity": int(cap or 0),
                "utilization": round(((booked or 0) / cap) * 100, 1) if cap else 0,
            }
        )
    return {
        "by_weekday": by_day,
        "busiest_day": busiest["weekday"],
        "centre_utilization": centre_util,
        "expected_arrivals_today": next(d["expected_farmers"] for d in by_day if d["weekday"] == weekday_names[today.weekday()]),
        "expected_volume_today": next(d["expected_quintals"] for d in by_day if d["weekday"] == weekday_names[today.weekday()]),
    }
