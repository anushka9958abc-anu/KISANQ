from datetime import date

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session, joinedload

from app.auth import get_current_user
from app.database import SessionLocal, get_db
from app.models import Procurement, ProcurementStatus, Slot, User
from app.services import current_token_key, queue_key, rebuild_live_queue, redis_client

router = APIRouter(prefix="/api", tags=["queue"])


def queue_view(db: Session, procurement: Procurement) -> dict:
    if not procurement.slot:
        raise HTTPException(400, "No slot assigned")
    slot_date = procurement.slot.slot_date.isoformat()
    rebuild_live_queue(db, procurement.centre_id, slot_date)
    ids = redis_client.lrange(queue_key(procurement.centre_id, slot_date), 0, -1)
    current = int(redis_client.get(current_token_key(procurement.centre_id, slot_date)) or 0)

    ahead = []
    found = False
    for pid in ids:
        p = db.get(Procurement, int(pid))
        if not p:
            continue
        if p.id == procurement.id:
            found = True
            break
        if p.status in (
            ProcurementStatus.slot_assigned,
            ProcurementStatus.arrived,
            ProcurementStatus.weighing,
            ProcurementStatus.quality_check,
        ):
            ahead.append(p)

    farmers_ahead = len(ahead)
    wait = sum(p.estimated_minutes for p in ahead)
    position = farmers_ahead + 1
    serving = (
        db.query(Procurement)
        .join(Slot)
        .filter(
            Procurement.centre_id == procurement.centre_id,
            Slot.slot_date == procurement.slot.slot_date,
            Procurement.token_number == current,
        )
        .first()
    )
    message = (
        f"You are #{procurement.token_number} — approx. {wait} min remaining."
        if procurement.status
        not in (
            ProcurementStatus.procurement_completed,
            ProcurementStatus.payment_initiated,
            ProcurementStatus.paid,
        )
        else "Procurement completed. Payment is in progress."
    )
    if farmers_ahead <= 5 and farmers_ahead > 0 and procurement.status == ProcurementStatus.slot_assigned:
        message = f"There are {farmers_ahead} farmers ahead of you. Please reach the centre within 20 minutes."

    return {
        "token_number": procurement.token_number,
        "current_token": current,
        "position": position,
        "farmers_ahead": farmers_ahead,
        "estimated_wait_minutes": wait,
        "centre": procurement.centre.name,
        "slot": {
            "date": slot_date,
            "start_time": procurement.slot.start_time.strftime("%H:%M"),
            "end_time": procurement.slot.end_time.strftime("%H:%M"),
        },
        "status": procurement.status.value,
        "message": message,
        "serving_name": serving.farmer.name if serving else None,
        "in_queue": found,
    }


@router.get("/queue/{procurement_id}")
def get_queue(procurement_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    p = (
        db.query(Procurement)
        .options(joinedload(Procurement.slot), joinedload(Procurement.centre), joinedload(Procurement.farmer))
        .filter(Procurement.id == procurement_id)
        .first()
    )
    if not p:
        raise HTTPException(404, "Not found")
    if user.role.value == "farmer" and p.farmer_id != user.id:
        raise HTTPException(403, "Not allowed")
    view = queue_view(db, p)
    if view["farmers_ahead"] == 5 and p.status == ProcurementStatus.slot_assigned:
        from app.services import publish_notification

        publish_notification(
            {
                "channel": "sms",
                "phone": p.farmer.phone,
                "title": "KISANQ queue alert",
                "message": view["message"],
            }
        )
    return view


@router.websocket("/ws/queue/{procurement_id}")
async def ws_queue(websocket: WebSocket, procurement_id: int):
    await websocket.accept()
    try:
        while True:
            db = SessionLocal()
            try:
                p = (
                    db.query(Procurement)
                    .options(
                        joinedload(Procurement.slot),
                        joinedload(Procurement.centre),
                        joinedload(Procurement.farmer),
                    )
                    .filter(Procurement.id == procurement_id)
                    .first()
                )
                if not p:
                    await websocket.send_json({"error": "not found"})
                    break
                await websocket.send_json(queue_view(db, p))
            finally:
                db.close()
            await websocket.receive_text()
    except WebSocketDisconnect:
        return
