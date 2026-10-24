"""Read-only storage inventory for experiment runs and published results."""
import json
import os
import shutil
from pathlib import Path


def inventory(root):
    logical=0
    unique=0
    count=0
    seen=set()
    for directory, dirs, files in os.walk(root,followlinks=False):
        dirs[:]=[d for d in dirs if not (Path(directory)/d).is_symlink()]
        for name in files:
            path=Path(directory)/name
            if path.is_symlink():
                continue
            try:
                s=path.stat()
            except FileNotFoundError:
                continue
            count+=1
            logical+=s.st_size
            key=(s.st_dev,s.st_ino) if s.st_ino else str(path.resolve())
            if key not in seen:
                seen.add(key)
                unique+=s.st_size
    return dict(files=count,logical_bytes=logical,unique_file_bytes=unique)


if __name__ == '__main__':
    rows={str(p):inventory(p) for p in (Path('runs'),Path('results'))}
    rows['free_bytes']=shutil.disk_usage('.').free
    rows['scope']='Live read-only snapshot; unique file lengths deduplicate hard links, not filesystem allocated blocks. No files removed.'
    print(json.dumps(rows,indent=2))
