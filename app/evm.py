"""Earned value management formulas."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvmResult:
    sv: float
    cv: float
    spi: float | None
    cpi: float | None
    eac: float | None
    etc: float | None
    vac: float | None
    tcpi: float | None


def _ratio(numerator: float, denominator: float) -> float | None:
    return None if denominator == 0 else numerator / denominator


def compute_evm(*, bac: float, pv: float, ev: float, ac: float) -> EvmResult:
    """Compute EVM indicators. Ratios are None when they are undefined.

    bac: budget at completion, pv: planned value, ev: earned value, ac: actual cost.
    """
    for name, value in (("bac", bac), ("pv", pv), ("ev", ev), ("ac", ac)):
        if value < 0:
            raise ValueError(f"{name} must not be negative")

    cpi = _ratio(ev, ac)
    eac = None if not cpi else bac / cpi
    return EvmResult(
        sv=ev - pv,
        cv=ev - ac,
        spi=_ratio(ev, pv),
        cpi=cpi,
        eac=eac,
        etc=None if eac is None else eac - ac,
        vac=None if eac is None else bac - eac,
        tcpi=_ratio(bac - ev, bac - ac),
    )
