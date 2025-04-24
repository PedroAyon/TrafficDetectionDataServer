import random
from datetime import datetime, timedelta

from db.database import SessionLocal
from db.models import TrafficCam, TelegramBotUser, Subscription, TrafficJamAlert, TrafficRecord

# Sample data
DEVICE_LOCATIONS = ["Calle Francia", "Avenida 1ro de Mayo", "Calle Angela Peralta"]
USER_IDS = [1001, 1002, 1003, 1004, 1005]


def populate_traffic_cams(db):
    devices = [TrafficCam(location=loc, alias=f"Cam_{i + 1}") for i, loc in enumerate(DEVICE_LOCATIONS)]
    db.add_all(devices)
    db.commit()
    print(f"Inserted {len(devices)} traffic cameras.")


def populate_bot_users(db):
    users = [TelegramBotUser(user_id=user_id) for user_id in USER_IDS]
    db.add_all(users)
    db.commit()
    print(f"Inserted {len(users)} bot users.")


def populate_subscriptions(db):
    devices = db.query(TrafficCam).all()
    users = db.query(TelegramBotUser).all()

    subscriptions = [
        Subscription(user_id=random.choice(users).id, device_id=random.choice(devices).id)
        for _ in range(5)  # Creating 5 subscriptions
    ]

    db.add_all(subscriptions)
    db.commit()
    print(f"Inserted {len(subscriptions)} subscriptions.")


def populate_traffic_records(db):
    devices = db.query(TrafficCam).all()
    records = []

    for _ in range(20):  # Creating 20 records
        device = random.choice(devices)
        start_time = datetime.utcnow() - timedelta(days=random.randint(1, 30))
        end_time = start_time + timedelta(minutes=random.randint(5, 15))
        vehicle_count = random.randint(5, 100)
        avg_speed = round(random.uniform(20, 80), 2)

        records.append(TrafficRecord(
            device_id=device.id,
            start_time=start_time,
            end_time=end_time,
            vehicle_count=vehicle_count,
            average_speed=avg_speed
        ))

    db.add_all(records)
    db.commit()
    print(f"Inserted {len(records)} traffic records.")


def populate_critical_events(db):
    devices = db.query(TrafficCam).all()
    events = []

    for _ in range(5):  # Creating 5 critical events
        device = random.choice(devices)
        event_time = datetime.utcnow() - timedelta(days=random.randint(1, 10))

        events.append(TrafficJamAlert(
            device_id=device.id,
            event_time=event_time
        ))

    db.add_all(events)
    db.commit()
    print(f"Inserted {len(events)} critical events.")


def main():
    """Runs all population functions."""
    db = SessionLocal()
    try:
        populate_traffic_cams(db)
        populate_bot_users(db)
        populate_subscriptions(db)
        populate_traffic_records(db)
        populate_critical_events(db)
        print("Database successfully populated!")
    except Exception as e:
        db.rollback()
        print(f"Error populating database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
