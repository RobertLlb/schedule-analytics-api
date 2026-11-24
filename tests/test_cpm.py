import pytest

from app.cpm import CycleError, Task, compute_schedule


def tasks():
    return [
        Task("A", "Design", 3, ()),
        Task("B", "Order parts", 2, ("A",)),
        Task("C", "Prepare site", 4, ("A",)),
        Task("D", "Install", 5, ("B", "C")),
    ]


def test_forward_and_backward_pass():
    result = compute_schedule(tasks())
    by_id = {t.id: t for t in result.tasks}

    assert by_id["A"].early_start == 0 and by_id["A"].early_finish == 3
    assert by_id["C"].early_start == 3 and by_id["C"].early_finish == 7
    assert by_id["D"].early_start == 7 and by_id["D"].early_finish == 12
    assert result.project_duration == 12


def test_critical_path_and_float():
    result = compute_schedule(tasks())
    by_id = {t.id: t for t in result.tasks}

    assert result.critical_path == ["A", "C", "D"]
    assert by_id["B"].total_float == 2
    assert by_id["B"].is_critical is False
    assert by_id["C"].total_float == 0


def test_parallel_critical_paths_are_all_reported():
    parallel = [
        Task("A", "Start", 1, ()),
        Task("B", "Left", 3, ("A",)),
        Task("C", "Right", 3, ("A",)),
        Task("D", "End", 1, ("B", "C")),
    ]

    result = compute_schedule(parallel)

    assert set(result.critical_path) == {"A", "B", "C", "D"}


def test_zero_duration_milestone():
    result = compute_schedule([Task("A", "Work", 2, ()), Task("M", "Milestone", 0, ("A",))])

    assert result.project_duration == 2
    assert result.critical_path == ["A", "M"]


def test_cycle_is_rejected():
    cyclic = [Task("A", "A", 1, ("B",)), Task("B", "B", 1, ("A",))]

    with pytest.raises(CycleError):
        compute_schedule(cyclic)


def test_unknown_predecessor_is_rejected():
    with pytest.raises(ValueError, match="unknown predecessor"):
        compute_schedule([Task("A", "A", 1, ("Z",))])


def test_duplicate_ids_are_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        compute_schedule([Task("A", "A", 1, ()), Task("A", "Again", 1, ())])


def test_negative_duration_is_rejected():
    with pytest.raises(ValueError, match="negative"):
        compute_schedule([Task("A", "A", -1, ())])


def test_empty_schedule_is_rejected():
    with pytest.raises(ValueError, match="at least one"):
        compute_schedule([])
