"""Reuse the existing deterministic music-envelope helper on current film windows."""
import json,sys
from pathlib import Path
canonical=Path(__file__).resolve().parents[3]/'hypit/scripts'
if (canonical/'music_envelope.py').is_file():sys.path.insert(0,str(canonical))
from music_envelope import envelope
data=json.loads(sys.argv[1]);config=data['config']
points=envelope(data['windows'],data['duration'],**{k:config[k] for k in ('depth_db','lead','release','merge_gap') if k in config})
print(json.dumps(points))
