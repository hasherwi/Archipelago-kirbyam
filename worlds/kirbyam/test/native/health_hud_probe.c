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
static void invoke(struct mCore*c,unsigned entry,unsigned stop,int hp,int max,int demo){
 struct ARMCore*cpu=c->cpu;c->busWrite8(c,0x02020FE0,hp);c->busWrite8(c,0x02020FE1,max);c->busWrite32(c,0x0203AD10,demo);
 cpu->gprs[0]=0x02020EE0;cpu->gprs[13]=0x03007000;cpu->gprs[14]=0x02010001;cpu->gprs[15]=entry;
 for(int r=4;r<=11;r++)cpu->gprs[r]=0x12340000+r;
 _ARMSetMode(cpu,MODE_THUMB);ThumbWritePC(cpu);unsigned n=0;
 while(cpu->gprs[15]!=stop+2 && n++<4000)c->step(c);
 assert(n<4000);assert(cpu->gprs[13]==0x03007000);
 for(int r=4;r<=11;r++)assert(cpu->gprs[r]==0x12340000+r);
 assert(c->busRead8(c,0x02020FE0)==(unsigned char)hp);assert(c->busRead8(c,0x02020FE1)==(unsigned char)max);
}
static void fill(struct mCore*c){
 for(unsigned a=0x0600E400;a<0x0600E540;a+=2)c->busWrite16(c,a,0xABCD);
 for(unsigned i=0;i<6;i++){c->busWrite16(c,0x0600E49A+i*2,0x184);c->busWrite16(c,0x0600E4DA+i*2,0x184);}
}
static void snapshot(struct mCore*c,unsigned char*b){for(unsigned i=0;i<0x140;i++)b[i]=c->busRead8(c,0x0600E400+i);}
int main(void){
 unsigned char*rom=malloc(0x1000000);assert(fread(rom,1,0x1000000,stdin)==0x1000000);
 struct mCore*c=GBACoreCreate();assert(c&&c->init(c));mCoreInitConfig(c,"isolated-hud-matrix");assert(c->loadROM(c,VFileFromMemory(rom,0x1000000)));c->reset(c);
 unsigned sites[]={0x080339B2,0x08033BF2,0x08035A62};unsigned char expected[0x140],actual[0x140];unsigned cases=0;
 for(int s=0;s<3;s++)for(int old=1;old<=10;old++)for(int cap=1;cap<=10;cap++)for(int h=-3;h<=cap;h++){
  int hp=h==-3?-128:h==-2?-1:h==-1?0:h;
  fill(c);invoke(c,0x0803518C,0x02010000,hp,cap,0);snapshot(c,expected);
  fill(c);invoke(c,0x0803518C,0x02010000,old,old,0);
  invoke(c,sites[s],sites[s]+4,hp,cap,0);snapshot(c,actual);
  if(memcmp(expected,actual,sizeof actual)){fprintf(stderr,"MISMATCH site=%x old=%d max=%d hp=%d\n",sites[s],old,cap,hp);return 1;}
  invoke(c,sites[s],sites[s]+4,hp,cap,0);snapshot(c,actual);assert(!memcmp(expected,actual,sizeof actual));cases++;
 }
 for(int s=0;s<3;s++){fill(c);snapshot(c,expected);invoke(c,sites[s],sites[s]+4,4,4,0x10);snapshot(c,actual);assert(!memcmp(expected,actual,sizeof actual));}
 printf("PASS %u actual-instruction transitions; 3 callsites; capacities1..10; dead/zero/damaged/full HP; repeat redraw; callee registers/SP; neighboring tile preservation; 3 demo-mode no-write cases\n",cases);
 c->unloadROM(c);mCoreConfigDeinit(&c->config);c->deinit(c);free(rom);
}
