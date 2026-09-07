from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Centre, Crop
from app.services.recommend import centre_snapshot, recommend_centres
from app.services.slots import ensure_slots_for_date

router = APIRouter(prefix="/api", tags=["centres"])


@router.get("/crops")
def list_crops(db: Session = Depends(get_db)):
    crops = db.query(Crop).order_by(Crop.name).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "name_hi": c.name_hi,
            "base_minutes": c.base_minutes,
            "minutes_per_quintal": c.minutes_per_quintal,
            "season": c.season,
        }
        for c in crops
    ]


@router.get("/centres")
def list_centres(
    slot_date: date = Query(default_factory=date.today),
    lat: float | None = None,
    lng: float | None = None,
    preferred_centre_id: int | None = None,
    db: Session = Depends(get_db),
):
    centres = db.query(Centre).filter(Centre.is_active.is_(True)).all()
    for c in centres:
        ensure_slots_for_date(db, c, slot_date)
    db.commit()
    snaps = [centre_snapshot(db, c, slot_date, lat, lng) for c in centres]
    if preferred_centre_id:
        return {"centres": recommend_centres(snaps, preferred_centre_id), "date": slot_date.isoformat()}
    if lat is not None:
        snaps.sort(key=lambda s: (s["distance_km"] is None, s["distance_km"] or 99, s["estimated_wait_minutes"]))
    return {"centres": snaps, "date": slot_date.isoformat()}
