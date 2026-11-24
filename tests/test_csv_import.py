import pytest

from app.csv_import import CsvImportError, parse_tasks_csv

VALID = """id,name,duration,predecessors
A,Design,3,
B,Order parts,2,A
C,Prepare site,4,A
D,Install,5,B;C
"""


def test_parses_valid_csv():
    parsed = parse_tasks_csv(VALID)

    assert [t.id for t in parsed] == ["A", "B", "C", "D"]
    assert parsed[3].predecessors == ("B", "C")
    assert parsed[0].predecessors == ()
    assert parsed[1].duration == 2


def test_accepts_semicolon_delimiter_and_spaces():
    text = "id;name;duration;predecessors\nA; Design ;3;\nB;Build;2; A \n"

    parsed = parse_tasks_csv(text)

    assert parsed[0].name == "Design"
    assert parsed[1].predecessors == ("A",)


def test_missing_column_is_reported():
    with pytest.raises(CsvImportError, match="missing column"):
        parse_tasks_csv("id,name\nA,Design\n")


def test_bad_duration_reports_the_line():
    text = "id,name,duration,predecessors\nA,Design,three,\n"

    with pytest.raises(CsvImportError, match="line 2"):
        parse_tasks_csv(text)


def test_empty_file_is_rejected():
    with pytest.raises(CsvImportError, match="empty"):
        parse_tasks_csv("")


def test_blank_id_is_rejected():
    with pytest.raises(CsvImportError, match="line 2"):
        parse_tasks_csv("id,name,duration,predecessors\n,Design,3,\n")


def test_too_many_rows_are_rejected():
    rows = "\n".join(f"T{i},Task,1," for i in range(5001))

    with pytest.raises(CsvImportError, match="too many"):
        parse_tasks_csv("id,name,duration,predecessors\n" + rows)
