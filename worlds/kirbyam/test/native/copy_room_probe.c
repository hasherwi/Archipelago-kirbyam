/* Private native probe: controller input plus simulated client ownership commands.
 * Commands 1024/1025 write only the documented Copy Room request mailbox. */
#include <mgba/flags.h>
#include <mgba/core/core.h>
#include <mgba/core/blip_buf.h>
#include <mgba/core/serialize.h>
#include <mgba/core/log.h>
#include <mgba-util/vfs.h>
static struct mCore *c;
static color_t pixels[256*256];
static unsigned tick;
static void logger(struct mLogger *l,int cat,enum mLogLevel level,const char *fmt,va_list args) {
 (void)l;(void)cat;if(level&(mLOG_FATAL|mLOG_ERROR)){vfprintf(stderr,fmt,args);fputc('\n',stderr);}
}
#define R8(a) c->busRead8(c,(a))
#define R16(a) c->busRead16(c,(a))
#define R32(a) c->busRead32(c,(a))
static void report(void) {
 uint32_t pc=0;c->readRegister(c,"pc",&pc);
 printf("pc=%08x coreframe=%u ",pc,c->frameCounter(c));
 printf("frame=%u room=%u xy=%.3f,%.3f hp=%u ability=%u world18=%u\n",tick,R16(0x02020f40),(int32_t)R32(0x02020f20)/256.,(int32_t)R32(0x02020f24)/256.,R8(0x02020fe0),R8(0x02020fe3),R32(0x02028c58));
 printf("context=%u serial=%u slot=%u dirty=%u loaded=%u task=%08x bits=%08x cookie=%08x\n",R32(0x0203b13c),R32(0x0203b140),R32(0x0203b144),R32(0x0203b148),R32(0x0203b14c),R32(0x0203b150),R32(0x0203b154),R32(0x0203b158));
 printf("save_id=%u words22..26=%08x,%08x,%08x,%08x,%08x\n",R16(0x0203ad48),R32(0x02028c68),R32(0x02028c6c),R32(0x02028c70),R32(0x02028c74),R32(0x02028c78));
}
static void observe(void) {
 static uint32_t prevroom=~0u,prevflag=~0u;
 if(R16(0x02020f40)!=prevroom || R32(0x02028c58)!=prevflag) {
  report();prevroom=R16(0x02020f40);prevflag=R32(0x02028c58);
 }

}
int main(int argc,char**argv) {
 if(argc!=5)return 2; /* ROM, input state, output state, image */
 struct mLogger log={.log=logger,.filter=NULL};mLogSetDefaultLogger(&log);
 c=mCoreFind(argv[1]);if(!c||!c->init(c))return 3;
 mCoreInitConfig(c,"isolated-copy-room-access");
 mCoreConfigSetIntValue(&c->config,"useBios",0);mCoreConfigSetIntValue(&c->config,"skipBios",1);
 c->loadConfig(c,&c->config);c->setVideoBuffer(c,pixels,256);
 if(!mCoreLoadFile(c,argv[1]))return 4;
 struct VFile *v;
 if(!strncmp(argv[2],"cold:",5)) {
  if(!mCoreLoadSaveFile(c,argv[2]+5,true))return 5;
  c->reset(c);
 } else {
  c->reset(c);
  v=VFileOpen(argv[2],O_RDONLY);if(!v||!mCoreLoadStateNamed(c,v,SAVESTATE_ALL))return 5;v->close(v);
 }
 blip_set_rates(c->getAudioChannel(c,0),16777216,32768);blip_set_rates(c->getAudioChannel(c,1),16777216,32768);
 observe();unsigned keys,frames;
 while(scanf("%u %u",&keys,&frames)==2) {
  if(keys==1024 || keys==1025) {
   c->busWrite32(c,0x0203b164,keys-1024);
   c->busWrite32(c,0x0203b160,R32(0x0203b13c));
   keys=0;
  }
  if(keys>1023||frames>36000)return 6;
  c->setKeys(c,keys);
  for(unsigned j=0;j<frames;j++) {c->runFrame(c);++tick;blip_clear(c->getAudioChannel(c,0));blip_clear(c->getAudioChannel(c,1));observe();}
  report();fflush(stdout);
 }
 c->setKeys(c,0);
 void *sram=NULL;size_t size=c->savedataClone(c,&sram);
 char path[4096];snprintf(path,sizeof(path),"%s.sav",argv[3]);
 FILE *sf=fopen(path,"wb");if(!sf||!size||!sram)return 9;
 if(fwrite(sram,1,size,sf)!=size)return 10;
 fclose(sf);free(sram);
 v=VFileOpen(argv[3],O_WRONLY|O_CREAT|O_TRUNC);if(!v||!mCoreSaveStateNamed(c,v,SAVESTATE_ALL))return 7;v->close(v);
 FILE *f=fopen(argv[4],"wb");if(!f)return 8;fprintf(f,"P6\n240 160\n255\n");
 for(unsigned y=0;y<160;y++)for(unsigned x=0;x<240;x++){color_t p=pixels[y*256+x];unsigned char rgb[]={p&255,(p>>8)&255,(p>>16)&255};fwrite(rgb,1,3,f);}
 fclose(f);
 c->unloadROM(c);mCoreConfigDeinit(&c->config);c->deinit(c);return 0;
}
