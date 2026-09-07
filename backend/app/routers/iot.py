from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Procurement, ProcurementStatus, StatusEvent
from app.schemas import IotScanIn
from app.services import publish_notification, rebuild_live_queue
from app.routers.procurements import serialize_procurement

router = APIRouter(prefix="/api/iot", tags=["iot"])


@router.post("/scan")
def scan(body: IotScanIn, db: Session = Depends(get_db)):
    p = db.query(Procurement).filter(Procurement.qr_code == body.qr_code.upper()).first()
    if not p:
        raise HTTPException(404, "Unknown QR token")
    if p.centre_id != body.centre_id:
        raise HTTPException(400, "QR belongs to a different centre")
    if p.status == ProcurementStatus.slot_assigned:
        p.status = ProcurementStatus.arrived
        p.arrived_at = datetime.utcnow()
        db.add(StatusEvent(procurement_id=p.id, status=ProcurementStatus.arrived, note=f"Gate scan {body.device_id}"))
        db.commit()
        if p.slot:
            rebuild_live_queue(db, p.centre_id, p.slot.slot_date.isoformat())
        publish_notification(
            {
                "channel": "sms",
                "phone": p.farmer.phone,
                "title": "KISANQ arrival",
                "message": f"Token #{p.token_number} scanned at {p.centre.name}. Please move to weighing bay.",
            }
        )
    db.refresh(p)
    return {"ok": True, "device_id": body.device_id, "procurement": serialize_procurement(p)}
