import os
from pathlib import Path
import subprocess
import sys

from runtime import Runtime
from production import production_tool

if __name__=='__main__':
    runtime=Runtime(Path(sys.argv[1]).parent);provider=sys.argv[2]
    adapter=Path(production_tool().__file__).with_name('provider_adapters.py')
    result=subprocess.run([sys.executable,str(adapter),provider],input=sys.stdin.buffer.read(),
        stdout=sys.stdout.buffer,stderr=sys.stderr.buffer,env=runtime.environment(provider),
        creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    raise SystemExit(result.returncode)
