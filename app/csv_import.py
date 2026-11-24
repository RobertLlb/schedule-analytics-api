"""Parse a task list from CSV text (for example exported from a spreadsheet)."""

from __future__ import annotations

import csv
import io

from app.cpm import Task

REQUIRED_COLUMNS = ("id", "name", "duration", "predecessors")
MAX_ROWS = 5000


class CsvImportError(ValueError):
    """Raised when the CSV cannot be turned into a valid task list."""


def _detect_delimiter(header_line: str) -> str:
    return ";" if header_line.count(";") > header_line.count(",") else ","


def parse_tasks_csv(text: str) -> list[Task]:
    if not text.strip():
        raise CsvImportError("file is empty")

    text = text.lstrip("﻿")
    delimiter = _detect_delimiter(text.splitlines()[0])
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)

    headers = [(h or "").strip().lower() for h in (reader.fieldnames or [])]
    for column in REQUIRED_COLUMNS:
        if column not in headers:
            raise CsvImportError(f"missing column: {column}")
    reader.fieldnames = headers

    tasks: list[Task] = []
    for row in reader:
        line = reader.line_num
        if len(tasks) >= MAX_ROWS:
            raise CsvImportError(f"too many rows (limit is {MAX_ROWS})")

        task_id = (row["id"] or "").strip()
        if not task_id:
            raise CsvImportError(f"line {line}: id is empty")

        try:
            duration = int((row["duration"] or "").strip())
        except ValueError:
            raise CsvImportError(f"line {line}: duration must be a whole number") from None

        raw_preds = (row["predecessors"] or "").strip()
        predecessors = tuple(p.strip() for p in raw_preds.split(";") if p.strip())
        tasks.append(Task(task_id, (row["name"] or "").strip(), duration, predecessors))

    if not tasks:
        raise CsvImportError("file has a header but no tasks")
    return tasks
