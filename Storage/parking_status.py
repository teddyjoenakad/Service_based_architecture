from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql.functions import now
from base import Base

class ParkingStatus(Base):
    """ Parking Status """

    __tablename__ = "parking_status"

    id = Column(Integer, primary_key=True)
    meter_id = Column(String, nullable=False)
    device_id = Column(String, nullable=False)
    status = Column(Boolean, nullable=False)
    spot_number = Column(Integer, nullable=False)
    timestamp = Column(String, nullable=False)
    date_created = Column(DateTime, nullable=False)
    trace_id = Column(String, nullable=False)

    def __init__(self, meter_id, device_id, status, spot_number, timestamp, trace_id):
        """ Initializes a parking status update """
        self.meter_id = meter_id
        self.device_id = device_id
        self.status = status
        self.spot_number = spot_number
        self.timestamp = timestamp
        self.date_created = now()  # Sets the date/time record is created
        self.trace_id = trace_id

    def to_dict(self):
        """ Dictionary Representation of a parking status update """
        return {
            'id': self.id,
            'meter_id': self.meter_id,
            'device_id': self.device_id,
            'status': self.status,
            'spot_number': self.spot_number,
            'timestamp': self.timestamp,
            'date_created': self.date_created,
            'trace_id': self.trace_id
        }
