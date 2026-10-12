/* Optional isolated instruction/save probe. No game session, ROM output or save file. */
#include <mgba/flags.h>
#include <mgba/core/core.h>
#include <mgba/gba/core.h>
#include <mgba/internal/arm/arm.h>
#include <mgba/internal/arm/isa-inlines.h>
#include <mgba-util/vfs.h>
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned start_calls;
static unsigned call(struct mCore*c,unsigned entry,unsigned a,unsigned b,unsigned d){
 struct ARMCore*cpu=c->cpu;cpu->gprs[0]=a;cpu->gprs[1]=b;cpu->gprs[2]=d;cpu->gprs[3]=0x02018000;
 cpu->gprs[13]=0x03007000;cpu->gprs[14]=0x0201F001;cpu->gprs[15]=entry;
 c->busWrite32(c,0x03007000,0x02018010);
 for(int r=4;r<=11;r++)cpu->gprs[r]=0x12340000+r;
 _ARMSetMode(cpu,MODE_THUMB);ThumbWritePC(cpu);unsigned n=0;
 while(cpu->gprs[15]!=0x0201F002 && n++<300000){
  /* Startup's scene construction is intentionally an IO stand-in; inspect its ABI. */
  if(cpu->gprs[15]==0x080332BE){
   assert(cpu->gprs[0]==1&&cpu->gprs[1]==0&&cpu->gprs[2]==0x02018000&&cpu->gprs[3]==0x02018000);
   assert(c->busRead32(c,cpu->gprs[13])==0x02018010);start_calls++;
   cpu->gprs[15]=cpu->gprs[14]&~1;ThumbWritePC(cpu);
  }else c->step(c);
 }
 if(n>=300000){fprintf(stderr,"timeout %x pc=%x\n",entry,cpu->gprs[15]);exit(2);}
 assert(cpu->gprs[13]==0x03007000);
 for(int r=4;r<=11;r++)assert(cpu->gprs[r]==0x12340000+r);
 return cpu->gprs[0];
}
static void ready(struct mCore*c){
 c->busWrite32(c,0x03003674,0x083B909C); /* native Init sprite table */
 c->busWrite32(c,0x03000010,0x03001000);c->busWrite32(c,0x03001008,0x08033B9D);
 c->busWrite16(c,0x03001006,0x2000);
 c->busWrite32(c,0x02020FAC,0x03001200);c->busWrite8(c,0x02020FE3,0);
 c->busWrite32(c,0x0203AD10,0);c->busWrite8(c,0x0203AD3C,0);
 c->busWrite16(c,0x030024E8,0);c->busWrite16(c,0x030024EC,0);
 c->busWrite32(c,0x03002440,0);c->busWrite32(c,0x0203B040,0x4B41504D);
 c->busWrite32(c,0x0203B0B8,0);c->busWrite32(c,0x0203B004,0);
}
int main(int argc,char**argv){
 assert(argc==4);unsigned poll=strtoul(argv[1],0,0),menu_hook=strtoul(argv[2],0,0),start=strtoul(argv[3],0,0);
 unsigned char*rom=malloc(0x1000000);assert(fread(rom,1,0x1000000,stdin)==0x1000000);
 struct mCore*c=GBACoreCreate();assert(c&&c->init(c));mCoreInitConfig(c,"isolated-color-save-probe");assert(c->loadROM(c,VFileFromMemory(rom,0x1000000)));c->reset(c);
 unsigned bg=c->busRead32(c,0x0803D248),backup=c->busRead32(c,0x0803D24C);
 unsigned transitions=0;
 const unsigned abilities[]={0,1,14,20};
 for(unsigned ability_i=0;ability_i<4;ability_i++)for(unsigned old=0;old<14;old++)for(unsigned next=0;next<14;next++)if(old!=next){
  ready(c);c->busWrite8(c,0x02020FE3,abilities[ability_i]);
  c->busWrite8(c,0x02020FBF,next);call(c,0x0803E558,0,0,0);
  unsigned expected_obj[16],expected_backup[16];
  for(unsigned i=0;i<16;i++){expected_obj[i]=c->busRead16(c,0x03002c60+2*i);expected_backup[i]=c->busRead16(c,0x02022320+2*i);}
  c->busWrite8(c,0x02020FBF,old);call(c,0x0803E558,0,0,0);call(c,0x08035FDC,0,0,0);
  c->rawWrite32(c,0x0815F694,-1,0xC0100100|old);
  c->busWrite32(c,0x0203B050,next);
  c->busWrite32(c,0x02038974,0x3fff);c->busWrite16(c,0x02038982,0xC600|(old<<4)|(old^15));
  call(c,poll,0,0,0);assert(c->busRead8(c,0x02020FBF)==next);
  assert(c->busRead32(c,0x0203B0B8)==1&&(c->busRead32(c,0x03002440)&1));
  for(unsigned i=0;i<16;i++){assert(c->busRead16(c,0x03002c60+2*i)==expected_obj[i]);assert(c->busRead16(c,0x02022320+2*i)==expected_backup[i]);}
  for(unsigned i=0;i<16;i++){
   unsigned expected=c->busRead16(c,0x0834BB20+32*next+2*i);
   assert(c->busRead16(c,bg+0x1e0+2*i)==expected&&c->busRead16(c,backup+0x1e0+2*i)==expected);
  }
  /* No repeated update without a new request, including Pink. */
  c->busWrite32(c,0x03002440,0);call(c,poll,0,0,0);assert(!(c->busRead32(c,0x03002440)&1));
  transitions++;
 }
 unsigned saves=0;unsigned char sram_before[0x8000];
 for(unsigned slot=0;slot<3;slot++)for(unsigned color=0;color<14;color++){
  ready(c);c->busWrite16(c,0x0203AD48,slot);c->busWrite16(c,0x02038982,0);
  c->busWrite32(c,0x02038974,1u<<color);c->busWrite16(c,0x030039FC,1);
  unsigned index=0;for(;index<40;index++)if(c->busRead16(c,0x08386A50+4*index)==0x101+color)break;assert(index<40);
  c->busWrite8(c,0x0201002A,index);c->busWrite8(c,0x02010002+index,1);c->busWrite8(c,0x02010001,color);
  for(unsigned i=0;i<0x8000;i++)sram_before[i]=c->busRead8(c,0x0E000000+i);
  /* Invoke the resolved payload wrapper and its native handler/serializer.
   * The patched caller encoding is checked separately; this is not menu traversal. */
  call(c,menu_hook,0x02010000,0,0);
  unsigned marker=0xC600|(color<<4)|(color^15),base=0x18+slot*0x628;
  assert(c->busRead16(c,0x02038982)==marker);
  for(unsigned i=0;i<0x314;i++)assert(c->busRead8(c,0x0E000000+base+i)==c->busRead8(c,0x0E000000+base+0x314+i));
  for(unsigned i=0;i<0x8000;i++)if(i<base||i>=base+0x628)assert(c->busRead8(c,0x0E000000+i)==sram_before[i]);
  c->reset(c); /* actual EWRAM reset, same disposable SRAM */
  assert((int16_t)call(c,0x0800A91C,1,slot,0)==0); /* native checksum verify + load */
  assert(c->busRead16(c,0x02038982)==marker&&c->busRead32(c,0x02038974)==(1u<<color));
  ready(c);c->busWrite32(c,0x0203B040,0);c->rawWrite32(c,0x0815F694,-1,0xC0100000|((color+1)%14));
  call(c,start,1,0,0x02018000);
  assert(c->busRead8(c,0x0203AD1C)==color&&c->busRead16(c,0x0203ADE0)==color);
  /* Corrupt primary only, verify native recovery from the backup copy. */
  c->busWrite8(c,0x0E000000+base,c->busRead8(c,0x0E000000+base)^1);
  c->busWrite16(c,0x02038982,0);assert((int16_t)call(c,0x0800A91C,1,slot,0)==0);
  assert(c->busRead16(c,0x02038982)==marker);saves++;
 }
 assert(start_calls==42);
 printf("PASS %u packaged-payload color transitions including Pink; 42 owned paints/3 slots with native checksums, both SRAM copies, cold-reset load and primary-corruption backup recovery; other slots preserved; startup ABI checked with scene-construction stand-in. No gameplay/save files.\n",transitions);
 c->unloadROM(c);mCoreConfigDeinit(&c->config);c->deinit(c);free(rom);return 0;
}
