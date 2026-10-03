"""Compatibility façade. Implementation lives in director.cli."""

from director.cli import *
from director.cli import (
    _date_key,
    _load_build_json,
    _reject_json_constant,
    _serialize_line_items,
    _unique_json_object,
    _validate_build_output,
)

if __name__ == "__main__":
    raise SystemExit(main())
