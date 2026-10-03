"""Compatibility façade. Implementation lives in director.current_build."""

from director import current_build as _canonical
import sys

sys.modules[__name__] = _canonical
