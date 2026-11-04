#!/usr/bin/env python3
import json
import os
import shutil
import struct
from datetime import datetime
from pathlib import Path

ROOT = Path(os.path.expanduser('~') + "/.local/share/Steam/steamapps/compatdata/5155360/pfx/drive_c/users/steamuser/AppData/Local/HW2HACKEDCLIENT/Saved")
SAVES = ROOT / "SaveGames"
STAMP = datetime.now().strftime("%Y%m%d-%H%M%S")
TARGET_LEVEL = 100
TARGET_STAT = 10000


def backup(path: Path) -> Path:
    destination = path.with_name(f"{path.name}.before-unlock-{STAMP}.bak")
    shutil.copy2(path, destination)
    return destination


def fstring(value: str) -> bytes:
    encoded = value.encode("utf-8") + b"\0"
    return struct.pack("<i", len(encoded)) + encoded


def patch_level_save(path: Path) -> None:
    data = bytearray(path.read_bytes())
    values = {b"Level\0": TARGET_LEVEL, b"Experience\0": 0}
    for marker, value in values.items():
        start = data.index(marker, 0x700)
        type_start = start + len(marker)
        type_length = struct.unpack_from("<i", data, type_start)[0]
        assert data[type_start + 4:type_start + 4 + type_length] == b"IntProperty\0"
        value_offset = type_start + 4 + type_length + 9
        struct.pack_into("<i", data, value_offset, value)
    path.write_bytes(data)


def patch_progression(path: Path) -> None:
    data = bytearray(path.read_bytes())
    first_entry = data.index(fstring("AK-47|Kills"), data.index(b"SavedStats\0"))
    count_offset = first_entry - 4
    size_offset = count_offset - 9
    count = struct.unpack_from("<i", data, count_offset)[0]
    old_size = struct.unpack_from("<I", data, size_offset)[0]
    assert old_size > 4 and data[size_offset + 4:count_offset] == b"\0" * 5

    cursor = count_offset + 4
    stats = {}
    for _ in range(count):
        length = struct.unpack_from("<i", data, cursor)[0]
        cursor += 4
        key = bytes(data[cursor:cursor + length - 1]).decode("utf-8")
        cursor += length
        stats[key] = struct.unpack_from("<i", data, cursor)[0]
        cursor += 4
    # UE 5.8 includes the following property's four-byte FString length in this
    # MapProperty size field. Keep that quirk intact for this game's saves.
    assert cursor + 4 == count_offset + old_size

    weapons = ("AK-47", "AKM", "M14", "M40A5", "Mac-10", "Uzi", "12-Gauge", "Glock", "X24")
    challenges = ("Kills", "Headshots", "ADS", "Hipfire", "NoOptic", "Objective", "BestStreak", "Longshots", "Doubles", "Triples", "Crouched")
    for weapon in weapons:
        for challenge in challenges:
            stats[f"{weapon}|{challenge}"] = TARGET_STAT

    payload = bytearray(struct.pack("<i", len(stats)))
    for key, value in stats.items():
        payload += fstring(key)
        payload += struct.pack("<i", value)

    data[count_offset:cursor] = payload
    struct.pack_into("<I", data, size_offset, len(payload) + 4)
    path.write_bytes(data)


def patch_account_level(path: Path) -> None:
    account = json.loads(path.read_text())
    account["level"] = TARGET_LEVEL
    path.write_text(json.dumps(account, indent=2) + "\n")


def main() -> None:
    targets = [SAVES / "LevelSave.sav", SAVES / "ProgressionSave.sav", ROOT / "HW2HACKEDCLIENTOnline" / "AccountLevel.json"]
    backups = [backup(path) for path in targets]
    patch_level_save(targets[0])
    patch_progression(targets[1])
    patch_account_level(targets[2])
    print(f"Set player/account level to {TARGET_LEVEL} and weapon challenge stats to {TARGET_STAT}.")
    for item in backups:
        print(f"Backup: {item}")


if __name__ == "__main__":
    main()
