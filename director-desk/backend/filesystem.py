"""Use Windows extended paths only at I/O boundaries; project paths stay portable."""
import os
from pathlib import Path


def io_path(path):
    path=Path(path).resolve()
    if os.name!='nt' or str(path).startswith('\\\\?\\'):return path
    raw=str(path)
    return Path('\\\\?\\UNC\\'+raw[2:] if raw.startswith('\\\\') else '\\\\?\\'+raw)


from contextlib import contextmanager
import shutil
import tempfile

@contextmanager
def temporary_directory(parent=None):
    base=Path(parent or tempfile.gettempdir()).resolve()
    folder=Path(tempfile.mkdtemp(dir=base)).resolve()
    try:yield str(folder)
    finally:
        if folder.parent!=base:raise ValueError('Temporary folder escaped its parent')
        shutil.rmtree(io_path(folder))


def walk_files(root):
    root=Path(root);physical=io_path(root)
    for path in physical.rglob('*'):
        if path.is_file():yield root/path.relative_to(physical)
