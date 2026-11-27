"""Identify the running application independently from the user's library."""
import hashlib
from pathlib import Path

def build_id(root=None):
 root=Path(root or Path(__file__).resolve().parents[1]);digest=hashlib.sha256(str(root.resolve()).encode())
 files=sorted(p for p in (root/'backend').iterdir() if p.suffix in ('.py','.mjs') and not p.name.startswith('test_'))
 files.append(root/'web/dist/index.html')
 files.append(root.parent/'short-drama/references/document-contract.json')
 for path in files:
  if path.is_file():digest.update(path.name.encode());digest.update(path.read_bytes())
 return digest.hexdigest()
