from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any


@dataclass
class ProjectRecord:
    project_id: str
    state: dict[str, Any]
    current_step: int = 1
    status: str = "initialized"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class InMemoryProjectStore:
    def __init__(self, storage_path: str | Path | None = None) -> None:
        self._records: dict[str, ProjectRecord] = {}
        self._lock = Lock()
        self._storage_path = Path(storage_path) if storage_path else None
        if self._storage_path:
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            self._load()

    def create(self, project_id: str, state: dict[str, Any]) -> ProjectRecord:
        record = ProjectRecord(project_id=project_id, state=deepcopy(state))
        with self._lock:
            self._records[project_id] = record
            self._save()
        return deepcopy(record)

    def get(self, project_id: str) -> ProjectRecord | None:
        with self._lock:
            record = self._records.get(project_id)
            return deepcopy(record) if record else None

    def update(
        self,
        project_id: str,
        *,
        state_updates: dict[str, Any] | None = None,
        current_step: int | None = None,
        status: str | None = None,
    ) -> ProjectRecord:
        with self._lock:
            if project_id not in self._records:
                raise KeyError(project_id)

            record = self._records[project_id]
            if state_updates:
                record.state.update(state_updates)
            if current_step is not None:
                record.current_step = current_step
            if status is not None:
                record.status = status
            record.updated_at = datetime.utcnow()
            self._save()
            return deepcopy(record)

    def _load(self) -> None:
        if not self._storage_path or not self._storage_path.exists():
            return

        raw_payload = json.loads(self._storage_path.read_text(encoding="utf-8"))
        records = raw_payload.get("records", {})
        loaded_records: dict[str, ProjectRecord] = {}

        for project_id, item in records.items():
            if not isinstance(item, dict):
                continue
            loaded_records[project_id] = ProjectRecord(
                project_id=project_id,
                state=deepcopy(item.get("state", {})),
                current_step=int(item.get("current_step", 1) or 1),
                status=str(item.get("status", "initialized") or "initialized"),
                created_at=_parse_datetime(item.get("created_at")),
                updated_at=_parse_datetime(item.get("updated_at")),
            )

        self._records = loaded_records

    def _save(self) -> None:
        if not self._storage_path:
            return

        payload = {
            "records": {
                project_id: {
                    "project_id": record.project_id,
                    "state": deepcopy(record.state),
                    "current_step": record.current_step,
                    "status": record.status,
                    "created_at": record.created_at.isoformat(),
                    "updated_at": record.updated_at.isoformat(),
                }
                for project_id, record in self._records.items()
            }
        }

        temp_path = self._storage_path.with_suffix(f"{self._storage_path.suffix}.tmp")
        temp_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        temp_path.replace(self._storage_path)


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass
    return datetime.utcnow()
