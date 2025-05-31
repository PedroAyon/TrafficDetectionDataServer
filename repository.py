import sys
import os
from datetime import datetime
from functools import wraps
from contextlib import contextmanager
from collections import defaultdict, Counter
from math import floor

from sqlalchemy.orm import joinedload

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import desc, extract, Integer, func
from db.database import SessionLocal
from db.entities import TrafficRecord, TrafficCam, TrafficJamAlert
from utils import TrafficStates


@contextmanager
def session_scope():
    """
    Provide a transactional scope around a series of operations.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def handle_exceptions(func):
    """
    Decorator to handle exceptions uniformly and log function names.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Error in {func.__name__}: {e}")
            raise

    return wrapper


def apply_filters(query, cam_id=None, city=None):
    """
    Apply optional camera ID and city filters to a Query.
    """
    if cam_id is not None:
        query = query.filter(TrafficRecord.traffic_cam_id == cam_id)
    if city is not None:
        query = query.join(TrafficCam).filter(TrafficCam.city == city)
    return query


def apply_date_range(query, start_datetime=None, end_datetime=None):
    """
    Apply optional start/end datetime filters to a Query.
    """
    if start_datetime:
        query = query.filter(TrafficRecord.start_time >= start_datetime)
    if end_datetime:
        query = query.filter(TrafficRecord.end_time <= end_datetime)
    return query


def record_to_dict(record):
    """
    Convert a TrafficRecord instance to a dictionary.
    """
    return {
        "traffic_cam_id": record.traffic_cam_id,
        "start_datetime": record.start_time.strftime('%Y-%m-%d %H:%M:%S'),
        "end_datetime": record.end_time.strftime('%Y-%m-%d %H:%M:%S'),
        "vehicle_count": record.vehicle_count,
        "average_speed": record.average_speed
    }


# ========== TELEGRAM ==========

@handle_exceptions
def get_available_cities():
    with session_scope() as session:
        result = session.query(TrafficCam.city).all()
        return [city for (city,) in result]


@handle_exceptions
def get_cams(city=None):
    with session_scope() as session:
        q = session.query(TrafficCam)
        if city:
            q.filter(TrafficCam.city == city)
        return q.all()


@handle_exceptions
def get_traffic_state(traffic_cam_id):
    with session_scope() as session:
        latest = (
            session.query(TrafficRecord)
            .filter(TrafficRecord.traffic_cam_id == traffic_cam_id)
            .order_by(desc(TrafficRecord.end_time))
            .first()
        )
        avg_speed = (
                session.query(func.avg(TrafficRecord.average_speed))
                .filter(TrafficRecord.traffic_cam_id == traffic_cam_id)
                .scalar() or 0
        )
        current_speed = latest.average_speed if latest else 0

        if current_speed >= avg_speed * 1.2:
            return TrafficStates.Low
        if avg_speed * 0.8 <= current_speed <= avg_speed * 1.2:
            return TrafficStates.Regular
        if avg_speed * 0.2 < current_speed < avg_speed * 0.8:
            return TrafficStates.High
        return TrafficStates.Jam


# ========== DASHBOARD ==========


@handle_exceptions
def get_traffic_stats_in_range(start_datetime: datetime, end_datetime: datetime, cam_id: int = None, city: str = None):
    with session_scope() as session:
        query = session.query(
            func.avg(TrafficRecord.average_speed).label('average_speed'),
            func.sum(TrafficRecord.vehicle_count).label('total_vehicle_count')
        )
        query = query.filter(
            TrafficRecord.start_time >= start_datetime,
            TrafficRecord.end_time <= end_datetime
        )
        query = apply_filters(query, cam_id, city)
        return query.first()


