import os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from skill_paths import skills_root

class SkillPathTests(unittest.TestCase):
 def test_checkout_does_not_require_shared_installation(self):
  with patch.dict(os.environ,{},clear=True):
   root=skills_root()
  self.assertEqual(root,Path(__file__).resolve().parents[2])
 def test_explicit_override_is_preserved_and_missing_override_is_not_ignored(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   with patch.dict(os.environ,{'DIRECTOR_SKILLS_HOME':str(root)}):
    with self.assertRaises(ValueError):skills_root()
    (root/'short-drama').mkdir();(root/'short-drama/SKILL.md').write_text('test')
    self.assertEqual(skills_root(),root.resolve())

if __name__=='__main__':unittest.main()
