from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from app.models import Centre, Slot


def iter_slot_windows(centre: Centre):
    start_dt = datetime.combine(date.today(), centre.open_time)
    end_dt = datetime.combine(date.today(), centre.close_time)
    cursor = start_dt
    while cursor < end_dt:
        nxt = cursor + timedelta(minutes=centre.slot_minutes)
        if nxt > end_dt:
            break
        yield cursor.time(), nxt.time()
        cursor = nxt


def ensure_slots_for_date(db: Session, centre: Centre, slot_date: date) -> list[Slot]:
    existing = (
        db.query(Slot)
        .filter(Slot.centre_id == centre.id, Slot.slot_date == slot_date)
        .order_by(Slot.start_time)
        .all()
    )
    if existing:
        return existing
    created = []
    for start, end in iter_slot_windows(centre):
        slot = Slot(
            centre_id=centre.id,
            slot_date=slot_date,
            start_time=start,
            end_time=end,
            max_farmers=centre.farmers_per_slot,
            booked_count=0,
            reserved_minutes=0,
            max_minutes=centre.slot_minutes * centre.processing_bays,
        )
        db.add(slot)
        created.append(slot)
    db.flush()
    return created


def allocate_best_slot(db: Session, centre: Centre, slot_date: date, estimated_minutes: int) -> Slot | None:
    slots = ensure_slots_for_date(db, centre, slot_date)
    now = datetime.now()
    for slot in slots:
        if slot_date == now.date() and slot.end_time <= now.time():
            continue
        if slot.booked_count >= slot.max_farmers:
            continue
        if slot.reserved_minutes + estimated_minutes > slot.max_minutes:
            continue
        return slot
    return None


def slot_score(slot: Slot, estimated_minutes: int) -> float:
    farmer_load = slot.booked_count / max(slot.max_farmers, 1)
    minute_load = slot.reserved_minutes / max(slot.max_minutes, 1)
    leftover = slot.max_minutes - slot.reserved_minutes - estimated_minutes
    return farmer_load * 0.5 + minute_load * 0.4 - leftover * 0.001
