#!/usr/bin/env python3
"""Add an unlock button to Config/Profile using the existing menu renderer."""
import hashlib
import os
import json
from pathlib import Path
import struct
import pefile

DIRECTORY = Path(__file__).resolve().parent
TARGET = Path(os.path.expanduser('~') + "/.local/share/Steam/steamapps/common/Hood Warfare 2/HW2HACKEDCLIENT/Binaries/Win64/HW2HACKEDCLIENT_internal.dll")
ORIGINAL = DIRECTORY / 'HW2HACKEDCLIENT_internal.original.dll'
EXPECTED_SIZE = 1271808

def aligned(value, alignment):
    return (value + alignment - 1) // alignment * alignment

def build(original):
    p = pefile.PE(data=original)
    assert len(original) == EXPECTED_SIZE
    # Replace only the Config/Profile Reset button's rendering call. Its return
    # value and the original Reset behavior are preserved by the callback.
    hook = 0xd51f
    assert p.get_data(hook, 5) == bytes.fromhex('e8 2c e2 ff ff')
    title_reference = 0xc0cf
    assert p.get_data(title_reference, 7) == bytes.fromhex('48 8d 1d da 05 0a 00')
    rva = aligned(p.OPTIONAL_HEADER.SizeOfImage, p.OPTIONAL_HEADER.SectionAlignment)
    code = bytearray()
    labels = {}
    fixups = []
    def emit(raw): code.extend(bytes.fromhex(raw))
    def rel(raw, target):
        emit(raw); pos = len(code); code.extend(b'\0'*4); fixups.append((pos,target))
    def label(name): labels[name] = rva + len(code)
    label('callback')
    emit('48 83 ec 48')
    rel('e8',0xb750)  # Existing Reset button, incoming RCX/XMM1 unchanged.
    emit('88 44 24 40')
    rel('48 8d 0d','button')
    emit('0f 57 c9')
    rel('e8',0xb750)
    emit('84 c0')
    rel('0f 84','status')
    rel('48 8d 0d','request_w')
    emit('ba 00 00 00 40')  # GENERIC_WRITE
    emit('41 b8 03 00 00 00 45 33 c9')  # share read/write, no security.
    emit('c7 44 24 20 02 00 00 00')  # CREATE_ALWAYS
    emit('c7 44 24 28 80 00 00 00')  # FILE_ATTRIBUTE_NORMAL
    emit('48 c7 44 24 30 00 00 00 00')
    rel('ff 15',0xa9138)  # CreateFileW
    emit('48 83 f8 ff')
    rel('0f 84','status')
    emit('48 89 c1')
    rel('ff 15',0xa9190)  # CloseHandle
    label('status')
    rel('48 8d 0d','request_a')
    rel('ff 15',0xa91c0)  # GetFileAttributesA
    emit('83 f8 ff')
    rel('0f 84','idle')
    rel('48 8d 0d','queued')
    rel('e9','text')
    label('idle')
    rel('48 8d 0d','description')
    label('text')
    emit('33 d2')
    rel('e8',0x69710)  # ImGui::TextUnformatted
    emit('0f b6 44 24 40 48 83 c4 48 c3')
    label('code_end')
    label('menu_title'); code.extend(b'HW2HACKEDCLIENT\0')
    for name, value in [('button','Local unlocks'),('description','Cloud may restore locks.'),('queued','Queued - restart HW2HACKEDCLIENT.'),('restart','Available after restarting HW2HACKEDCLIENT.'),('request_a','Z:' + os.path.expanduser('~').replace('/', '\\') + '\\HW2HACKEDCLIENT-tool-extension\\unlock.request')]:
        label(name); code.extend(value.encode() + b'\0')
    if len(code)%2: code.append(0)
    label('request_w'); code.extend(('Z:' + os.path.expanduser('~').replace('/', '\\') + '\\HW2HACKEDCLIENT-tool-extension\\unlock.request\0').encode('utf-16le'))
    while len(code)%4: code.append(0)
    label('unwind'); code.extend(bytes([1,4,1,0,4,0x82,0,0]))
    while len(code)%4: code.append(0)
    label('exception_table')
    old_directory = p.OPTIONAL_HEADER.DATA_DIRECTORY[3]
    old_table = p.get_data(old_directory.VirtualAddress, old_directory.Size)
    code.extend(old_table)
    code.extend(struct.pack('<III',labels['callback'],labels['code_end'],labels['unwind']))
    for pos, target in fixups:
        if isinstance(target,str): target=labels[target]
        struct.pack_into('<i',code,pos,target-(rva+pos+4))
    raw_offset = aligned(len(original),p.OPTIONAL_HEADER.FileAlignment)
    raw_size = aligned(len(code),p.OPTIONAL_HEADER.FileAlignment)
    header_offset = p.sections[-1].get_file_offset()+40
    assert header_offset + 40 <= p.OPTIONAL_HEADER.SizeOfHeaders
    result=bytearray(original)
    def put(offset,raw): result[offset:offset+len(raw)]=raw
    put(header_offset,struct.pack('<8sIIIIIIHHI',b'.unlock\0',len(code),rva,raw_size,raw_offset,0,0,0,0,0x60000020))
    put(p.FILE_HEADER.get_field_absolute_offset('NumberOfSections'),struct.pack('<H',len(p.sections)+1))
    put(p.OPTIONAL_HEADER.get_field_absolute_offset('SizeOfImage'),struct.pack('<I',aligned(rva+len(code),p.OPTIONAL_HEADER.SectionAlignment)))
    put(p.OPTIONAL_HEADER.get_field_absolute_offset('SizeOfCode'),struct.pack('<I',p.OPTIONAL_HEADER.SizeOfCode+raw_size))
    put(old_directory.get_file_offset(),struct.pack('<II',labels['exception_table'],len(old_table)+12))
    put(p.get_offset_from_rva(hook),b'\xe8'+struct.pack('<i',labels['callback']-hook-5))
    put(p.get_offset_from_rva(title_reference), bytes.fromhex('48 8d 1d') + struct.pack('<i', labels['menu_title']-title_reference-7))
    result.extend(b'\0'*(raw_offset-len(result)))
    result.extend(code);result.extend(b'\0'*(raw_size-len(code)))
    rebuilt=pefile.PE(data=bytes(result))
    assert len(rebuilt.DIRECTORY_ENTRY_EXCEPTION)==len(p.DIRECTORY_ENTRY_EXCEPTION)+1
    assert rebuilt.get_data(labels['callback'],4)==bytes.fromhex('48 83 ec 48')
    return bytes(result),labels

def main():
    if not ORIGINAL.exists():
        ORIGINAL.write_bytes(TARGET.read_bytes())
    patched, labels = build(ORIGINAL.read_bytes())
    TARGET.write_bytes(patched)
    manifest = {'original_sha256':hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(),'patched_sha256':hashlib.sha256(patched).hexdigest(),'hook_rva':'0xd51f','labels':{k:hex(v) for k,v in labels.items()}}
    (DIRECTORY/'patch.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Patched Config/Profile menu; original binary backed up:',ORIGINAL)

if __name__=='__main__':main()
