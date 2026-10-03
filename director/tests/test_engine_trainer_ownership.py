"""Canonical Engine/Trainer ownership and retained compatibility façades."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_canonical_imports_are_component_owned():
    from composer.workbook_opening import _add_bav_opening
    from director.build_contract import BUILD_MODULES as POLICY
    from legacy.trainer.checker import check_workbook
    from legacy.trainer.derive import build_training_workbook, derive_trainer_workbook
    from modeler.build_bav import build_bav_workbook, finalize_bav
    from modeler.check_context import embed_check_context_sheet, live_classification_formula
    from modeler.engine.build_contract import BUILD_MODULES, complete_build_modules
    from modeler.engine.component_catalog import COMPONENT_CATALOG
    from modeler.engine.map_embed import embed_component_map_sheet
    from modeler.engine.semantic_map import SemanticMap
    from modeler.semantic_io import load_semantic_map
    from modeler.workbook import ReferenceModelBuilder

    assert POLICY[-1].id == "forecast"
    assert POLICY[-1].status == "deferred"
    assert [m.id for m in POLICY] == [m.id for m in BUILD_MODULES]
    assert BUILD_MODULES[-1].status == "deferred"
    assert callable(complete_build_modules)
    assert callable(ReferenceModelBuilder.build)
    assert callable(build_bav_workbook)
    assert callable(finalize_bav)
    assert callable(_add_bav_opening)
    assert callable(load_semantic_map)
    assert callable(live_classification_formula)
    assert callable(embed_check_context_sheet)
    assert callable(embed_component_map_sheet)
    assert COMPONENT_CATALOG
    assert SemanticMap
    assert callable(build_training_workbook)
    assert callable(derive_trainer_workbook)
    assert callable(check_workbook)


def test_compatibility_exports_are_identity_equal():
    from composer.workbook_opening import _add_bav_opening as canonical_opening
    from legacy.trainer.checker import check_workbook as canonical_check
    from legacy.trainer.derive import (
        build_training_workbook as canonical_training,
        derive_trainer_workbook as canonical_derive,
    )
    from modeler.build_bav import build_bav_workbook as canonical_bav
    from modeler.check_context import live_classification_formula as canonical_live
    from modeler.engine.build_contract import (
        BUILD_MODULES as canonical_modules,
        complete_build_modules as canonical_complete,
    )
    from modeler.engine.component_catalog import COMPONENT_CATALOG as canonical_catalog
    from modeler.engine.semantic_map import SemanticMap as canonical_map
    from modeler.semantic_io import load_semantic_map as canonical_load
    from modeler.workbook import ReferenceModelBuilder as canonical_builder
    from core.engine.build_contract import (
        BUILD_MODULES as facade_modules,
        complete_build_modules as facade_complete,
    )
    from core.engine.component_catalog import COMPONENT_CATALOG as facade_catalog
    from core.engine.reference_model import ReferenceModelBuilder as facade_builder
    from core.engine.semantic_map import SemanticMap as facade_map
    from core.trainer.check_context import live_classification_formula as facade_live
    from core.trainer.checker import check_workbook as facade_check
    from core.trainer.semantic_io import load_semantic_map as facade_load
    from core.trainer.workbook import (
        _add_bav_opening as facade_opening,
        build_bav_workbook as facade_bav,
        build_training_workbook as facade_training,
        derive_trainer_workbook as facade_derive,
    )

    assert facade_bav is canonical_bav
    assert facade_opening is canonical_opening
    assert facade_load is canonical_load
    assert facade_live is canonical_live
    assert facade_check is canonical_check
    assert facade_training is canonical_training
    assert facade_derive is canonical_derive
    assert facade_builder is canonical_builder
    assert facade_map is canonical_map
    assert facade_catalog is canonical_catalog
    assert facade_complete is canonical_complete
    assert facade_modules is canonical_modules


def test_facade_and_canonical_import_orders():
    orders = (
        (
            "import core.engine.reference_model as facade_rm\n"
            "import modeler.workbook as canonical_rm\n"
            "import core.trainer.workbook as facade_wb\n"
            "import modeler.build_bav as canonical_bav\n"
        ),
        (
            "import modeler.workbook as canonical_rm\n"
            "import core.engine.reference_model as facade_rm\n"
            "import modeler.build_bav as canonical_bav\n"
            "import core.trainer.workbook as facade_wb\n"
        ),
    )
    for import_order in orders:
        script = f"""
{import_order}
from composer.workbook_opening import _add_bav_opening
from legacy.trainer.derive import build_training_workbook
assert facade_rm.ReferenceModelBuilder is canonical_rm.ReferenceModelBuilder
assert facade_wb.build_bav_workbook is canonical_bav.build_bav_workbook
assert facade_wb._add_bav_opening is _add_bav_opening
assert facade_wb.build_training_workbook is build_training_workbook
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            check=False,
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )
        assert result.returncode == 0, result.stderr or result.stdout


