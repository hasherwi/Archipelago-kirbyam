/* Synthetic instructions/address space only. C callees are hostile ABI stubs;
 * shipping C/state semantics are exercised separately by mapped host tests. */
#include <mgba/flags.h>
#include <mgba/core/core.h>
#include <mgba/gba/core.h>
#include <mgba/internal/arm/arm.h>
#include <mgba/internal/arm/isa-inlines.h>
#include <mgba-util/vfs.h>
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#define STACK 0x03007000u
#define DATA 0x02018000u
#define BASE 0x0201F000u
struct Site {uint32_t pc; uint16_t a,b; unsigned addr,out; int op;};
static const struct Site sites[]={
 {0x080339FE,0x7800,0x7330,0,0,-1},{0x08033F06,0x7812,0x4290,2,2,-1},
 {0x08034000,0x7818,0x7328,3,0,-1},{0x0803411C,0x7820,0x4281,4,0,-1},
 {0x0803415A,0x7820,0x7330,4,0,-1},{0x08034D9A,0x7800,0x2801,0,0,-1},
 {0x0804FFE4,0x2003,0x7008,1,0,0},{0x080501AC,0x2003,0x7020,4,0,0},
 {0x080501BA,0x2001,0x7020,4,0,1},{0x0805082C,0x2001,0x7008,1,0,1},
 {0x0805735A,0x3901,0x7001,0,1,2},{0x081231F2,0x3001,0x7008,1,0,3},
 {0x0801B2E2,0x3001,0x7008,1,0,3}};
static void jump(struct ARMCore*c,uint32_t a){c->gprs[15]=a&~1u;_ARMSetMode(c,(a&1)?MODE_THUMB:MODE_ARM);if(a&1)ThumbWritePC(c);else ARMWritePC(c);}
static uint32_t pc(struct ARMCore*c){return c->gprs[15]-(c->cpsr.t?2:4);}
static void setup(struct mCore*m,const struct Site*s,unsigned flags,unsigned value){
 m->reset(m);struct ARMCore*c=m->cpu;
 for(unsigned i=0;i<13;i++)c->gprs[i]=0x12340000+i*0x123;
 c->gprs[5]=DATA+0x100;c->gprs[6]=DATA+0x200;c->gprs[s->addr]=DATA;
 if(s->op>=0)c->gprs[s->out]=value;
 c->gprs[13]=STACK;c->gprs[14]=0x08001235;
 c->cpsr.n=!!(flags&8);c->cpsr.z=!!(flags&4);c->cpsr.c=!!(flags&2);c->cpsr.v=!!(flags&1);
 m->busWrite8(m,DATA,value);m->busWrite8(m,DATA+0x10C,99);m->busWrite8(m,DATA+0x20C,99);
 for(unsigned a=STACK-96;a<STACK+16;a+=4)m->busWrite32(m,a,0xABCD1234);
}
int main(int argc,char**argv){
 assert(argc==4);uint32_t visible=strtoul(argv[1],0,0),native=strtoul(argv[2],0,0);
 size_t size=0x1010000;unsigned char*rom=malloc(size);assert(rom&&fread(rom,1,size,stdin)==size);
 struct mCore*m=GBACoreCreate();assert(m&&m->init(m));mCoreInitConfig(m,"battery-abi-only");assert(m->loadROM(m,VFileFromMemory(rom,size)));
 const unsigned values[]={0,1,2,3,254,255};unsigned cases=0;
 for(unsigned i=0;i<13;i++)for(unsigned f=0;f<16;f++)for(unsigned v=0;v<6;v++)for(unsigned masked=0;masked<2;masked++){
  const struct Site*s=&sites[i];unsigned value=values[v];
  if(s->op==1)value=0; if(s->op==2&&value==0)value=1;if(s->op==3)value%=3;
  unsigned result=s->op==0?3:s->op==1?1:s->op==2?value-1:s->op==3?value+1:masked?0:value;
  setup(m,s,f,s->op<0?result:value);struct ARMCore*c=m->cpu;
  m->busWrite16(m,BASE,s->a);m->busWrite16(m,BASE+2,s->b);jump(c,BASE|1);m->step(m);m->step(m);
  uint32_t regs[15];for(unsigned r=0;r<15;r++)regs[r]=c->gprs[r];uint32_t flags=c->cpsr.packed&0xF0000000u;
  unsigned cache1=m->busRead8(m,DATA+0x10C),cache2=m->busRead8(m,DATA+0x20C);
  /* Saturated wide decrement changes the proxy result, not displaced SUBS flags. */
  if(s->op==2&&value==255&&masked)result=255;
  regs[s->out]=result;
  setup(m,s,f,value);jump(c,s->pc|1);unsigned calls=0,steps=0;
  while(pc(c)!=s->pc+4&&steps++<200){
   if(pc(c)==(s->op<0?visible:native)){
    assert((uint32_t)c->gprs[0]==DATA);if(s->op>=0)assert(c->gprs[1]==s->op);
    uint32_t lr=c->gprs[14];assert(c->gprs[13]==STACK-64);
    c->gprs[0]=result;for(unsigned r=1;r<4;r++)c->gprs[r]=0xDEAD0000+r;c->gprs[12]=0xBAD0000C;
    c->cpsr.n=c->cpsr.z=c->cpsr.c=c->cpsr.v=1;
    if(s->op>=0)m->busWrite8(m,DATA,result);
    jump(c,lr);calls++;
   }else m->step(m);
  }
  assert(steps<200&&calls==1&&c->cpsr.t);
  for(unsigned r=0;r<14;r++)assert((uint32_t)c->gprs[r]==regs[r]);
  assert((c->cpsr.packed&0xF0000000u)==flags);
  assert(m->busRead8(m,DATA+0x10C)==cache1&&m->busRead8(m,DATA+0x20C)==cache2);
  assert(m->busRead32(m,STACK)==0xABCD1234&&m->busRead32(m,STACK-68)==0xABCD1234);
  cases++;
 }
 /* Unknown direct entry is not a recognized native hook: preserve all state
  * and return without calling either C consumer. */
 for(unsigned f=0;f<16;f++) {
  setup(m,&sites[0],f,7); struct ARMCore*c=m->cpu;
  uint32_t regs[14];for(unsigned r=0;r<14;r++)regs[r]=c->gprs[r];
  uint32_t flags=c->cpsr.packed&0xF0000000u;c->gprs[14]=BASE|1;
  jump(c,strtoul(argv[3],0,0)|1); unsigned steps=0;
  while(pc(c)!=BASE&&steps++<200) {assert(pc(c)!=visible&&pc(c)!=native);m->step(m);}
  assert(steps<200);for(unsigned r=0;r<14;r++)assert((uint32_t)c->gprs[r]==regs[r]);
  assert((c->cpsr.packed&0xF0000000u)==flags);
 }
 m->unloadROM(m);mCoreConfigDeinit(&m->config);m->deinit(m);free(rom);printf("Battery ABI: %u cases passed\n",cases);return 0;
}
