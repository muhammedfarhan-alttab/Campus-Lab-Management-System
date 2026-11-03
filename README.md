# Campus Lab Equipment Booking & Fault Reporting System

A menu-driven Python OOP application for managing university laboratory equipment. Students can search, book and return equipment, and report faults. Administrators can add equipment and track maintenance.

## Features
- Student registration and login; separate administrator login
- Equipment catalogue with category-specific booking limits
- Booking, return, and booking-history features
- Fault reporting automatically takes affected equipment out of service
- Admin maintenance workflow: Open → In Progress → Resolved
- JSON persistence: data remains after the program closes
- Passwords are stored as salted PBKDF2-HMAC-SHA256 hashes
- Input validation and exception handling

## Requirements
- Python 3.9 or newer
- No third-party packages

## Run
Open a terminal in this folder and execute:

```bash
python main.py
```

On Windows, if `python` is not recognized, try `py main.py`.

## First administrator login
- Email: `admin@campus.local`
- Password: `Admin@123`

**Change this demonstration password before using the application for real data.** This is a classroom project, not a production authentication system. The default admin account is created automatically in a fresh data folder.

## Booking limits
| Equipment category | Maximum booking |
|---|---:|
| Electronics | 3 hours |
| Computer | 5 hours |
| Measurement | 2 hours |

## OOP concepts demonstrated
1. **Classes and objects:** `Student`, `Admin`, `Booking`, `FaultReport`, and equipment objects.
2. **Inheritance:** `Student` and `Admin` inherit from `User`; equipment categories inherit from `Equipment`.
3. **Encapsulation:** equipment availability and condition are managed through properties and methods.
4. **Abstraction:** `Equipment` is an abstract base class with abstract methods.
5. **Polymorphism:** each equipment subclass supplies its own booking limit and category.
6. **Composition:** bookings connect a student ID with an equipment ID.

## Project structure
```text
Campus-Lab-Management-System/
├── main.py
├── system.py
├── models.py
├── storage.py
├── test_system.py
├── bookings.json
├── equipment.json
├── faults.json
├── README.md
└── requirements.txt
```

## Data files
The application creates the `data/` folder and JSON files automatically. To reset the sample data, close the program and delete the JSON files in `data/`; the next run recreates the administrator and sample equipment.

## Suggested demo for evaluation
1. Log in as admin and show the four sample equipment items.
2. Register a student and log in.
3. Book `EQ101` for 2 hours.
4. Try booking `EQ101` again to demonstrate validation.
5. Report a fault against `EQ102`.
6. Log in as admin and move that fault report to `In Progress`, then `Resolved`.
7. Show that the equipment becomes available again.

## Limitations
This is a local, single-computer classroom application. It does not provide networked multi-user access, concurrent booking locks, email verification, or production-grade account recovery. The default admin password must be changed before any real deployment.
