# import .database as database
from marshmallow_sqlalchemy import fields
from sqlalchemy import JSON, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import db, ma


class Stop(db.Model):
    __tablename__ = "stop"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    stop = Column(String, nullable=True)
    alerts = relationship("Alerts", back_populates="stop")


class Alerts(db.Model):
    __tablename__ = "alerts"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    alert_type = Column(String, nullable=True)
    created_at = Column(Integer, nullable=True)
    updated_at = Column(Integer, nullable=True)
    direction = Column(String, nullable=True)
    heading = Column(String, nullable=True)
    dateText = Column(JSON, nullable=True)
    parsedDate = Column(String, nullable=True)
    route = Column(String, nullable=True)
    stop_id = Column(Integer, ForeignKey("stop.id"), nullable=True)
    stop = relationship("Stop", back_populates="alerts")


class ListofAlerts(ma.SQLAlchemyAutoSchema):

    class Meta:

        model = Alerts
        exclude = ("id", "stop_id", "created_at", "updated_at")
        include_relationships = True


class StopSchema(ma.SQLAlchemyAutoSchema):
    alerts = fields.Nested(ListofAlerts, many=True)

    class Meta:
        model = Stop
        exclude = ("id",)
        include_relationships = True
        include_fk = True
