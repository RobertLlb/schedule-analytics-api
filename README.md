# Schedule Analytics API

A small **FastAPI** service that calculates the **critical path (CPM)** of a project schedule and **earned value (EVM)** indicators. You can send tasks as JSON or upload a CSV exported from a spreadsheet.

[![CI](https://github.com/RobertLlb/schedule-analytics-api/actions/workflows/ci.yml/badge.svg)](https://github.com/RobertLlb/schedule-analytics-api/actions/workflows/ci.yml)

## Why I built it

For about ten years I worked in industrial planning and project controls. Critical path, float and earned value were part of my daily work, usually in spreadsheets and MS Project. This API is those calculations written as clean, tested code, so other tools can use them.

> The example data is **synthetic**. It does not describe any real project or company.

## Features

- **Critical path method:** forward and backward pass, early/late dates, total float, critical tasks. Parallel critical paths are all reported.
- **Input validation:** duplicate ids, unknown predecessors, negative durations and **dependency cycles** return a clear `422` error, never a crash.
- **CSV import:** comma or semicolon delimiter, UTF-8 with or without BOM, and errors that name the line (`line 2: duration must be a whole number`).
- **Earned value:** SV, CV, SPI, CPI, EAC, ETC, VAC and TCPI. Undefined ratios (division by zero) return `null`, not `NaN` or `Infinity`.
- **Interactive docs:** OpenAPI at `/docs`.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000/docs>. Or use Docker:

```bash
docker build -t schedule-analytics-api .
docker run --rm -p 8000:8000 schedule-analytics-api
```

## Example

```bash
curl -X POST http://127.0.0.1:8000/cpm/csv \
  -H "Content-Type: text/csv" \
  --data-binary @examples/retrofit_schedule.csv
```

For the sample file (9 tasks) the API returns a **project duration of 140** and the critical path `A → B → C → D → E → G → H → I`. Task `F` (site preparation) has **60 days of float**: it finishes on day 45 but `G` cannot start before day 105.

### CSV format

```csv
id,name,duration,predecessors
A,Basic design,10,
B,Detailed design,20,A
G,Installation,25,E;F
```

`predecessors` is a list of task ids separated by `;`. All links are finish-to-start.

### Earned value

```bash
curl -X POST http://127.0.0.1:8000/evm \
  -H "Content-Type: application/json" \
  -d '{"bac": 1000, "pv": 500, "ev": 450, "ac": 600}'
```

returns `spi: 0.9`, `cpi: 0.75`, `eac: 1333.33` and the other indicators.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Liveness check |
| POST | `/cpm` | Critical path from a JSON task list |
| POST | `/cpm/csv` | Critical path from a CSV request body |
| POST | `/evm` | Earned value indicators |

## Tests

```bash
pytest --cov=app --cov-report=term-missing   # 36 tests, 99% coverage
ruff check .
```

## Design notes

- **Pure core, thin API.** `cpm.py`, `evm.py` and `csv_import.py` do not import FastAPI, so they are tested directly. `main.py` only validates input and maps errors to HTTP codes.
- **Kahn's algorithm** gives a topological order and detects cycles in one pass. Ties keep input order, so output is stable.
- **Limits.** Requests are capped at 5,000 tasks and 1 MB of CSV to avoid abuse.
- **Out of scope (for now).** Start-to-start and finish-to-finish links, lags, calendars and resource levelling.

## Author

Robert Barbosa · [GitHub](https://github.com/RobertLlb) · [LinkedIn](https://www.linkedin.com/in/robert-lucas-barbosa-60620214a)
