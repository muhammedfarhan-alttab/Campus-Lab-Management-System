"""Application logic and command-line interface."""
import hashlib
import os
from getpass import getpass
from models import (
    Admin, Student, ElectronicsEquipment, ComputerEquipment,
    MeasurementEquipment, equipment_from_record, Booking, FaultReport
)


def hash_password(password, salt=None):
    """Hash a password with a per-user salt (stdlib demonstration, not production auth)."""
    salt = salt or os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                                 bytes.fromhex(salt), 150_000).hex()
    return f"{salt}${digest}"


def check_password(password, stored):
    try:
        salt, _ = stored.split("$", 1)
        return hash_password(password, salt) == stored
    except (ValueError, AttributeError):
        return False


class LabManagementSystem:
    def __init__(self, store):
        self.store = store
        self.users = {}
        self.equipment = {}
        self.bookings = {}
        self.faults = {}
        self._load_data()
        self._seed_data()

    def _load_data(self):
        for row in self.store.load("users"):
            role = row.get("role")
            if role == "admin":
                user = Admin(row["user_id"], row["name"], row["email"], row["password_hash"])
            elif role == "student":
                user = Student(row["user_id"], row["name"], row["email"],
                               row["password_hash"], row.get("department", "General"))
            else:
                continue
            self.users[user.user_id] = user
        self.equipment = {
            row["equipment_id"]: equipment_from_record(row)
            for row in self.store.load("equipment")
        }
        self.bookings = {
            row["booking_id"]: Booking.from_record(row)
            for row in self.store.load("bookings")
        }
        self.faults = {
            row["report_id"]: FaultReport.from_record(row)
            for row in self.store.load("faults")
        }

    def _seed_data(self):
        if not any(isinstance(user, Admin) for user in self.users.values()):
            self.users["ADMIN01"] = Admin(
                "ADMIN01", "Lab Administrator", "admin@campus.local",
                hash_password("Admin@123")
            )
        if not self.equipment:
            samples = [
                ElectronicsEquipment("EQ101", "Digital Oscilloscope", "Electronics Lab"),
                ElectronicsEquipment("EQ102", "Function Generator", "Electronics Lab"),
                ComputerEquipment("EQ103", "Development Workstation", "Computer Lab"),
                MeasurementEquipment("EQ104", "Digital Multimeter", "Basic Electrical Lab"),
            ]
            self.equipment = {item.equipment_id: item for item in samples}
        self._save_all()

    def _save_all(self):
        self.store.save("users", [u.public_record() for u in self.users.values()])
        self.store.save("equipment", [e.to_record() for e in self.equipment.values()])
        self.store.save("bookings", [b.to_record() for b in self.bookings.values()])
        self.store.save("faults", [f.to_record() for f in self.faults.values()])

    def register_student(self, name, email, password, department):
        if not name.strip() or "@" not in email or len(password) < 8:
            raise ValueError("Enter a name, valid email, and password of at least 8 characters.")
        if any(u.email.lower() == email.lower() for u in self.users.values()):
            raise ValueError("An account with that email already exists.")
        user_id = "STU" + str(sum(isinstance(u, Student) for u in self.users.values()) + 1).zfill(3)
        while user_id in self.users:
            user_id += "X"
        self.users[user_id] = Student(user_id, name.strip(), email.strip(),
                                      hash_password(password), department.strip() or "General")
        self._save_all()
        return user_id

    def authenticate(self, email, password, role=None):
        for user in self.users.values():
            actual_role = "admin" if isinstance(user, Admin) else "student"
            if user.email.lower() == email.lower() and check_password(password, user._password_hash):
                if role is None or role == actual_role:
                    return user
        return None

    def list_equipment(self, available_only=False):
        items = list(self.equipment.values())
        if available_only:
            items = [item for item in items if item.available]
        return sorted(items, key=lambda item: item.equipment_id)

    def book_equipment(self, student, equipment_id, duration):
        item = self.equipment.get(equipment_id.upper())
        if item is None:
            raise ValueError("Equipment ID was not found.")
        if not item.available:
            raise ValueError("This equipment is currently unavailable.")
        active = [b for b in self.bookings.values()
                  if b.equipment_id == item.equipment_id and b.status == "Active"]
        if active:
            raise ValueError("This equipment already has an active booking.")
        if duration < 1 or duration > item.booking_limit_hours():
            raise ValueError(f"{item.category().title()} equipment can be booked for 1 to "
                             f"{item.booking_limit_hours()} hours.")
        booking = Booking(student.user_id, item.equipment_id, duration_hours=duration)
        self.bookings[booking.booking_id] = booking
        item.set_available(False)
        self._save_all()
        return booking

    def return_equipment(self, student, booking_id):
        booking = self.bookings.get(booking_id.upper())
        if booking is None or booking.student_id != student.user_id or booking.status != "Active":
            raise ValueError("No active booking with that ID belongs to you.")
        booking.status = "Returned"
        item = self.equipment[booking.equipment_id]
        item.set_available(item.condition == "Good")
        self._save_all()

    def report_fault(self, student, equipment_id, description):
        item = self.equipment.get(equipment_id.upper())
        if item is None:
            raise ValueError("Equipment ID was not found.")
        if len(description.strip()) < 5:
            raise ValueError("Please describe the fault in at least 5 characters.")
        report = FaultReport(student.user_id, item.equipment_id, description.strip())
        self.faults[report.report_id] = report
        item.condition = "Needs Repair"
        # Close active bookings for safety and mark them for admin attention.
        for booking in self.bookings.values():
            if booking.equipment_id == item.equipment_id and booking.status == "Active":
                booking.status = "Cancelled - Fault Reported"
        self._save_all()
        return report

    def add_equipment(self, equipment_id, name, lab, kind):
        equipment_id = equipment_id.strip().upper()
        if not equipment_id or equipment_id in self.equipment or not name.strip() or not lab.strip():
            raise ValueError("Use a unique ID and provide an equipment name and lab.")
        classes = {
            "1": ElectronicsEquipment,
            "2": ComputerEquipment,
            "3": MeasurementEquipment,
        }
        cls = classes.get(kind)
        if cls is None:
            raise ValueError("Choose a valid equipment category.")
        self.equipment[equipment_id] = cls(equipment_id, name.strip(), lab.strip())
        self._save_all()

    def update_fault(self, report_id, status, note):
        report = self.faults.get(report_id.upper())
        if report is None:
            raise ValueError("Fault report was not found.")
        if status not in {"Open", "In Progress", "Resolved"}:
            raise ValueError("Invalid maintenance status.")
        report.status = status
        report.admin_note = note.strip()
        item = self.equipment[report.equipment_id]
        if status == "Resolved":
            # Only mark equipment Good when no other unresolved report exists.
            unresolved = any(f.equipment_id == item.equipment_id and f.status != "Resolved"
                             and f.report_id != report.report_id for f in self.faults.values())
            if not unresolved:
                item.condition = "Good"
                item.set_available(True)
        else:
            item.condition = "Under Maintenance" if status == "In Progress" else "Needs Repair"
        self._save_all()

    def run(self):
        while True:
            print("\n" + "=" * 54)
            print("          CAMPUS LAB MANAGEMENT SYSTEM")
            print("=" * 54)
            print("1. Student registration\n2. Student login\n3. Admin login\n4. View equipment\n5. Exit")
            choice = input("Choose an option: ").strip()
            try:
                if choice == "1":
                    self._register_screen()
                elif choice == "2":
                    self._login_screen("student")
                elif choice == "3":
                    self._login_screen("admin")
                elif choice == "4":
                    self._show_equipment()
                elif choice == "5":
                    print("Thank you. Goodbye!")
                    break
                else:
                    print("Please choose an option from 1 to 5.")
            except (ValueError, OSError) as error:
                print(f"Error: {error}")

    def _register_screen(self):
        print("\n--- Student Registration ---")
        name = input("Full name: ")
        email = input("Email: ")
        password = getpass("Password (minimum 8 characters): ")
        department = input("Department: ")
        user_id = self.register_student(name, email, password, department)
        print(f"Registration successful. Your student ID is {user_id}.")

    def _login_screen(self, role):
        print(f"\n--- {role.title()} Login ---")
        email = input("Email: ")
        password = getpass("Password: ")
        user = self.authenticate(email, password, role)
        if user is None:
            print("Invalid credentials or account type.")
            return
        print(f"Welcome, {user.name}!")
        if isinstance(user, Admin):
            self._admin_menu(user)
        else:
            self._student_menu(user)

    def _show_equipment(self, available_only=False):
        items = self.list_equipment(available_only)
        print("\nID      Equipment                    Lab                       Status")
        print("-" * 78)
        for item in items:
            status = "Available" if item.available else item.condition
            print(f"{item.equipment_id:<7} {item.name:<28} {item.lab:<25} {status}")
        if not items:
            print("No equipment found.")

    def _student_menu(self, student):
        while True:
            print("\n--- STUDENT DASHBOARD ---")
            print("1. View available equipment\n2. Search equipment\n3. Book equipment")
            print("4. Return equipment\n5. Report equipment fault\n6. View my bookings\n7. Logout")
            choice = input("Choose an option: ").strip()
            try:
                if choice == "1":
                    self._show_equipment(available_only=True)
                elif choice == "2":
                    term = input("Enter equipment ID, name, or category: ").lower()
                    found = [e for e in self.list_equipment()
                             if term in e.equipment_id.lower() or term in e.name.lower()
                             or term in e.category().lower()]
                    for e in found:
                        print(f"{e.equipment_id} | {e.name} | {e.category()} | "
                              f"{'Available' if e.available else e.condition}")
                    if not found:
                        print("No matching equipment.")
                elif choice == "3":
                    self._show_equipment(available_only=True)
                    equipment_id = input("Equipment ID: ")
                    duration = int(input("Duration in hours: "))
                    booking = self.book_equipment(student, equipment_id, duration)
                    print(f"Booked successfully. Booking ID: {booking.booking_id}")
                elif choice == "4":
                    booking_id = input("Booking ID: ")
                    self.return_equipment(student, booking_id)
                    print("Equipment returned successfully.")
                elif choice == "5":
                    equipment_id = input("Equipment ID: ")
                    description = input("Describe the fault: ")
                    report = self.report_fault(student, equipment_id, description)
                    print(f"Fault report submitted. Report ID: {report.report_id}")
                elif choice == "6":
                    rows = [b for b in self.bookings.values() if b.student_id == student.user_id]
                    for b in rows:
                        print(f"{b.booking_id} | {b.equipment_id} | {b.status} | "
                              f"{b.duration_hours} hour(s)")
                    if not rows:
                        print("You have no bookings.")
                elif choice == "7":
                    break
                else:
                    print("Invalid choice.")
            except (ValueError, KeyError) as error:
                print(f"Error: {error}")

    def _admin_menu(self, admin):
        while True:
            print("\n--- ADMIN DASHBOARD ---")
            print("1. View all equipment\n2. Add equipment\n3. View fault reports")
            print("4. Update maintenance report\n5. View all bookings\n6. Logout")
            choice = input("Choose an option: ").strip()
            try:
                if choice == "1":
                    self._show_equipment()
                elif choice == "2":
                    equipment_id = input("New equipment ID: ")
                    name = input("Equipment name: ")
                    lab = input("Lab location: ")
                    print("1. Electronics  2. Computer  3. Measurement")
                    kind = input("Category: ")
                    self.add_equipment(equipment_id, name, lab, kind)
                    print("Equipment added.")
                elif choice == "3":
                    for f in self.faults.values():
                        print(f"{f.report_id} | {f.equipment_id} | {f.description} | "
                              f"{f.status} | by {f.student_id}")
                    if not self.faults:
                        print("No fault reports.")
                elif choice == "4":
                    report_id = input("Report ID: ")
                    print("Status: 1. Open  2. In Progress  3. Resolved")
                    status_choice = input("Choose status: ")
                    statuses = {"1": "Open", "2": "In Progress", "3": "Resolved"}
                    if status_choice not in statuses:
                        raise ValueError("Choose 1, 2, or 3.")
                    note = input("Admin note (optional): ")
                    self.update_fault(report_id, statuses[status_choice], note)
                    print("Maintenance report updated.")
                elif choice == "5":
                    for b in self.bookings.values():
                        print(f"{b.booking_id} | {b.student_id} | {b.equipment_id} | "
                              f"{b.status} | {b.duration_hours} hour(s)")
                    if not self.bookings:
                        print("No bookings.")
                elif choice == "6":
                    break
                else:
                    print("Invalid choice.")
            except (ValueError, KeyError) as error:
                print(f"Error: {error}")