@handle_exceptions
def get_peak_hours(start_datetime: datetime, end_datetime: datetime, cam_id: int = None, city: str = None):
    with session_scope() as session:
        base_q = session.query(
            func.date(TrafficRecord.start_time).label("day"),
            extract("hour", TrafficRecord.start_time).cast(Integer).label("hour"),
            func.sum(TrafficRecord.vehicle_count).label("vehicles"),
        )
        base_q = base_q.filter(
            TrafficRecord.start_time >= start_datetime,
            TrafficRecord.end_time <= end_datetime
        )
        base_q = apply_filters(base_q, cam_id, city)
        daily_counts = base_q.group_by("day", "hour").all()

        per_day = defaultdict(list)
        for day, hour, vehicles in daily_counts:
            per_day[day].append((hour, vehicles))

        daily_peaks = []
        for lst in per_day.values():
            max_veh = max(v for (_, v) in lst)
            daily_peaks.extend([{"hour": h, "vehicles": v} for (h, v) in lst if v == max_veh])

        if not daily_peaks:
            return []

        freq = Counter(p["hour"] for p in daily_peaks)
        max_freq = max(freq.values())

        result = []
        for hour, count in freq.items():
            if count == max_freq:
                counts = [p["vehicles"] for p in daily_peaks if p["hour"] == hour]
                avg_veh = sum(counts) / len(counts)
                result.append({
                    "hour": f"{hour:02d}:00 - {hour + 1:02d}:00",
                    "vehicle_count": int(floor(avg_veh))
                })
        return result


@handle_exceptions
def get_speed_based_congestion(traffic_cam_id: int = None, start_datetime: datetime = None,
                               end_datetime: datetime = None,
                               speed_threshold: int = 10, city: str = None):
    with session_scope() as session:
        query = session.query(TrafficRecord)
        if traffic_cam_id is not None:
            query = query.filter(TrafficRecord.traffic_cam_id == traffic_cam_id)
        query = apply_date_range(query, start_datetime, end_datetime)
        if city:
            query = query.join(TrafficCam).filter(TrafficCam.city == city)

        total = query.count()
        if total == 0:
            return {"congestion_percentage": 0, "status": "no data"}

        low_count = query.filter(TrafficRecord.average_speed <= speed_threshold).count()
        perc = (low_count / total) * 100
        return {"congestion_percentage": round(perc, 2), "status": "congested" if perc > 50 else "fluid"}


@handle_exceptions
def get_traffic_records_in_range(start_datetime: datetime,
                                 end_datetime: datetime,
                                 cam_id: int = None,
                                 city: str = None):
    with session_scope() as session:
        query = session.query(TrafficRecord)
        query = query.join(TrafficCam).options(joinedload(TrafficRecord.traffic_cam))
        query = apply_date_range(query, start_datetime, end_datetime)
        query = apply_filters(query, cam_id, city)
        records = query.all()
        result = []
        for rec in records:
            rd = record_to_dict(rec)
            rd['alias'] = rec.traffic_cam.alias
            result.append(rd)

        return result


@handle_exceptions
def get_traffic_jams_in_range(start_datetime: datetime, end_datetime: datetime, cam_id: int = None, city: str = None):
    with session_scope() as session:
        query = session.query(TrafficJamAlert)
        query = query.filter(
            TrafficJamAlert.event_time >= start_datetime,
            TrafficJamAlert.event_time <= end_datetime
        )
        if cam_id is not None:
            query = query.filter(TrafficJamAlert.traffic_cam_id == cam_id)
        if city is not None:
            query = query.join(TrafficCam).filter(TrafficCam.city == city)
        alerts = query.all()
        return [
            {
                "traffic_cam_id": alert.traffic_cam_id,
                "event_time": alert.event_time.strftime('%Y-%m-%d %H:%M:%S')
            }
            for alert in alerts
        ]


# ========== Traffic Detection ==========

@handle_exceptions
def add_traffic_record(device_id: int, start_time: datetime, end_time: datetime, vehicle_count: int,
                       average_speed: float):
    with session_scope() as session:
        record = TrafficRecord(
            traffic_cam_id=device_id,
            start_time=start_time,
            end_time=end_time,
            vehicle_count=vehicle_count,
            average_speed=average_speed
        )
        session.add(record)
        session.flush()  # Ensure record ID is populated
        if get_traffic_state(device_id) == TrafficStates.Jam:
            alert = TrafficJamAlert(traffic_cam_id=device_id, event_time=datetime.now())
            session.add(alert)
        return record
