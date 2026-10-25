#define _GNU_SOURCE
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#define CHECK(c) do { if (!(c)) { fprintf(stderr, "line %d: %s\n", __LINE__, #c); return 1; } } while (0)
static unsigned requests, spawns, tasks, accepts = 1, script_after_tasks;
static void native_spawn(uint16_t room, uint8_t *x, uint8_t *y);
static uint8_t native_request(void *k, uint16_t room, uint8_t x, uint8_t y);
static void native_tasks(void);
static uint32_t *native_world_props(uint32_t a, uint8_t b, uint8_t c) {
    static uint32_t props; (void)a; (void)b; (void)c; return &props;
}
/* PAYLOAD */
#define U8(a) (*(uint8_t *)(uintptr_t)(a))
#define U16(a) (*(uint16_t *)(uintptr_t)(a))
#define U32(a) (*(uint32_t *)(uintptr_t)(a))
static void native_spawn(uint16_t room, uint8_t *x, uint8_t *y) {
    if (room != 0x321) __builtin_trap();
    spawns++; *x = 12; *y = 9;
}
static uint8_t native_request(void *k, uint16_t room, uint8_t x, uint8_t y) {
    if ((uintptr_t)k != KIRBY_STRUCTS_ADDR || room != 0x321 || x != 12 || y != 9
        || AP_IN_FLAG != 1 || AP_ITEM_RCVD_COUNTER != 100) __builtin_trap();
    requests++;
    if (accepts) U32(KIRBY_STRUCTS_ADDR + 8) |= 0x100; /* Native transition blocks the next request. */
    return accepts;
}
static void native_tasks(void) {
    tasks++;
    if (script_after_tasks) U32(KIRBY_STRUCTS_ADDR + 0x110) = 1;
}
static void ready(void) {
    memset((void*)0x02000000, 0, 0x40000);
    memset((void*)0x03000000, 0, 0x8000);
    AP_MAILBOX_INIT_COOKIE = AP_MAILBOX_INIT_COOKIE_VALUE;
    AP_STARTING_KIRBY_COLOR_APPLIED = 1; /* Palette config already applied by native startup. */
    AI_KIRBY_STATE = 300;
    U32(0x03000010) = 0x03002000; U32(0x03002008) = 0x08033B9D;
    U8(0x0203AD30) = 1;
    U32(KIRBY_STRUCTS_ADDR + 0xCC) = 0x03001000;
    U32(KIRBY_STRUCTS_ADDR + 0xC) = 0x1000;
    U8(KIRBY_STRUCTS_ADDR + 0x100) = 6;
    U16(KIRBY_STRUCTS_ADDR + 0x60) = 1;
    AP_IN_ITEM_ID = 3860041; AP_IN_PLAYER = 7; AP_IN_FLAG = 1;
    AP_ITEM_RCVD_COUNTER = 100;
    requests = spawns = tasks = script_after_tasks = 0; accepts = 1;
}
int main(void) {
    CHECK(mmap((void*)0x02000000, 0x40000, PROT_READ|PROT_WRITE,
        MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED, -1, 0) == (void*)0x02000000);
    CHECK(mmap((void*)0x03000000, 0x8000, PROT_READ|PROT_WRITE,
        MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED, -1, 0) == (void*)0x03000000);
    ready();
    ap_poll_mailbox_c(); /* Input poll cannot execute or acknowledge this trap. */
    CHECK(AP_IN_FLAG == 1 && AP_ITEM_RCVD_COUNTER == 100 && !requests);
    ap_after_tasks();
    CHECK(tasks == 1 && requests == 1 && spawns == 1);
    CHECK(AP_IN_FLAG == 0 && AP_ITEM_RCVD_COUNTER == 101 && AP_DEBUG_LAST_FROM == 7);
    ap_after_tasks(); CHECK(requests == 1 && AP_ITEM_RCVD_COUNTER == 101);
    /* Repeat receipts remain ordered; the second waits for transition completion. */
    AP_IN_FLAG = 1; ap_after_tasks(); CHECK(requests == 1 && AP_IN_FLAG == 1);
    U32(KIRBY_STRUCTS_ADDR + 8) = 0; U16(KIRBY_STRUCTS_ADDR + 0x60) = 0x321;
    ap_after_tasks(); CHECK(requests == 1 && AP_IN_FLAG == 0 && AP_ITEM_RCVD_COUNTER == 102);
    /* Every safety gate independently retains the exact pending receipt. */
    const uint32_t addresses[] = {0x03000010, 0x03002008, 0x0203AD2C, 0x0203AD10, 0x03002440, 0x0203AD3C,
        0x0203AD30, 0x03000514, KIRBY_STRUCTS_ADDR+0xCC, KIRBY_STRUCTS_ADDR+0x100,
        KIRBY_STRUCTS_ADDR+0xD4, KIRBY_STRUCTS_ADDR+0x110, KIRBY_STRUCTS_ADDR+8,
        KIRBY_STRUCTS_ADDR+0xC};
    const uint32_t values[] = {0, 0, 299, 0x10, 0x800, 1, 2, 0x10, 0, 0, 39, 1, 0x100, 0};
    for (unsigned i = 0; i < sizeof addresses / sizeof *addresses; i++) {
        ready(); U32(addresses[i]) = values[i]; ap_after_tasks();
        CHECK(!requests && !spawns && AP_IN_FLAG == 1 && AP_ITEM_RCVD_COUNTER == 100);
    }
    ready(); script_after_tasks = 1; ap_after_tasks();
    CHECK(tasks == 1 && !requests && AP_IN_FLAG == 1);
    ready(); accepts = 0; ap_after_tasks();
    CHECK(requests == 1 && AP_IN_FLAG == 1 && AP_ITEM_RCVD_COUNTER == 100);
    accepts = 1; ap_after_tasks(); CHECK(requests == 2 && AP_IN_FLAG == 0);
    ready(); U16(KIRBY_STRUCTS_ADDR+0x60) = 0x321;
    U32(KIRBY_STRUCTS_ADDR+0x110) = 1; ap_after_tasks(); CHECK(AP_IN_FLAG == 1);
    U32(KIRBY_STRUCTS_ADDR+0x110) = 0; ap_after_tasks(); CHECK(AP_IN_FLAG == 0 && !requests);
    /* All original traps retain their original effects and input-poll ACK. */
    for (unsigned id = 32; id <= 36; id++) {
        ready(); AP_IN_ITEM_ID = 3860000 + id;
        KIRBY_LIVES = 5; U8(KIRBY_STRUCTS_ADDR+0xDC) = 3;
        ap_poll_mailbox_c();
        CHECK(!requests && AP_IN_FLAG == 0 && AP_ITEM_RCVD_COUNTER == 101);
        CHECK(U8(KIRBY_STRUCTS_ADDR+0x100) == (id == 32 ? 4 : id == 34 ? 0 : 6));
        CHECK(KIRBY_LIVES == (id == 33 ? 4 : id == 36 ? 0 : 5));
        CHECK(U8(KIRBY_STRUCTS_ADDR+0xDC) == (id == 35 ? 0 : 3));
    }
    ready(); AP_IN_ITEM_ID = 0xFFFFFFFF; ap_after_tasks(); ap_poll_mailbox_c();
    CHECK(!requests && AP_IN_FLAG == 1 && AP_ITEM_RCVD_COUNTER == 100);
    return 0;
}
