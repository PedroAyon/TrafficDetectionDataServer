import random
from datetime import datetime, timedelta

from db.database import SessionLocal, Base, db_engine
from db.entities import (
    TrafficCam,
    TelegramBotUser,
    Subscription,
    TrafficRecord,
    TrafficJamAlert,
)

# ================ Sample Data ================
# (latitude, longitude, alias)
DEVICE_LOCATIONS = [
    (25.676000, -100.310000, "Calle Francia con Aduana", "Tampico"),
    (25.690000, -100.320000, "Avenida 1ro de Mayo enfrente del Tec Madero", "Ciudad Madero"),
    (25.695000, -100.300000, "Calle Juventino Rosas enfrente del Tec Madero Campus 2", "Ciudad Madero"),
]

USER_IDS = [1001, 1002, 1003, 1004, 1005]

def create_tables():
    """
    Creates or updates all tables defined in the entities.
    """
    Base.metadata.create_all(bind=db_engine)
    print("Tables created or updated successfully.")

def populate_traffic_cams(db):
    cams = [
        TrafficCam(location_lat=lat, location_lng=lng, alias=alias, city=city)
        for lat, lng, alias, city in DEVICE_LOCATIONS
    ]
    db.add_all(cams)
    db.commit()
    print(f"Inserted {len(cams)} traffic cameras.")


def populate_bot_users(db):
    users = [TelegramBotUser(user_id=uid) for uid in USER_IDS]
    db.add_all(users)
    db.commit()
    print(f"Inserted {len(users)} bot users.")


def populate_subscriptions(db, count=5):
    cams = db.query(TrafficCam).all()
    users = db.query(TelegramBotUser).all()

    # build all possible (user_id, traffic_cam_id) pairs
    all_pairs = [(u.user_id, cam.id) for u in users for cam in cams]
    # sample without replacement to avoid PK conflicts
    sampled = random.sample(all_pairs, k=min(count, len(all_pairs)))

    subs = [
        Subscription(user_id=uid, traffic_cam_id=cam_id)
        for uid, cam_id in sampled
    ]
    db.add_all(subs)
    db.commit()
    print(f"Inserted {len(subs)} subscriptions.")


def populate_traffic_records(db, count=20):
    cams = db.query(TrafficCam).all()
    now = datetime.utcnow()

    records = []
    for _ in range(count):
        cam = random.choice(cams)
        # pick a random window in the past month
        end_time = now - timedelta(days=random.randint(0, 30))
        start_time = end_time - timedelta(minutes=random.randint(5, 15))
        vehicle_count = random.randint(5, 100)
        avg_speed = round(random.uniform(20.0, 80.0), 2)

        records.append(
            TrafficRecord(
                traffic_cam_id=cam.id,
                start_time=start_time,
                end_time=end_time,
                vehicle_count=vehicle_count,
                average_speed=avg_speed,
            )
        )

    db.add_all(records)
    db.commit()
    print(f"Inserted {len(records)} traffic records.")


def populate_traffic_jam_alerts(db, count=5):
    cams = db.query(TrafficCam).all()
    now = datetime.utcnow()

    events = []
    for _ in range(count):
        cam = random.choice(cams)
        # random alert in last 10 days
        event_time = now - timedelta(days=random.randint(0, 10), hours=random.randint(0, 23))
        events.append(
            TrafficJamAlert(
                traffic_cam_id=cam.id,
                event_time=event_time,
            )
        )

    db.add_all(events)
    db.commit()
    print(f"Inserted {len(events)} traffic‐jam alerts.")


def main():
    db = SessionLocal()
    try:
        create_tables()
        populate_traffic_cams(db)
        populate_bot_users(db)
        populate_subscriptions(db)
        populate_traffic_records(db)
        populate_traffic_jam_alerts(db)
        print("Database successfully populated!")
    except Exception as e:
        db.rollback()
        print(f"Error populating database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
