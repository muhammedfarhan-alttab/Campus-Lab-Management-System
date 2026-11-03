"""Entry point for the Campus Lab Management System."""
from system import LabManagementSystem
from storage import DataStore

def main():
    app = LabManagementSystem(DataStore())
    app.run()

if __name__ == "__main__":
    main()
