import importlib.util
import os
import json
from pathlib import Path
import shutil
import struct
import tempfile

spec=importlib.util.spec_from_file_location('unlock', os.path.expanduser('~') + "/unlock_HW2HACKEDCLIENT_weapons.py")
u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)

def stats(data):
 start=data.index(b'SavedStats\0'); first=data.index(u.fstring('AK-47|Kills'),start);count=struct.unpack_from('<i',data,first-4)[0]
 cursor=first;result={}
 for _ in range(count):
  length=struct.unpack_from('<i',data,cursor)[0];cursor+=4;key=data[cursor:cursor+length-1].decode();cursor+=length
  result[key]=struct.unpack_from('<i',data,cursor)[0];cursor+=4
 return result,cursor,data[cursor:]

with tempfile.TemporaryDirectory(prefix='HW2HACKEDCLIENT-unlock-check-') as tmp:
 directory=Path(tmp)
 level=directory/'LevelSave.sav'; progression=directory/'ProgressionSave.sav'; account=directory/'AccountLevel.json'
 shutil.copy2(u.SAVES/level.name,level);shutil.copy2(u.SAVES/progression.name,progression);shutil.copy2(u.ROOT/'HW2HACKEDCLIENTOnline'/account.name,account)
 before,_,tail=stats(progression.read_bytes());u.patch_progression(progression);after,_,new_tail=stats(progression.read_bytes())
 assert tail==new_tail
 assert all(after[k]==v for k,v in before.items() if k.startswith('@'))
 assert all(v>=10000 for k,v in after.items() if not k.startswith('@') and '|' in k)
 assert after['M-14|PointBlanks']==10000 and after['AK-47|Suppressed']==10000
 u.patch_progression(progression);again,_,_=stats(progression.read_bytes());assert after==again
 u.patch_level_save(level);u.patch_account_level(account)
 assert json.loads(account.read_text())['level']==100
 print(f'Passed: {len(after)} stats, current weapon/challenge names, global stats and trailing save data preserved, repeated unlock stable.')
