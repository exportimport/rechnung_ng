import os
import shutil
from pathlib import Path

import yaml
from filelock import FileLock


class NotFoundError(Exception):
    pass


class YamlStore:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, entity: str) -> Path:
        return self.data_dir / f"{entity}.yaml"

    def _lock_path(self, entity: str) -> Path:
        return self.data_dir / f"{entity}.yaml.lock"

    def _bak_path(self, entity: str) -> Path:
        return self.data_dir / f"{entity}.yaml.bak"

    def load(self, entity: str) -> list[dict]:
        path = self._path(entity)
        if not path.exists():
            return []
        with open(path) as f:
            data = yaml.safe_load(f)
        return data or []

    def save(self, entity: str, records: list[dict]) -> None:
        path = self._path(entity)
        tmp_path = self.data_dir / f"{entity}.yaml.tmp"
        lock = FileLock(str(self._lock_path(entity)))
        with lock:
            if path.exists():
                shutil.copy2(path, self._bak_path(entity))
            with open(tmp_path, "w") as f:
                yaml.dump(records, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            os.replace(tmp_path, path)

    def get_by_id(self, entity: str, id: int | str) -> dict | None:
        for record in self.load(entity):
            if record.get("id") == id:
                return record
        return None

    def create(self, entity: str, data: dict) -> dict:
        records = self.load(entity)
        # Auto-increment integer IDs; string IDs must be provided in data
        if "id" not in data:
            existing_ids = [r["id"] for r in records if isinstance(r.get("id"), int)]
            data["id"] = max(existing_ids, default=0) + 1
        records.append(data)
        self.save(entity, records)
        return data

    def update(self, entity: str, id: int | str, data: dict) -> dict:
        records = self.load(entity)
        for i, record in enumerate(records):
            if record.get("id") == id:
                records[i] = {**record, **data}
                self.save(entity, records)
                return records[i]
        raise NotFoundError(f"{entity} with id={id!r} not found")

    def delete(self, entity: str, id: int | str) -> None:
        records = self.load(entity)
        new_records = [r for r in records if r.get("id") != id]
        if len(new_records) == len(records):
            raise NotFoundError(f"{entity} with id={id!r} not found")
        self.save(entity, new_records)


# Module-level singleton using the default data directory
_default_data_dir = Path(__file__).parent.parent.parent / "data"
store = YamlStore(_default_data_dir)
