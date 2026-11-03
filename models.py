"""Domain classes demonstrating abstraction, inheritance, encapsulation and polymorphism."""
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from uuid import uuid4


class User:
    """Base class for every system user."""

    def __init__(self, user_id, name, email, password_hash):
        self.user_id = user_id
        self.name = name
        self.email = email
        self._password_hash = password_hash  # Encapsulated credential data

    def verify_password(self, password_hash):
        return self._password_hash == password_hash

    def public_record(self):
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "password_hash": self._password_hash,
            "role": self.__class__.__name__.lower(),
        }


class Student(User):
    """A student can book equipment and report faults."""

    def __init__(self, user_id, name, email, password_hash, department):
        super().__init__(user_id, name, email, password_hash)
        self.department = department

    def public_record(self):
        record = super().public_record()
        record["department"] = self.department
        return record


class Admin(User):
    """An administrator can manage equipment and maintenance reports."""
    pass


class Equipment(ABC):
    """Abstract base class for lab equipment."""

    def __init__(self, equipment_id, name, lab, condition="Good", available=True):
        self.equipment_id = equipment_id
        self.name = name
        self.lab = lab
        self._condition = condition
        self._available = available

    @property
    def condition(self):
        return self._condition

    @condition.setter
    def condition(self, value):
        allowed = {"Good", "Needs Repair", "Under Maintenance"}
        if value not in allowed:
            raise ValueError(f"Condition must be one of: {', '.join(sorted(allowed))}")
        self._condition = value
        if value != "Good":
            self._available = False

    @property
    def available(self):
        return self._available and self._condition == "Good"

    def set_available(self, value):
        if value and self._condition != "Good":
            raise ValueError("Equipment cannot be made available unless its condition is Good.")
        self._available = bool(value)

    @abstractmethod
    def booking_limit_hours(self):
        """Return the maximum booking duration for this equipment type."""
        raise NotImplementedError

    @abstractmethod
    def category(self):
        raise NotImplementedError

    def to_record(self):
        return {
            "equipment_id": self.equipment_id,
            "name": self.name,
            "lab": self.lab,
            "condition": self._condition,
            "available": self._available,
            "type": self.category(),
        }


class ElectronicsEquipment(Equipment):
    def booking_limit_hours(self):
        return 3

    def category(self):
        return "electronics"


class ComputerEquipment(Equipment):
    def booking_limit_hours(self):
        return 5

    def category(self):
        return "computer"


class MeasurementEquipment(Equipment):
    def booking_limit_hours(self):
        return 2

    def category(self):
        return "measurement"


def equipment_from_record(record):
    """Factory function: recreate the correct subclass from saved JSON data."""
    classes = {
        "electronics": ElectronicsEquipment,
        "computer": ComputerEquipment,
        "measurement": MeasurementEquipment,
    }
    cls = classes.get(record.get("type"), ElectronicsEquipment)
    return cls(
        record["equipment_id"], record["name"], record["lab"],
        record.get("condition", "Good"), record.get("available", True)
    )


class Booking:
    """A booking is composed of a student and an equipment reference."""

    def __init__(self, student_id, equipment_id, start_time=None, duration_hours=1, booking_id=None):
        self.booking_id = booking_id or str(uuid4())[:8].upper()
        self.student_id = student_id
        self.equipment_id = equipment_id
        self.start_time = start_time or datetime.now().isoformat(timespec="minutes")
        self.duration_hours = int(duration_hours)
        self.status = "Active"

    def to_record(self):
        return {
            "booking_id": self.booking_id,
            "student_id": self.student_id,
            "equipment_id": self.equipment_id,
            "start_time": self.start_time,
            "duration_hours": self.duration_hours,
            "status": self.status,
        }

    @classmethod
    def from_record(cls, record):
        booking = cls(
            record["student_id"], record["equipment_id"],
            record.get("start_time"), record.get("duration_hours", 1),
            record.get("booking_id")
        )
        booking.status = record.get("status", "Active")
        return booking


class FaultReport:
    def __init__(self, student_id, equipment_id, description, report_id=None,
                 status="Open", created_at=None, admin_note=""):
        self.report_id = report_id or str(uuid4())[:8].upper()
        self.student_id = student_id
        self.equipment_id = equipment_id
        self.description = description
        self.status = status
        self.created_at = created_at or datetime.now().isoformat(timespec="minutes")
        self.admin_note = admin_note

    def to_record(self):
        return self.__dict__.copy()

    @classmethod
    def from_record(cls, record):
        return cls(
            record["student_id"], record["equipment_id"], record["description"],
            record.get("report_id"), record.get("status", "Open"),
            record.get("created_at"), record.get("admin_note", "")
        )
