#!/usr/bin/env python3
"""Consume menu requests only after HW2HACKEDCLIENT has finished writing its saves."""
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import struct
import time
import traceback

DIRECTORY = Path(__file__).resolve().parent
REQUEST = DIRECTORY / 'unlock.request'
STATUS = DIRECTORY / 'unlock.status'

def local_progression_intact():
    saved = Path(os.path.expanduser('~') + "/.local/share/Steam/steamapps/compatdata/5155360/pfx/drive_c/users/steamuser/AppData/Local/HW2HACKEDCLIENT/Saved")
    try:
        account = json.loads((saved / 'HW2HACKEDCLIENTOnline/AccountLevel.json').read_text())
        if account.get('level', 0) < 100:
            return False
        data = (saved / 'SaveGames/ProgressionSave.sav').read_bytes()
        cursor = data.index(b'AK-47|Kills\0', data.index(b'SavedStats\0')) - 4
        count = struct.unpack_from('<i', data, cursor - 4)[0]
        for _ in range(count):
            length = struct.unpack_from('<i', data, cursor)[0]
            cursor += 4
            key = data[cursor:cursor + length - 1].decode()
            cursor += length
            value = struct.unpack_from('<i', data, cursor)[0]
            cursor += 4
            if not key.startswith('@') and '|' in key and value < 10000:
                return False
        return True
    except (OSError, ValueError, struct.error, UnicodeError):
        return None  # A save may be in the middle of a write; retry later.

def game_running():
    for path in Path('/proc').glob('[0-9]*/cmdline'):
        try:
            argv = path.read_bytes().split(b'\0')
            if argv and b'HW2HACKEDCLIENT-HoodWarfare2-Win64-Shipping.exe' in argv[0]:
                return True
        except (OSError, PermissionError):
            pass
    return False

def apply():
    spec = importlib.util.spec_from_file_location('HW2HACKEDCLIENT_unlock', os.path.expanduser('~') + "/unlock_HW2HACKEDCLIENT_weapons.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main()

def main():
    with (DIRECTORY / 'worker.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        while True:
            if STATUS.exists() and STATUS.read_text().startswith(('Applied:', 'Local edits applied:')):
                if local_progression_intact() is False:
                    STATUS.write_text('Reverted: the online profile replaced the local progression edits. Online unlocks have not been granted.\n')
            if REQUEST.exists():
                if game_running():
                    STATUS.write_text('Queued. Close HW2HACKEDCLIENT, then wait for unlock.status to say Applied before relaunching.\n')
                else:
                    # Allow late shutdown writes to settle, then recheck.
                    time.sleep(2)
                    if game_running():
                        continue
                    try:
                        apply()
                    except Exception:
                        STATUS.write_text('Failed; request kept. See worker.log.\n')
                        traceback.print_exc()
                        return
                    STATUS.write_text('Local edits applied: level 100 and weapon challenge stats changed. In-game unlocks are unverified; online profile sync may restore the previous progression.\n')
                    REQUEST.unlink()
            time.sleep(1)

if __name__ == '__main__':
    main()
