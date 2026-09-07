from datetime import date, datetime, timedelta
from uuid import uuid4

from sqlalchemy import text

from app.auth import hash_password
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import (
    Centre,
    Crop,
    HistoricalStat,
    Procurement,
    ProcurementStatus,
    Slot,
    StatusEvent,
    User,
    UserRole,
)
from app.services import rebuild_live_queue
from app.services.slots import ensure_slots_for_date

CENTRES = [
    ("KNL-A", "Karnal Anaj Mandi A", "Old Grain Market, Karnal", "Karnal", 29.6857, 76.9905, 2400, 8, 5),
    ("KNL-B", "Karnal Anaj Mandi B", "New Grain Market, Karnal", "Karnal", 29.7012, 76.9780, 1800, 7, 4),
    ("KKR-1", "Kurukshetra Procurement Centre", "Pipli Road, Kurukshetra", "Kurukshetra", 29.9695, 76.8783, 2200, 8, 4),
    ("PNP-1", "Panipat Procurement Yard", "GT Road, Panipat", "Panipat", 29.3909, 76.9635, 2000, 8, 4),
    ("KTL-1", "Kaithal Mandi", "Ambala Road, Kaithal", "Kaithal", 29.8015, 76.3998, 1600, 6, 3),
    ("AMB-1", "Ambala Grain Centre", "Baldev Nagar, Ambala", "Ambala", 30.3782, 76.7767, 1900, 7, 4),
    ("YNR-1", "Yamunanagar Centre", "Jagadhri Road, Yamunanagar", "Yamunanagar", 30.1290, 77.2674, 1500, 6, 3),
    ("JND-1", "Jind Procurement Centre", "Patiala Chowk, Jind", "Jind", 29.3162, 76.3051, 1700, 6, 3),
]

CROPS = [
    ("Wheat", "गेहूँ", 8, 0.55, "rabi"),
    ("Paddy", "धान", 10, 0.7, "kharif"),
    ("Mustard", "सरसों", 7, 0.5, "rabi"),
    ("Bajra", "बाजरा", 6, 0.45, "kharif"),
    ("Maize", "मक्का", 9, 0.6, "kharif"),
]


