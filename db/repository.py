from datetime import datetime
from sqlalchemy import func
from db.database import db_engine, Base, SessionLocal
from db.models import (
    TrafficRecord,
    TrafficCam,
    TrafficJamAlert
)


def create_tables():
    """
    Creates or updates all tables defined in the models.
    """
    Base.metadata.create_all(bind=db_engine)
    print("Tables created or updated successfully.")


def add_traffic_record(device_id: int, start_time: datetime, end_time: datetime, vehicle_count: int,
                       average_speed: float):
    """
    Inserts a new traffic record into the database.
    """
    db = SessionLocal()
    try:
        new_record = TrafficRecord(
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
            vehicle_count=vehicle_count,
            average_speed=average_speed
        )
        db.add(new_record)
        db.commit()
        print("Traffic record added successfully.")
        return new_record
    except Exception as e:
        db.rollback()
        print(f"Error adding traffic record: {e}")
        raise e
    finally:
        db.close()


def get_traffic_history(device_id: int = None, start_date: datetime = None, end_date: datetime = None):
    """
    Retrieves traffic history.
    - If device_id is provided, returns records for that specific device.
    - Otherwise, returns all traffic records.
    Optionally filters by a date range if both start_date and end_date are provided.
    """
    db = SessionLocal()
    try:
        query = db.query(TrafficRecord)
        if device_id is not None:
            query = query.filter(TrafficRecord.traffic_cam_id == device_id)
        if start_date and end_date:
            query = query.filter(TrafficRecord.start_time.between(start_date, end_date))
        records = query.all()
        return records
    except Exception as e:
        print(f"Error retrieving traffic history: {e}")
        raise e
    finally:
        db.close()


def get_device_list():
    """
    Retrieves a list of traffic cam devices with their IDs, locations, and aliases.
    """
    db = SessionLocal()
    try:
        devices = db.query(TrafficCam.id, TrafficCam.location, TrafficCam.alias).all()
        return devices
    except Exception as e:
        print(f"Error retrieving device list: {e}")
        raise e
    finally:
        db.close()


def get_critical_events(device_id: int):
    """
    Retrieves critical events for a specific device.
    """
    db = SessionLocal()
    try:
        events = db.query(TrafficJamAlert).filter(TrafficJamAlert.traffic_cam_id == device_id).all()
        return events
    except Exception as e:
        print(f"Error retrieving critical events: {e}")
        raise e
    finally:
        db.close()


def get_critical_events_since(since_datetime: datetime):
    """
    Retrieves critical events that occurred on or after the specified datetime.
    """
    db = SessionLocal()
    try:
        events = db.query(TrafficJamAlert).filter(TrafficJamAlert.event_time >= since_datetime).all()
        return events
    except Exception as e:
        print(f"Error retrieving critical events since {since_datetime}: {e}")
        raise e
    finally:
        db.close()


def update_traffic_record(record_id: int, vehicle_count: int, average_speed: float):
    """
    Updates an existing traffic record with a new vehicle count and average speed.
    """
    db = SessionLocal()
    try:
        record = db.query(TrafficRecord).filter(TrafficRecord.id == record_id).first()
        if record:
            record.vehicle_count = vehicle_count
            record.average_speed = average_speed
            db.commit()
            print("Traffic record updated successfully.")
            return record
        else:
            raise Exception("Traffic record not found.")
    except Exception as e:
        db.rollback()
        print(f"Error updating traffic record: {e}")
        raise e
    finally:
        db.close()


def delete_traffic_record(record_id: int):
    """
    Deletes a traffic record from the database.
    """
    db = SessionLocal()
    try:
        record = db.query(TrafficRecord).filter(TrafficRecord.id == record_id).first()
        if record:
            db.delete(record)
            db.commit()
            print("Traffic record deleted successfully.")
        else:
            raise Exception("Traffic record not found.")
    except Exception as e:
        db.rollback()
        print(f"Error deleting traffic record: {e}")
        raise e
    finally:
        db.close()


def get_total_traffic_volume(device_id: int = None, start_date: datetime = None, end_date: datetime = None):
    """
    Retrieves the total traffic volume (sum of vehicle_count).
    Optionally filters by device_id and by a date range (start_date and end_date).
    """
    db = SessionLocal()
    try:
        query = db.query(func.sum(TrafficRecord.vehicle_count))
        if device_id is not None:
            query = query.filter(TrafficRecord.traffic_cam_id == device_id)
        if start_date and end_date:
            query = query.filter(TrafficRecord.start_time.between(start_date, end_date))
        total_volume = query.scalar()
        return total_volume or 0  # Return 0 if total_volume is None
    except Exception as e:
        print(f"Error retrieving total traffic volume: {e}")
        raise e
    finally:
        db.close()
