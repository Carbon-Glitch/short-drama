"""Director desk uses the same document contract as standalone Skills."""
import importlib.util
from skill_paths import skills_root

_path=skills_root()/'short-drama/scripts/creator_document.py'
_spec=importlib.util.spec_from_file_location('short_drama_creator_document',_path)
_module=importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
CONTRACT=_module.CONTRACT
SHOT_FIELDS=_module.SHOT_FIELDS
FIELD=_module.FIELD
split_fields=_module.split_fields
render_fields=_module.render_fields
check_headings=_module.check_headings
missing_shot_fields=_module.missing_shot_fields
validate_data=_module.validate_data
validate_agent_fields=_module.validate_agent_fields
patch_fields=_module.patch_fields

canonical_fields=_module.canonical_fields
SHOT_DEPENDENCIES=[*SHOT_FIELDS, "references", "design_refs"]

creative_basis=_module.creative_basis
