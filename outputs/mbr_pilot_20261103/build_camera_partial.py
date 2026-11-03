"""Reporting-only partial adaptation; generation and original scorer untouched."""
from pathlib import Path
H=Path(__file__).parent
s=(H/'camera240_score.py').read_text()
s=s.replace("P=Path('/mnt/m3diff/mbr_pilot_20261103/camera240');ROOT=P.parent", "P=Path('/mnt/m3diff/mbr_pilot_20261103/camera240/partial_diagnostic');ROOT=P.parent.parent")
s=s.replace("assert len(rows)==240 and", "assert 0<len(rows)<240 and")
s=s.replace(";assert len(pure)==180 and len(obj)==60", "")
s=s.replace("'camera_only_n':180", "'camera_only_n':len(pure)").replace("'camera_object_n':60", "'camera_object_n':len(obj)")
s=s.replace("summary['note']=", "summary['partial_only_not_full_camera240']=True\nsummary['note']=")
(H/'camera_partial_score.py').write_text(s)
print('Partial reporting adapter prepared; fixed selector and regex code unchanged.')
