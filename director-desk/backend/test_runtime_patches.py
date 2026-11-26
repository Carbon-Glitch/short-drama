import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

@unittest.skipUnless(os.name=='nt' and shutil.which('node'),'Windows Node runtime')
class RuntimePatchTests(unittest.TestCase):
    def test_patch_is_versioned_idempotent_and_preserves_original(self):
        patch=Path(__file__).with_name('runtime-patches.mjs').resolve().as_uri()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'src').mkdir();(root/'package.json').write_text('{"version":"0.4.1"}')
            source="import { basename, dirname, extname, join, resolve } from 'node:path';\naudioDir ??= mkdtempSync(join(dirname(work), `.parts-${process.pid}-audio-`));\n"
            (root/'src/render.mjs').write_text(source)
            script=f"import {{patchWindowsPaths}} from {json.dumps(patch)}; console.log(JSON.stringify([patchWindowsPaths(process.argv[1]),patchWindowsPaths(process.argv[1])]));"
            result=subprocess.run(['node','--input-type=module','-e',script,str(root)],capture_output=True,text=True,check=True)
            self.assertEqual(json.loads(result.stdout),[True,False])
            self.assertEqual((root/'director-desk-backups/render-0.4.1.mjs').read_text(),source)
            self.assertIn('mkdtempSync(toNamespacedPath(', (root/'src/render.mjs').read_text())
            (root/'package.json').write_text('{"version":"9.0.0"}')
            result=subprocess.run(['node','--input-type=module','-e',script,str(root)],capture_output=True,text=True,check=True)
            self.assertEqual(json.loads(result.stdout),[False,False])

if __name__=='__main__':unittest.main()
