import pytest

from app.evm import compute_evm


def test_standard_metrics():
    result = compute_evm(bac=1000, pv=500, ev=450, ac=600)

    assert result.sv == -50
    assert result.cv == -150
    assert result.spi == pytest.approx(0.9)
    assert result.cpi == pytest.approx(0.75)
    assert result.eac == pytest.approx(1000 / 0.75)
    assert result.etc == pytest.approx(1000 / 0.75 - 600)
    assert result.vac == pytest.approx(1000 - 1000 / 0.75)


def test_to_complete_performance_index():
    result = compute_evm(bac=1000, pv=500, ev=450, ac=600)

    assert result.tcpi == pytest.approx((1000 - 450) / (1000 - 600))


def test_zero_planned_value_gives_no_spi():
    result = compute_evm(bac=1000, pv=0, ev=0, ac=0)

    assert result.spi is None
    assert result.cpi is None
    assert result.eac is None


def test_budget_exhausted_gives_no_tcpi():
    result = compute_evm(bac=1000, pv=1000, ev=800, ac=1000)

    assert result.tcpi is None


def test_zero_earned_value_gives_no_forecast():
    result = compute_evm(bac=1000, pv=300, ev=0, ac=200)

    assert result.cpi == 0
    assert result.eac is None


@pytest.mark.parametrize("field", ["bac", "pv", "ev", "ac"])
def test_negative_inputs_are_rejected(field):
    values = {"bac": 100.0, "pv": 10.0, "ev": 10.0, "ac": 10.0, field: -1.0}

    with pytest.raises(ValueError, match="negative"):
        compute_evm(**values)