def seed():
    db = SessionLocal()
    try:
        if settings.database_url.startswith("postgresql"):
            db.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            db.commit()
    except Exception:
        db.rollback()
    Base.metadata.create_all(bind=engine)

    if db.query(User).first():
        db.close()
        return

    admin = User(
        name="Procurement Admin",
        phone="9990001111",
        email="admin@kisanq.gov",
        password_hash=hash_password("admin123"),
        role=UserRole.admin,
        district="Karnal",
        lat=29.6857,
        lng=76.9905,
    )
    officer = User(
        name="Centre Officer",
        phone="9990002222",
        email="officer@kisanq.gov",
        password_hash=hash_password("officer123"),
        role=UserRole.officer,
        district="Karnal",
        lat=29.6857,
        lng=76.9905,
    )
    farmer = User(
        name="Ramesh Kumar",
        phone="9876543210",
        password_hash=hash_password("farmer123"),
        role=UserRole.farmer,
        village="Kunjpura",
        district="Karnal",
        lat=29.7100,
        lng=77.0100,
    )
    db.add_all([admin, officer, farmer])

    extra_farmers = []
    for i in range(1, 22):
        extra_farmers.append(
            User(
                name=f"Farmer {i}",
                phone=f"98000000{i:02d}",
                password_hash=hash_password("farmer123"),
                role=UserRole.farmer,
                village="Sample",
                district="Karnal",
                lat=29.68 + i * 0.01,
                lng=76.99 + i * 0.008,
            )
        )
    db.add_all(extra_farmers)

    crops = [
        Crop(name=n, name_hi=h, base_minutes=b, minutes_per_quintal=m, season=s) for n, h, b, m, s in CROPS
    ]
    db.add_all(crops)

    centres = []
    for code, name, addr, dist, lat, lng, cap, fps, bays in CENTRES:
        centres.append(
            Centre(
                code=code,
                name=name,
                address=addr,
                district=dist,
                state="Haryana",
                lat=lat,
                lng=lng,
                daily_capacity_quintals=cap,
                farmers_per_slot=fps,
                processing_bays=bays,
            )
        )
    db.add_all(centres)
    db.flush()

    weekday_load = [0.72, 0.85, 0.9, 1.0, 0.95, 0.55, 0.4]
    for c in centres:
        for wd, load in enumerate(weekday_load):
            db.add(
                HistoricalStat(
                    centre_id=c.id,
                    weekday=wd,
                    expected_farmers=int(c.farmers_per_slot * 16 * load),
                    expected_quintals=int(c.daily_capacity_quintals * load),
                    avg_wait_minutes=int(18 + load * 50),
                )
            )

    today = date.today()
    wheat = crops[0]
    for c in centres:
        ensure_slots_for_date(db, c, today)
    db.flush()

    knl_a = centres[0]
    slots = (
        db.query(Slot)
        .filter(Slot.centre_id == knl_a.id, Slot.slot_date == today)
        .order_by(Slot.start_time)
        .all()
    )
    statuses = [
        ProcurementStatus.slot_assigned,
        ProcurementStatus.arrived,
        ProcurementStatus.weighing,
        ProcurementStatus.quality_check,
        ProcurementStatus.procurement_completed,
        ProcurementStatus.payment_initiated,
        ProcurementStatus.paid,
    ]
    all_farmers = extra_farmers
    token = 1
    for i, f in enumerate(all_farmers):
        slot = slots[min(i // knl_a.farmers_per_slot, len(slots) - 1)]
        qty = 12 + (i % 9) * 4
        minutes = int(round(8 + qty * 0.55))
        st = statuses[i % len(statuses)] if i < 14 else ProcurementStatus.slot_assigned
        p = Procurement(
            token_number=token,
            farmer_id=f.id,
            centre_id=knl_a.id,
            crop_id=wheat.id,
            slot_id=slot.id,
            quantity_quintals=qty,
            estimated_minutes=minutes,
            status=st,
            qr_code=uuid4().hex[:12].upper(),
            created_at=datetime.utcnow() - timedelta(hours=2, minutes=i),
        )
        slot.booked_count += 1
        slot.reserved_minutes += minutes
        db.add(p)
        db.flush()
        db.add(StatusEvent(procurement_id=p.id, status=ProcurementStatus.registered, note="Seeded"))
        db.add(StatusEvent(procurement_id=p.id, status=ProcurementStatus.slot_assigned, note="Auto slot"))
        token += 1

    paddy = crops[1]
    kkr = centres[2]
    kkr_slots = db.query(Slot).filter(Slot.centre_id == kkr.id, Slot.slot_date == today).all()
    if kkr_slots:
        p = Procurement(
            token_number=1,
            farmer_id=farmer.id,
            centre_id=kkr.id,
            crop_id=paddy.id,
            slot_id=kkr_slots[4],
            quantity_quintals=28,
            estimated_minutes=int(round(10 + 28 * 0.7)),
            status=ProcurementStatus.slot_assigned,
            qr_code="DEMOQRKISANQ",
        )
        kkr_slots[4].booked_count += 1
        kkr_slots[4].reserved_minutes += p.estimated_minutes
        db.add(p)
        db.flush()
        db.add(StatusEvent(procurement_id=p.id, status=ProcurementStatus.registered, note="Farmer registered"))
        db.add(StatusEvent(procurement_id=p.id, status=ProcurementStatus.slot_assigned, note="Demo slot"))

    db.commit()
    try:
        rebuild_live_queue(db, knl_a.id, today.isoformat())
        rebuild_live_queue(db, kkr.id, today.isoformat())
    except Exception as exc:
        print("queue rebuild skipped:", exc)
    db.close()
    print("KISANQ seed complete")


if __name__ == "__main__":
    seed()
