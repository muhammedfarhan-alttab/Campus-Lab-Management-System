import tempfile
import unittest
from pathlib import Path
from storage import DataStore
from system import LabManagementSystem
from models import Student


class LabSystemTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = LabManagementSystem(DataStore(Path(self.temp.name)))

    def tearDown(self):
        self.temp.cleanup()

    def student(self):
        uid = self.app.register_student("Test Student", "test@example.com",
                                        "password123", "CSE")
        return self.app.users[uid]

    def test_seeded_equipment_exists(self):
        self.assertEqual(len(self.app.list_equipment()), 4)

    def test_student_registration_and_authentication(self):
        uid = self.app.register_student("A Student", "a@example.com",
                                        "password123", "ECE")
        user = self.app.authenticate("a@example.com", "password123", "student")
        self.assertEqual(user.user_id, uid)
        self.assertIsInstance(user, Student)

    def test_booking_and_return(self):
        student = self.student()
        booking = self.app.book_equipment(student, "EQ101", 2)
        self.assertFalse(self.app.equipment["EQ101"].available)
        self.app.return_equipment(student, booking.booking_id)
        self.assertTrue(self.app.equipment["EQ101"].available)

    def test_booking_limit_is_enforced(self):
        student = self.student()
        with self.assertRaises(ValueError):
            self.app.book_equipment(student, "EQ101", 4)

    def test_fault_report_blocks_equipment(self):
        student = self.student()
        report = self.app.report_fault(student, "EQ102", "Power button is broken")
        self.assertEqual(report.status, "Open")
        self.assertFalse(self.app.equipment["EQ102"].available)
        self.app.update_fault(report.report_id, "Resolved", "Replaced switch")
        self.assertTrue(self.app.equipment["EQ102"].available)

    def test_data_survives_reload(self):
        self.student()
        reloaded = LabManagementSystem(DataStore(Path(self.temp.name)))
        self.assertTrue(any(u.email == "test@example.com" for u in reloaded.users.values()))


if __name__ == "__main__":
    unittest.main()
