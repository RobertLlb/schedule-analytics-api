from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from app.cpm import CycleError, Schedule, Task, compute_schedule
from app.csv_import import CsvImportError, parse_tasks_csv
from app.evm import compute_evm

MAX_CSV_BYTES = 1_000_000
MAX_TASKS = 5000

app = FastAPI(
    title="Schedule Analytics API",
    version="1.0.0",
    description="Critical path (CPM) and earned value (EVM) calculations for project schedules.",
)


class TaskIn(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    name: str = Field(default="", max_length=200)
    duration: int = Field(ge=0, le=100_000, description="Duration in time units (for example days)")
    predecessors: list[str] = Field(default_factory=list, max_length=200)


class ScheduleIn(BaseModel):
    tasks: list[TaskIn] = Field(min_length=1, max_length=MAX_TASKS)


class ScheduledTaskOut(BaseModel):
    id: str
    name: str
    duration: int
    predecessors: list[str]
    early_start: int
    early_finish: int
    late_start: int
    late_finish: int
    total_float: int
    is_critical: bool


class ScheduleOut(BaseModel):
    project_duration: int
    critical_path: list[str]
    tasks: list[ScheduledTaskOut]


class EvmIn(BaseModel):
    bac: float = Field(ge=0, description="Budget at completion")
    pv: float = Field(ge=0, description="Planned value")
    ev: float = Field(ge=0, description="Earned value")
    ac: float = Field(ge=0, description="Actual cost")


class EvmOut(BaseModel):
    sv: float
    cv: float
    spi: float | None
    cpi: float | None
    eac: float | None
    etc: float | None
    vac: float | None
    tcpi: float | None


def _to_out(schedule: Schedule) -> ScheduleOut:
    return ScheduleOut(
        project_duration=schedule.project_duration,
        critical_path=schedule.critical_path,
        tasks=[
            ScheduledTaskOut(
                id=t.id,
                name=t.name,
                duration=t.duration,
                predecessors=list(t.predecessors),
                early_start=t.early_start,
                early_finish=t.early_finish,
                late_start=t.late_start,
                late_finish=t.late_finish,
                total_float=t.total_float,
                is_critical=t.is_critical,
            )
            for t in schedule.tasks
        ],
    )


def _run_cpm(tasks: list[Task]) -> ScheduleOut:
    try:
        return _to_out(compute_schedule(tasks))
    except CycleError as error:
        raise HTTPException(status_code=422, detail=f"Dependency cycle: {error}") from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/cpm", response_model=ScheduleOut, summary="Critical path from a JSON task list")
def cpm(payload: ScheduleIn) -> ScheduleOut:
    tasks = [Task(t.id, t.name, t.duration, tuple(t.predecessors)) for t in payload.tasks]
    return _run_cpm(tasks)


@app.post(
    "/cpm/csv",
    response_model=ScheduleOut,
    summary="Critical path from a CSV body",
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {"text/csv": {"schema": {"type": "string"}}},
        }
    },
)
async def cpm_csv(request: Request) -> ScheduleOut:
    raw = await request.body()
    if len(raw) > MAX_CSV_BYTES:
        raise HTTPException(status_code=413, detail="CSV is too large")
    try:
        tasks = parse_tasks_csv(raw.decode("utf-8-sig"))
    except UnicodeDecodeError as error:
        raise HTTPException(status_code=422, detail="CSV must be UTF-8 text") from error
    except CsvImportError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return _run_cpm(tasks)


@app.post("/evm", response_model=EvmOut, summary="Earned value indicators")
def evm(payload: EvmIn) -> EvmOut:
    result = compute_evm(bac=payload.bac, pv=payload.pv, ev=payload.ev, ac=payload.ac)
    return EvmOut(**result.__dict__)
