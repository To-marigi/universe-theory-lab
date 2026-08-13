"""Build the corrected residual-unit cache for the bounded Groebner probe.

The cache contains complete 2-by-2 CPOBC residual units, not individual
scalar entries. It is scratch input for the hard-timeout worker and is not a
research artifact.
"""

from __future__ import annotations

import json

from probe_v042_721_groebner_preflight_worker import (
    CACHE_PATH,
    _smallest_reduced_residual_units,
)


def main() -> None:
    units = _smallest_reduced_residual_units(200)
    serialised = []
    for unit in units:
        serialised.append(
            {
                "first_id": unit["first_id"],
                "second_id": unit["second_id"],
                "selection_key": list(unit["selection_key"]),
                "matrix_stats": unit["matrix_stats"],
                "entries": [
                    {
                        "row": entry["row"],
                        "column": entry["column"],
                        "scalar": {
                            "|".join(monomial): coefficient
                            for monomial, coefficient in entry["scalar"].items()
                        },
                    }
                    for entry in unit["entries"]
                ],
            }
        )
    CACHE_PATH.write_text(
        json.dumps(serialised, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {CACHE_PATH} units={len(serialised)}")


if __name__ == "__main__":
    main()
