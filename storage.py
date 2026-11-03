"""Small JSON persistence layer using only Python's standard library."""
import json
from pathlib import Path


class DataStore:
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.paths = {
            "users": self.data_dir / "users.json",
            "equipment": self.data_dir / "equipment.json",
            "bookings": self.data_dir / "bookings.json",
            "faults": self.data_dir / "faults.json",
        }
        for path in self.paths.values():
            if not path.exists():
                path.write_text("[]", encoding="utf-8")

    def load(self, key):
        try:
            with self.paths[key].open("r", encoding="utf-8") as file:
                data = json.load(file)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def save(self, key, records):
        temp_path = self.paths[key].with_suffix(".tmp")
        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(records, file, indent=4)
        temp_path.replace(self.paths[key])
