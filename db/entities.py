from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Numeric, Index
from sqlalchemy.orm import relationship

from db.database import Base


# ================ Core ================
class TrafficCam(Base):
    """Represents Arduino devices with a camera to record traffic at a specific latitude/longitude."""
    __tablename__ = "traffic_cams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    location_lat = Column(Numeric(9, 6), nullable=False, comment="Latitude (±90.000000)")
    location_lng = Column(Numeric(9, 6), nullable=False, comment="Longitude (±180.000000)")
    alias = Column(String(255), nullable=False)
    city = Column(String(255), nullable=False)

    subscriptions = relationship("Subscription", back_populates="traffic_cam")
    traffic_records = relationship("TrafficRecord", back_populates="traffic_cam")
    traffic_jam_alerts = relationship("TrafficJamAlert", back_populates="traffic_cam")

    def __repr__(self):
        # unambiguous representation, good for debugging
        return (f"<TrafficCam(id={self.id!r}, alias={self.alias!r}, "
                f"city={self.city!r}, lat={self.location_lat!r}, "
                f"lng={self.location_lng!r})>")


class TrafficRecord(Base):
    """Contains the vehicle count and the average speed over a period of time at a certain location."""
    __tablename__ = "traffic_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    traffic_cam_id = Column(Integer, ForeignKey("traffic_cams.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    vehicle_count = Column(Integer, nullable=False)
    average_speed = Column(Float, nullable=False)  # in km/h

    traffic_cam = relationship("TrafficCam", back_populates="traffic_records")


class TrafficJamAlert(Base):
    """Marks when a traffic jam was detected at a given location at a certain time."""
    __tablename__ = "traffic_jam_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    traffic_cam_id = Column(Integer, ForeignKey("traffic_cams.id"), nullable=False)
    event_time = Column(DateTime, nullable=False)

    traffic_cam = relationship("TrafficCam", back_populates="traffic_jam_alerts")


# ================ Telegram ================
class TelegramBotUser(Base):
    """A user of our Telegram bot."""
    __tablename__ = "bot_users"

    user_id = Column(Integer, primary_key=True)  # Given from Telegram

    subscriptions = relationship("Subscription", back_populates="bot_user")


class Subscription(Base):
    """Links a bot user to a traffic camera for alerts."""
    __tablename__ = "subscriptions"

    user_id = Column(Integer, ForeignKey("bot_users.user_id"), primary_key=True)
    traffic_cam_id = Column(Integer, ForeignKey("traffic_cams.id"), primary_key=True)

    bot_user = relationship("TelegramBotUser", back_populates="subscriptions")
    traffic_cam = relationship("TrafficCam", back_populates="subscriptions")
