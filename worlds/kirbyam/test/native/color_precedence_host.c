/* Appended to actual shipping C by test_color_precedence.py; IO only is stubbed. */
#define CHECK(c) do {if(!(c)){printf("failed line %d\n",__LINE__);return 1;}}while(0)
static unsigned transform_calls;
static void transform_bg(const uint16_t *p,uint8_t index,uint16_t count){
 if(p!=(const uint16_t*)0x02022300u||index!=240||count!=16)abort();
 transform_calls++;
}
static unsigned obj_calls,bg_calls,save_calls,start_calls,menu_calls,bad_io;
static uint16_t slots[3], bg[16], bg_backup[16];
static uint8_t obj_color;
static void refresh_obj(uint8_t player){if(player!=0)bad_io++;obj_calls++;obj_color=*(uint8_t*)0x02020FBF;}
static void load_bg(const uint16_t *p,uint8_t index,uint16_t count){
 if(index!=240||count!=16)bad_io++;
 memcpy(bg,p,32);memcpy(bg_backup,p,32);bg_calls++;
}
static void start_game(uint8_t mode,uint8_t arg,const uint16_t*r,const int32_t*p,const uint32_t*f){
 if(mode!=1||arg||r!=(void*)0x20||p!=(void*)0x30||f!=(void*)0x40)bad_io++;
 *(uint8_t*)0x02020FBF=KIRBY_PLAYER_COLOR_TABLE[0];start_calls++;
}
static uint32_t menu_select(uint8_t*m){(void)m;menu_calls++;return 77;}
static int16_t save_world(uint32_t type,uint16_t slot){
 if(type!=1||slot>2){bad_io++;return -1;}slots[slot]=AP_SAVED_PAINT_CHOICE;save_calls++;return 0;
}
static void ready(void){
 KIRBY_HUD_TASK=0x03001000;*(uint32_t*)0x03001008=0x08033B9D;
 *(uint32_t*)(KIRBY_STRUCTS_ADDR+KIRBY_STRUCT_TASK_OFFSET)=0x03001200;
 *(uint8_t*)(KIRBY_STRUCTS_ADDR+KIRBY_STRUCT_ABILITY_OFFSET)=0;
 KIRBY_MAIN_FLAGS=0x1000;KIRBY_BLD_CONTROL=0;KIRBY_BLD_Y=0;
 DEMO_PLAYBACK_FLAGS=0;KIRBY_CURRENT_PLAYER=0;
 AP_STARTING_KIRBY_COLOR_APPLIED=0;obj_calls=bg_calls=0;
}
int main(void){
 CHECK(mmap((void*)0x02000000,0x40000,3,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void*)0x02000000);
 CHECK(mmap((void*)0x03000000,0x8000,3,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void*)0x03000000);
 CHECK(mmap((void*)0x08000000,0x1000000,3,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void*)0x08000000);
 for(unsigned c=0;c<14;c++)for(unsigned i=0;i<16;i++)((uint16_t*)0x0834BB20)[c*16+i]=c*100+i;
 unsigned cases=0;
 for(unsigned seed=0;seed<19;seed++)for(unsigned mode=0;mode<2;mode++)
 for(unsigned choice=0;choice<15;choice++)for(unsigned owned=0;owned<2;owned++)
 for(unsigned runtime=0;runtime<20;runtime++)for(unsigned cookie=0;cookie<2;cookie++){
  ready();gApStartingKirbyColorInitial=AP_COLOR_CONFIG_MAGIC|(mode<<8)|seed;
  AP_MAILBOX_INIT_COOKIE=cookie?AP_MAILBOX_INIT_COOKIE_VALUE:0;
  AP_STARTING_KIRBY_COLOR_ID=runtime<19?runtime:0xffffffff;
  AP_SAVED_PAINT_CHOICE=choice<14?ap_color_choice_encode(choice):0;
  uint16_t marker=AP_SAVED_PAINT_CHOICE;
  KIRBY_SPRAY_PAINT_FLAGS=owned?0x3fff:0;
  unsigned expected=!mode&&choice<14&&owned?choice:cookie&&runtime<19?runtime:seed;
  CHECK(ap_get_effective_starting_kirby_color()==expected);
  ap_on_start_single_player_game(1,0,(void*)0x20,(void*)0x30,(void*)0x40);
  unsigned native_expected=expected<14?expected:0;
  CHECK(KIRBY_SELECTED_COLOR==native_expected&&KIRBY_PLAYER_COLOR_TABLE[0]==native_expected&&*(uint8_t*)0x02020FBF==native_expected);
  CHECK(AP_STARTING_KIRBY_COLOR_APPLIED==0);
  ap_apply_starting_kirby_color_config();
  CHECK(obj_calls==1&&bg_calls==1&&obj_color==native_expected&&AP_STARTING_KIRBY_COLOR_APPLIED==1);
  CHECK(KIRBY_MAIN_FLAGS==0x1001&&bg[0]==native_expected*100&&!memcmp(bg,bg_backup,32));
  CHECK(AP_SAVED_PAINT_CHOICE==marker&&KIRBY_SPRAY_PAINT_FLAGS==(owned?0x3fff:0));
  ap_apply_starting_kirby_color_config();CHECK(obj_calls==1&&bg_calls==1);cases++;
 }
 /* Reject malformed legacy padding and unowned selections. */
 for(unsigned v=0;v<65536;v++){
  unsigned c=(v>>4)&15;
  CHECK(ap_color_choice_decode(v,0)==AP_COLOR_INVALID);
  CHECK(ap_color_choice_decode(v,0xffff)==(c<14&&v==ap_color_choice_encode(c)?c:AP_COLOR_INVALID));
 }
 /* Mode metadata does not reinterpret old 0..13 ROM color words. */
 for(unsigned c=0;c<14;c++){CHECK(ap_color_initial(c)==c);CHECK(!ap_color_per_room(c));}
 CHECK(ap_color_initial(0xffffffff)==0);
 uint8_t *menu=(uint8_t*)0x02010000;
 for(unsigned slot=0;slot<3;slot++)for(unsigned c=0;c<14;c++){
  KIRBY_SAVE_ID=slot;KIRBY_PRESSED_KEYS=1;menu[0x2A]=1;menu[3]=1;
  ((uint16_t*)0x08386A50)[2]=0x101+c;menu[1]=c; /* same as AP default still explicit */
  KIRBY_SPRAY_PAINT_FLAGS=1u<<c;AP_SAVED_PAINT_CHOICE=0;unsigned saves=save_calls;
  CHECK(ap_on_treasure_paint_selection(menu)==77);
  CHECK(AP_SAVED_PAINT_CHOICE==ap_color_choice_encode(c)&&slots[slot]==AP_SAVED_PAINT_CHOICE);
  CHECK(save_calls==saves+1&&KIRBY_SPRAY_PAINT_FLAGS==(1u<<c));
  ap_on_treasure_paint_selection(menu);CHECK(save_calls==saves+1);
  /* Synthetic file load restores only the marker; native roundtrip tested separately. */
  AP_SAVED_PAINT_CHOICE=0;AP_MAILBOX_INIT_COOKIE=0;AP_SAVED_PAINT_CHOICE=slots[slot];
  gApStartingKirbyColorInitial=AP_COLOR_CONFIG_MAGIC|((c+1)%14);
  CHECK(ap_get_effective_starting_kirby_color()==c);
  KIRBY_SPRAY_PAINT_FLAGS=0;ap_on_treasure_paint_selection(menu);CHECK(save_calls==saves+1);
  KIRBY_PRESSED_KEYS=0;KIRBY_SPRAY_PAINT_FLAGS=1u<<c;AP_SAVED_PAINT_CHOICE=0;
  ap_on_treasure_paint_selection(menu);CHECK(save_calls==saves+1&&AP_SAVED_PAINT_CHOICE==0);
 }
 /* Uncollected default swatch clears preference without granting any paint. */
 KIRBY_SAVE_ID=1;KIRBY_PRESSED_KEYS=1;menu[0x2A]=0;menu[2]=1;
 ((uint16_t*)0x08386A50)[0]=0x100;AP_SAVED_PAINT_CHOICE=ap_color_choice_encode(5);
 KIRBY_SPRAY_PAINT_FLAGS=0;ap_on_treasure_paint_selection(menu);
 CHECK(AP_SAVED_PAINT_CHOICE==0&&slots[1]==0&&KIRBY_SPRAY_PAINT_FLAGS==0);
 /* Persistent transform modes must consume requests, without clearing native flags. */
 for(unsigned flags=1;flags<=3;flags++)for(unsigned color=0;color<19;color++){
  ready();gApStartingKirbyColorInitial=AP_COLOR_CONFIG_MAGIC|AP_COLOR_PER_ROOM;
  AP_MAILBOX_INIT_COOKIE=AP_MAILBOX_INIT_COOKIE_VALUE;AP_STARTING_KIRBY_COLOR_ID=color;
  KIRBY_MAIN_FLAGS|=flags<<16;transform_calls=0;
  ap_apply_starting_kirby_color_config();
  CHECK(obj_calls==1&&bg_calls==1&&AP_STARTING_KIRBY_COLOR_APPLIED==1);
  CHECK(transform_calls==(flags&1)&&((KIRBY_MAIN_FLAGS>>16)&3)==flags);
  CHECK(obj_color==ap_native_color(color));
 }
 /* Every unsafe palette context defers and retries instead of consuming latch. */
 for(unsigned reason=0;reason<7;reason++){
  ready();gApStartingKirbyColorInitial=AP_COLOR_CONFIG_MAGIC;AP_MAILBOX_INIT_COOKIE=0;
  switch(reason){case 0:KIRBY_HUD_TASK=0;break;case 1:KIRBY_HUD_TASK++;break;
   case 2:*(uint32_t*)0x03001008=0x081434F9;break;case 3:KIRBY_BLD_CONTROL=0xC0;KIRBY_BLD_Y=8;break;
   case 4:DEMO_PLAYBACK_FLAGS=0x10;break;case 5:KIRBY_CURRENT_PLAYER=1;break;
   case 6:*(uint32_t*)(KIRBY_STRUCTS_ADDR+KIRBY_STRUCT_TASK_OFFSET)=0;break;}
  ap_apply_starting_kirby_color_config();CHECK(!obj_calls&&!bg_calls&&!AP_STARTING_KIRBY_COLOR_APPLIED);
  ready();ap_apply_starting_kirby_color_config();CHECK(obj_calls==1&&bg_calls==1&&obj_color==0);
 }
 CHECK(!bad_io&&cases==45600);printf("%u precedence cases; explicit owned choices, Pink, invalid padding, save slots, deferred HUD/fades, retry/latch pass\n",cases);return 0;
}
