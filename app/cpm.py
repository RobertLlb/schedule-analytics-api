"""Critical Path Method (CPM) on a finish-to-start task network."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass


class CycleError(ValueError):
    """Raised when the task network contains a dependency cycle."""


@dataclass(frozen=True)
class Task:
    id: str
    name: str
    duration: int
    predecessors: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScheduledTask:
    id: str
    name: str
    duration: int
    predecessors: tuple[str, ...]
    early_start: int
    early_finish: int
    late_start: int
    late_finish: int
    total_float: int
    is_critical: bool


@dataclass(frozen=True)
class Schedule:
    tasks: list[ScheduledTask]
    project_duration: int
    critical_path: list[str]


def _validate(tasks: list[Task]) -> dict[str, Task]:
    if not tasks:
        raise ValueError("schedule needs at least one task")

    by_id: dict[str, Task] = {}
    for task in tasks:
        if task.id in by_id:
            raise ValueError(f"duplicate task id: {task.id}")
        if task.duration < 0:
            raise ValueError(f"task {task.id} has a negative duration")
        by_id[task.id] = task

    for task in tasks:
        for pred in task.predecessors:
            if pred not in by_id:
                raise ValueError(f"task {task.id} has unknown predecessor: {pred}")
    return by_id


def _topological_order(by_id: dict[str, Task]) -> list[str]:
    """Kahn's algorithm. Keeps input order for ties so output is stable."""
    indegree = {tid: len(set(t.predecessors)) for tid, t in by_id.items()}
    successors: dict[str, list[str]] = {tid: [] for tid in by_id}
    for tid, task in by_id.items():
        for pred in set(task.predecessors):
            successors[pred].append(tid)

    queue = deque(tid for tid in by_id if indegree[tid] == 0)
    order: list[str] = []
    while queue:
        current = queue.popleft()
        order.append(current)
        for nxt in successors[current]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)

    if len(order) != len(by_id):
        stuck = sorted(set(by_id) - set(order))
        raise CycleError(f"dependency cycle detected involving: {', '.join(stuck)}")
    return order


def compute_schedule(tasks: list[Task]) -> Schedule:
    by_id = _validate(tasks)
    order = _topological_order(by_id)

    early_start: dict[str, int] = {}
    early_finish: dict[str, int] = {}
    for tid in order:
        task = by_id[tid]
        early_start[tid] = max((early_finish[p] for p in task.predecessors), default=0)
        early_finish[tid] = early_start[tid] + task.duration

    project_duration = max(early_finish.values())

    successors: dict[str, list[str]] = {tid: [] for tid in by_id}
    for tid, task in by_id.items():
        for pred in set(task.predecessors):
            successors[pred].append(tid)

    late_start: dict[str, int] = {}
    late_finish: dict[str, int] = {}
    for tid in reversed(order):
        late_finish[tid] = min((late_start[s] for s in successors[tid]), default=project_duration)
        late_start[tid] = late_finish[tid] - by_id[tid].duration

    scheduled = [
        ScheduledTask(
            id=tid,
            name=by_id[tid].name,
            duration=by_id[tid].duration,
            predecessors=by_id[tid].predecessors,
            early_start=early_start[tid],
            early_finish=early_finish[tid],
            late_start=late_start[tid],
            late_finish=late_finish[tid],
            total_float=late_start[tid] - early_start[tid],
            is_critical=late_start[tid] == early_start[tid],
        )
        for tid in order
    ]
    critical = sorted(
        (t for t in scheduled if t.is_critical),
        key=lambda t: (t.early_start, t.early_finish),
    )
    return Schedule(
        tasks=scheduled,
        project_duration=project_duration,
        critical_path=[t.id for t in critical],
    )
