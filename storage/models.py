from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy import Integer, String, DateTime, func, BigInteger


class Base(DeclarativeBase):
    pass


class TemperatureReport(Base):
    __tablename__ = "temperature_report"
    id = mapped_column(Integer, primary_key=True)
    device_id = mapped_column(String(50), nullable=False)
    temperature = mapped_column(Integer, nullable=False)
    location = mapped_column(String(50), nullable=False)
    timestamp = mapped_column(DateTime, nullable=False)
    date_created = mapped_column(DateTime, nullable=False, default=func.now())
    trace_id = mapped_column(BigInteger, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "temperature": self.temperature,
            "location": self.location,
            "timestamp": self.timestamp.isoformat(),
            "date_created": self.date_created.isoformat(),
            "trace_id": self.trace_id
        }


class HumidityReport(Base):
    __tablename__ = "humidity_report"
    id = mapped_column(Integer, primary_key=True)
    device_id = mapped_column(String(50), nullable=False)
    humidity = mapped_column(Integer, nullable=False)
    location = mapped_column(String(50), nullable=False)
    timestamp = mapped_column(DateTime, nullable=False)
    date_created = mapped_column(DateTime, nullable=False, default=func.now())
    trace_id = mapped_column(BigInteger, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "humidity": self.humidity,
            "location": self.location,
            "timestamp": self.timestamp.isoformat(),
            "date_created": self.date_created.isoformat(),
            "trace_id": self.trace_id
        }
