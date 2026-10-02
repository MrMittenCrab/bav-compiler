"""Compatibility façade. Director owns policy; Modeler owns execution."""

from director.build_contract import BUILD_MODULES as BUILD_MODULE_POLICY
from modeler.engine.build_contract import (
    BUILD_MODULES,
    BuildModule,
    RequiredInput,
    WorkbookWriter,
    complete_build_modules,
    prepare_complete_build,
    verify_complete_build,
    write_complete_build,
)

__all__ = [
    "BUILD_MODULES",
    "BUILD_MODULE_POLICY",
    "BuildModule",
    "RequiredInput",
    "WorkbookWriter",
    "complete_build_modules",
    "prepare_complete_build",
    "verify_complete_build",
    "write_complete_build",
]
