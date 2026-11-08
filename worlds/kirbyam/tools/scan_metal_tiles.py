"""Read-only USA KATAM collision inventory. Emits coordinates, not ROM assets.
Usage: python scan_metal_tiles.py PRIVATE_ROM OUTPUT_JSON
F5 ordinary metal; F7 category-4 blocks (reinforced candidate); F6 separately
recorded category-3/hammer-trigger tiles. This does not prove traversal.
"""
import sys,json,hashlib,struct
from pathlib import Path
ROOM_PROPS=0x9331AC
FOREGROUND_TABLE=0xD64520
SOLIDITY_TABLE=0xD63330
COLLISION_ATTRIBUTES=0x2D88B8
USA_SHA1='274b102b6d940f46861a92b4e65f89a51815c12c'
def unpack(rom,fmt,offset):return struct.unpack_from(fmt,rom,offset)
def pointer(rom,offset):
 p=unpack(rom,'<I',offset)[0]-0x08000000
 if not 0<=p<len(rom):raise ValueError('Invalid pointer')
 return p
def decompress_rl(rom: bytes, offset: int, expected: int) -> bytes:
    header = unpack(rom, '<I', offset)[0]
    if header & 255 != 0x30 or header >> 8 != expected or not 0 < expected <= 0x2000:
        raise ValueError('Unsupported RL header or dimensions')
    cursor = offset + 4
    result = bytearray()
    while len(result) < expected:
        control = unpack(rom, '<B', cursor)[0]
        cursor += 1
        count = (control & 127) + (3 if control & 128 else 1)
        if len(result) + count > expected:
            raise ValueError('RL output overrun')
        if control & 128:
            result.extend([unpack(rom, '<B', cursor)[0]] * count)
            cursor += 1
        else:
            result.extend(unpack(rom, f'<{count}B', cursor))
            cursor += count
    return bytes(result)


def records(rom: bytes, cursor: int) -> list[dict[str, int]]:
    result: list[dict[str, int]] = []
    for _ in range(4096):
        if unpack(rom, '<B', cursor)[0] == 0:
            return result
        kind, attribute, x, y, size = unpack(rom, '<4BH', cursor)
        if size != {1: 18, 2: 14, 3: 14}.get(kind):
            raise ValueError('Unsupported solidity record')
        unpack(rom, f'<{size}x', cursor)
        result.append(dict(offset=cursor, kind=kind, attribute=attribute, x=x, y=y))
        cursor += size
    raise ValueError('Unterminated solidity list')


r=Path(sys.argv[1]).read_bytes();assert len(r)==0x1000000 and hashlib.sha1(r).hexdigest()==USA_SHA1
attrs={i:unpack(r,'<I',COLLISION_ATTRIBUTES+i*4)[0] for i in range(256)}

out={'sha1':USA_SHA1,'count':0x9998//40,'attributes':{hex(i):hex(a) for i,a in attrs.items()},'rooms':[],'errors':[],'unused_slots':[]}
for room in range(out['count']):
 try:
  p=unpack(r,'<20H',ROOM_PROPS+room*40)
  if p==tuple([65535]*19+[0]):
   out['unused_slots'].append(room);continue
  if p[12]>=287 or p[13]>=287:raise ValueError('index out of range')
  fg=pointer(r,FOREGROUND_TABLE+p[12]*4);w,h=unpack(r,'<HH',fg);w//=2;h//=2
  s=pointer(r,SOLIDITY_TABLE+p[13]*4);g=decompress_rl(r,pointer(r,s),w*h);rec=records(r,pointer(r,s+4))
  tiles=[{'x':i%w,'y':i//w,'tile':hex(v)} for i,v in enumerate(g) if v in (0xf5,0xf6,0xf7)]
  dyn=[]
  for e in rec:
   a=e['attribute'];replacement=unpack(r,'<B',e['offset']+(16 if e['kind']==1 else 12))[0] if e['kind'] in (1,2) else None
   if a in (0xf5,0xf6,0xf7) or (replacement is not None and replacement in (0xf5,0xf6,0xf7)):
    dyn.append(dict(e,replacement=replacement))
  out['rooms'].append({'room':room,'properties':list(p),'width':w,'height':h,'tiles':tiles,'records':dyn})
 except Exception as e:out['errors'].append({'room':room,'error':str(e)})
out['valid_room_ids']=[e['room'] for e in out['rooms']]
for e in out['rooms']:e.pop('properties')
out['rooms']=[e for e in out['rooms'] if e['tiles'] or e['records']]
out['attributes']={hex(i):hex(attrs[i]) for i in (0xf5,0xf6,0xf7)}
Path(sys.argv[2]).write_text(json.dumps(out,separators=(',',':'))+'\n')
assert not out["errors"],out["errors"]
assert len(out["valid_room_ids"])+len(out["unused_slots"])==983
