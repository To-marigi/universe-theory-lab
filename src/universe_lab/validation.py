"""独立した計算法を突き合わせる、環境検証用の小さな計算群。"""

from __future__ import annotations

import importlib
import platform
import sys
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class BackendStatus:
    """計算バックエンドの検出結果。"""

    name: str
    version: str
    available: bool = True


def _backend(name: str, import_name: str | None = None) -> BackendStatus:
    module_name = import_name or name
    try:
        module = importlib.import_module(module_name)
        version = getattr(module, "__version__", "unknown")
        return BackendStatus(name=name, version=str(version))
    except Exception as exc:  # pragma: no cover - 診断時に例外内容を残す
        return BackendStatus(name=name, version=f"{type(exc).__name__}: {exc}", available=False)


def environment_report() -> dict[str, Any]:
    """研究記録に保存できる、実行環境の機械可読レポートを返す。"""

    packages = [
        _backend("NumPy", "numpy"),
        _backend("SciPy", "scipy"),
        _backend("SymPy", "sympy"),
        _backend("mpmath"),
        _backend("FLINT", "flint"),
        _backend("gmpy2"),
        _backend("SymEngine", "symengine"),
        _backend("Numba", "numba"),
        _backend("Dask", "dask"),
        _backend("QuTiP", "qutip"),
        _backend("EinsteinPy", "einsteinpy"),
    ]
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "backends": [asdict(item) for item in packages],
    }


def _symbolic_identity_check() -> dict[str, Any]:
    """特殊相対論で頻出する双曲線恒等式を厳密に検算する。"""

    import sympy as sp

    rapidity = sp.symbols("eta", real=True)
    residual = sp.trigsimp(sp.cosh(rapidity) ** 2 - sp.sinh(rapidity) ** 2 - 1)
    return {"name": "symbolic_identity", "passed": residual == 0, "residual": str(residual)}


def _arbitrary_precision_check() -> dict[str, Any]:
    """mpmath と FLINT の独立実装で円周率を照合する。"""

    import mpmath as mp
    from flint import arb, ctx

    digits = 100
    mp.mp.dps = digits + 15
    ctx.dps = digits + 15
    pi_mpmath = mp.pi
    # python-flint は Arb の中央値を mpmath が読める内部 mpf 形式で公開する。
    # 文字列表現には誤差半径も含まれるため、数値オブジェクトを直接変換する。
    pi_flint = mp.mpf(arb.pi())
    error = abs(pi_mpmath - pi_flint)
    tolerance = mp.mpf(10) ** (-digits)
    return {
        "name": "arbitrary_precision_crosscheck",
        "passed": bool(error < tolerance),
        "digits": digits,
        "absolute_error": mp.nstr(error, 8),
    }


def _ode_invariant_check() -> dict[str, Any]:
    """調和振動子のエネルギー保存を数値積分で確認する。"""

    import numpy as np
    from scipy.integrate import solve_ivp

    def oscillator(_time: float, state: Any) -> tuple[float, float]:
        position, momentum = state
        return momentum, -position

    solution = solve_ivp(
        oscillator,
        (0.0, 100.0),
        (1.0, 0.0),
        method="DOP853",
        rtol=1e-11,
        atol=1e-13,
        dense_output=False,
    )
    energy = 0.5 * (solution.y[0] ** 2 + solution.y[1] ** 2)
    drift = float(np.max(np.abs(energy - energy[0])))
    return {
        "name": "ode_energy_invariant",
        "passed": bool(solution.success and drift < 1e-8),
        "max_energy_drift": drift,
        "evaluations": int(solution.nfev),
    }


def _quantum_check() -> dict[str, Any]:
    """QuTiPでパウリ交換関係 [σx,σy]=2iσz を検算する。"""

    import qutip as qt

    residual = qt.commutator(qt.sigmax(), qt.sigmay()) - 2j * qt.sigmaz()
    norm = float(residual.norm())
    return {"name": "pauli_commutator", "passed": norm < 1e-13, "residual_norm": norm}


def run_validation_suite() -> dict[str, Any]:
    """全検算を実行し、総合判定と個別結果を返す。"""

    checks = [
        _symbolic_identity_check(),
        _arbitrary_precision_check(),
        _ode_invariant_check(),
        _quantum_check(),
    ]
    return {"passed": all(check["passed"] for check in checks), "checks": checks}