def test_company_build_does_not_load_trainer_or_legacy(tmp_path, monkeypatch):
    script = r"""
import sys
from pathlib import Path

class BlockTrainer:
    def find_spec(self, name, path=None, target=None):
        if name == "legacy.trainer" or name.startswith("legacy.trainer."):
            raise ImportError(f"blocked {name}")
        if name == "legacy.ingestion" or name.startswith("legacy.ingestion."):
            raise ImportError(f"blocked {name}")
        if name == "core.trainer" or name.startswith("core.trainer."):
            raise ImportError(f"blocked {name}")
        return None

sys.meta_path.insert(0, BlockTrainer())
from core import current_build
from core.__main__ import main
current_build.OUTPUT_ROOT = Path(sys.argv[1])
assert main(["build", "Lululemon"]) == 0
assert main(["check", "Lululemon"]) == 0
assert main(["publish", "Lululemon"]) == 0
assert not any(name == "legacy.trainer" or name.startswith("legacy.trainer.") for name in sys.modules)
assert not any(name == "legacy.ingestion" or name.startswith("legacy.ingestion.") for name in sys.modules)
assert not any(name == "core.trainer" or name.startswith("core.trainer.") for name in sys.modules)
assert "core.ingestion.manual_hk" not in sys.modules
assert "core.ingestion.excel_import" not in sys.modules
company = current_build.resolve_company("Lululemon")
assert company.bav.is_file()
assert not company.trainer.is_file()
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(tmp_path)],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_explicit_json_build_derives_trainer(tmp_path):
    from core.__main__ import main

    source = ROOT / "core/tests/fixtures/ordinary_reconcile/lululemon/standardized.json"
    out = tmp_path / "Example"
    assert main(["build", str(source), "-o", str(out)]) == 0
    trainer = tmp_path / "Example_BAV_Trainer.xlsx"
    assert (tmp_path / "Example_BAV.xlsx").is_file()
    assert trainer.is_file()
    assert main(["check", "--workbook", str(trainer)]) == 0


RESTORED_BUILD_WRITERS = (
    "SOURCE",
    "CONDENSED",
    "DUPONT",
    "JUDGMENT",
    "OWNERSHIP",
    "NORMALIZATION_JUDGMENT",
    "NORMALIZATION",
    "QUALITY",
    "WORKING_CAPITAL",
    "PER_SHARE",
    "GEOGRAPHIC",
    "OPERATING_KPI",
    "COMPARABLE_SALES",
    "SALES_PER_SQUARE_FOOT",
    "REVENUE_PER_STORE",
    "REVENUE_DRIVER",
)


def test_restored_compatibility_exports_are_identity_equal():
    from core.engine.build_contract import (
        COMPARABLE_SALES,
        CONDENSED,
        DUPONT,
        GEOGRAPHIC,
        JUDGMENT,
        NORMALIZATION,
        NORMALIZATION_JUDGMENT,
        OPERATING_KPI,
        OWNERSHIP,
        PER_SHARE,
        QUALITY,
        REVENUE_DRIVER,
        REVENUE_PER_STORE,
        SALES_PER_SQUARE_FOOT,
        SOURCE,
        WORKING_CAPITAL,
        __all__ as facade_contract_all,
    )
    from core.trainer.workbook import CLEAR_BORDER, __all__ as facade_workbook_all
    from modeler.build_bav import CLEAR_BORDER as canonical_clear_border
    from modeler.engine.build_contract import (
        COMPARABLE_SALES as canonical_comparable_sales,
        CONDENSED as canonical_condensed,
        DUPONT as canonical_dupont,
        GEOGRAPHIC as canonical_geographic,
        JUDGMENT as canonical_judgment,
        NORMALIZATION as canonical_normalization,
        NORMALIZATION_JUDGMENT as canonical_normalization_judgment,
        OPERATING_KPI as canonical_operating_kpi,
        OWNERSHIP as canonical_ownership,
        PER_SHARE as canonical_per_share,
        QUALITY as canonical_quality,
        REVENUE_DRIVER as canonical_revenue_driver,
        REVENUE_PER_STORE as canonical_revenue_per_store,
        SALES_PER_SQUARE_FOOT as canonical_sales_per_square_foot,
        SOURCE as canonical_source,
        WORKING_CAPITAL as canonical_working_capital,
    )

    assert SOURCE is canonical_source
    assert CONDENSED is canonical_condensed
    assert DUPONT is canonical_dupont
    assert JUDGMENT is canonical_judgment
    assert OWNERSHIP is canonical_ownership
    assert NORMALIZATION_JUDGMENT is canonical_normalization_judgment
    assert NORMALIZATION is canonical_normalization
    assert QUALITY is canonical_quality
    assert WORKING_CAPITAL is canonical_working_capital
    assert PER_SHARE is canonical_per_share
    assert GEOGRAPHIC is canonical_geographic
    assert OPERATING_KPI is canonical_operating_kpi
    assert COMPARABLE_SALES is canonical_comparable_sales
    assert SALES_PER_SQUARE_FOOT is canonical_sales_per_square_foot
    assert REVENUE_PER_STORE is canonical_revenue_per_store
    assert REVENUE_DRIVER is canonical_revenue_driver
    assert CLEAR_BORDER is canonical_clear_border
    for name in RESTORED_BUILD_WRITERS:
        assert name in facade_contract_all
    assert "CLEAR_BORDER" in facade_workbook_all


def test_restored_export_import_orders():
    orders = (
        (
            "import core.engine.build_contract as facade_bc\n"
            "import modeler.engine.build_contract as canonical_bc\n"
            "import core.trainer.workbook as facade_wb\n"
            "import modeler.build_bav as canonical_bav\n"
        ),
        (
            "import modeler.engine.build_contract as canonical_bc\n"
            "import core.engine.build_contract as facade_bc\n"
            "import modeler.build_bav as canonical_bav\n"
            "import core.trainer.workbook as facade_wb\n"
        ),
    )
    names = ", ".join(RESTORED_BUILD_WRITERS)
    for import_order in orders:
        script = f"""
{import_order}
from core.engine.build_contract import {names}
from core.trainer.workbook import CLEAR_BORDER
from modeler.build_bav import CLEAR_BORDER as canonical_clear_border
from modeler.engine.build_contract import {names}
assert facade_wb.CLEAR_BORDER is canonical_bav.CLEAR_BORDER is CLEAR_BORDER is canonical_clear_border
assert "CLEAR_BORDER" in facade_wb.__all__
for name in {RESTORED_BUILD_WRITERS!r}:
    assert getattr(facade_bc, name) is getattr(canonical_bc, name)
    assert name in facade_bc.__all__
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            check=False,
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )
        assert result.returncode == 0, result.stderr or result.stdout
