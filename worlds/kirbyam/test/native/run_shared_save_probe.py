from pathlib import Path
import bsdiff4,subprocess,struct,json
import argparse
parser=argparse.ArgumentParser(description="Private native single-save acceptance; never commit outputs")
parser.add_argument('--rom',type=Path,required=True)
parser.add_argument('--observer',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
p=args.output.resolve();p.mkdir(parents=True,exist_ok=True)
d=p/'private';d.mkdir(exist_ok=True)
w=Path(__file__).resolve().parents[2]
clean=args.rom.read_bytes()
rom=bytearray(bsdiff4.patch(clean,(w/'data/base_patch.bsdiff4').read_bytes()))
rom[0xf00000:0xf00010]=bytes(range(1,17));(d/'single.gba').write_bytes(rom)
commands='0 180\n8 1\n0 120\n8 1\n0 240\n64 1\n0 1\n64 1\n0 1\n1 1\n0 120\n1 1\n0 240\n'
def run(name,save,rompath=d/'single.gba',inputs=commands):
 (d/(name+'.input.sav')).write_bytes(save)
 r=subprocess.run([str(args.observer.resolve()),str(rompath),'cold:'+str(d/(name+'.input.sav')),str(d/(name+'.ss1')),str(d/(name+'.ppm'))],input=inputs,text=True,capture_output=True)
 (p/(name+'.log')).write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr
 assert 'context=1 serial=1 slot=0 dirty=0 loaded=0' in r.stdout,r.stdout[-1500:]
 return (d/(name+'.ss1.sav')).read_bytes()
def checksum(b):
 s=sum(struct.unpack('<'+'H'*(len(b)//2),b))&65535
 return struct.pack('<4H',s,s^65535,(-s)&65535,0)
stride=4884 # 780 native +4096 extra +8 checksum
end=24+2*stride
blank=bytes([255])*32768
fresh=run('single-fresh',blank)
assert fresh[end:]==blank[end:],'neighbor SRAM touched'
def data(b,c):return b[24+c*stride+8:24+(c+1)*stride]
for c in range(2):assert checksum(data(fresh,c))==fresh[24+c*stride:32+c*stride]
resume=run('single-resume',fresh)
assert resume==fresh
# Authenticated extension payload plus feature flags in native save fixture.
pattern=bytes((i*37)&255 for i in range(4096));cached=bytearray(fresh)
for c in range(2):
 b=bytearray(data(fresh,c));b[780:]=pattern;struct.pack_into('<I',b,136,0x41530081)
 # Synthetic native progress fixture: Hub record, chest, shard, owned paint.
 b[140:156]=bytes(range(1,17));struct.pack_into('<I',b,156,0x48530003)
 b[734]=1;b[734+16]=1;struct.pack_into('<I',b,734+20,1<<5)
 struct.pack_into('<H',b,734+34,0xC65A)
 cached[24+c*stride:24+(c+1)*stride]=checksum(b)+b
for name,corrupt in [('cached',None),('primary-recovery',0),('backup-survival',1)]:
 inp=bytearray(cached)
 if corrupt is not None:inp[24+corrupt*stride+8+780]^=1
 saved=run('single-'+name,inp)
 assert data(saved,0)[780:]==pattern
 assert data(saved,0)[140:160]==data(cached,0)[140:160]
 assert data(saved,0)[734:770]==data(cached,0)[734:770]
 assert struct.unpack_from('<I',data(saved,0),136)[0]==0x41530081
 assert saved[end:]==blank[end:]
 if corrupt==0:assert data(saved,0)==data(saved,1)
other=bytearray(rom);other[0xf0000f]^=1;(d/'single-other.gba').write_bytes(other)
saved=run('single-other',cached,d/'single-other.gba')
for c in range(2):
 assert data(saved,c)[780:]==bytes(4096)
 assert struct.unpack_from('<I',data(saved,c),136)[0]==0x41500000
 assert checksum(data(saved,c))==saved[24+c*stride:32+c*stride]
# Controller reset and return through the title, then same-save re-entry.
reset_save=run('single-reset',cached,inputs=commands+'15 60\n'+commands)
assert 'context=2 serial=2 slot=0 dirty=0 loaded=0' in (p/'single-reset.log').read_text()
print('PASS blank SRAM, continue, full 4096-byte persistence, primary recovery, valid-primary/invalid-backup load, checksum coverage, neighboring SRAM, seed isolation, controller reset/re-entry')
