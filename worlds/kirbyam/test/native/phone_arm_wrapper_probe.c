/* ROM-free execution of the freshly linked shipping wrapper with mGBA's ARM7TDMI.
 * The predicate is intercepted at its first instruction and models hostile but
 * legal caller-saved clobbers. Native continuation is a synthetic ABI epilogue.
 * This verifies wrapper mechanics, not native gameplay or C predicate logic.
 */
#include <mgba/flags.h>
#include <mgba/core/core.h>
#include <mgba/gba/core.h>
#include <mgba/internal/arm/arm.h>
#include <mgba/internal/arm/isa-inlines.h>
#include <mgba-util/vfs.h>
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define ENTRY 0x08056C2Cu
#define CONTINUE 0x08056C34u
#define RETURN 0x0201F000u
#define BASELINE 0x0201E000u
#define STACK 0x03007000u

static void jump(struct ARMCore *cpu, uint32_t address) {
    cpu->gprs[15] = address & ~1u;
    _ARMSetMode(cpu, MODE_THUMB);
    ThumbWritePC(cpu);
}
static uint32_t initial(unsigned reg, unsigned variant) {
    return 0x12340000u ^ (reg * 0x1020301u) ^ (variant * 0x11111111u);
}
static void prepare(struct mCore *core, unsigned variant, uint32_t sp) {
    core->reset(core);
    for (unsigned addr = 0x03006F80u; addr < STACK + 32; addr += 4)
        core->busWrite32(core, addr, 0xA5A5A5A5u);
    for (unsigned reg = 0; reg < 13; ++reg)
        ((struct ARMCore *)core->cpu)->gprs[reg] = initial(reg, variant);
    struct ARMCore *cpu = core->cpu;
    cpu->gprs[13] = sp;
    cpu->gprs[14] = RETURN | 1;
}
static void run(struct mCore *core, uint32_t predicate, uint32_t blocked,
                unsigned variant, uint32_t sp) {
    struct ARMCore *cpu = core->cpu;
    /* Execute the original displaced prologue independently for the oracle. */
    const uint16_t prologue[] = {0xB5F0, 0x4647, 0xB480, 0xB081};
    prepare(core, variant, sp);
    for (unsigned i = 0; i < 4; ++i)
        core->busWrite16(core, BASELINE + i * 2, prologue[i]);
    jump(cpu, BASELINE);
    for (unsigned i = 0; i < 4; ++i) core->step(core);
    uint32_t expected_regs[16], expected_stack[7];
    for (unsigned r = 0; r < 16; ++r) expected_regs[r] = cpu->gprs[r];
    for (unsigned i = 0; i < 7; ++i)
        expected_stack[i] = core->busRead32(core, sp - 28 + 4 * i);
    assert(expected_regs[13] == sp - 28);

    prepare(core, variant, sp);
    jump(cpu, ENTRY);
    unsigned calls = 0, continuations = 0, steps = 0;
    while ((uint32_t)cpu->gprs[15] != RETURN + 2 && steps++ < 100) {
        uint32_t pc = cpu->gprs[15] - 2; /* mGBA's Thumb prefetch PC. */
        if (pc == predicate) {
            ++calls;
            for (unsigned r = 0; r < 3; ++r) assert((uint32_t)cpu->gprs[r] == initial(r, variant));
            for (unsigned r = 4; r < 12; ++r) assert((uint32_t)cpu->gprs[r] == initial(r, variant));
            assert((uint32_t)cpu->gprs[13] == sp - 16 && !(cpu->gprs[13] & 7));
            uint32_t lr = cpu->gprs[14];
            cpu->gprs[0] = blocked;
            cpu->gprs[1] = 0xDEAD0001;
            cpu->gprs[2] = 0xDEAD0002;
            cpu->gprs[3] = 0xDEAD0003;
            cpu->gprs[12] = 0xDEAD000C;
            cpu->cpsr.n = cpu->cpsr.z = cpu->cpsr.c = cpu->cpsr.v = 1;
            jump(cpu, lr);
        } else if (pc == CONTINUE) {
            ++continuations;
            assert(!blocked);
            /* r3 is scratch in the entry patch/continuation veneer, r12 is
             * caller-saved, and NZCV is not preserved by a function call. */
            for (unsigned r = 0; r < 16; ++r)
                if (r != 3 && r != 12 && r != 15)
                    assert((uint32_t)cpu->gprs[r] == expected_regs[r]);
            for (unsigned i = 0; i < 7; ++i)
                assert(core->busRead32(core, sp - 28 + 4 * i) == expected_stack[i]);
            /* Execute a real Thumb epilogue for that exact native stack frame. */
            const uint16_t epilogue[] = {0xB001, 0xBC01, 0x4680, 0xBDF0};
            for (unsigned i = 0; i < 4; ++i)
                core->busWrite16(core, BASELINE + 0x20 + 2 * i, epilogue[i]);
            jump(cpu, BASELINE + 0x20);
        } else {
            core->step(core);
        }
    }
    assert(steps < 100 && calls == 1 && continuations == (blocked ? 0u : 1u));
    assert(cpu->cpsr.t && (uint32_t)cpu->gprs[15] == RETURN + 2);
    assert((uint32_t)cpu->gprs[13] == sp);
    for (unsigned r = 4; r < 12; ++r) assert((uint32_t)cpu->gprs[r] == initial(r, variant));
    if (blocked)
        for (unsigned r = 0; r < 3; ++r) assert((uint32_t)cpu->gprs[r] == initial(r, variant));
    /* Wrapper stack writes must stay below SP and inside its 28-byte frame. */
    for (unsigned addr = 0x03006F80u; addr < sp - 28; addr += 4)
        assert(core->busRead32(core, addr) == 0xA5A5A5A5u);
    for (unsigned addr = sp; addr < STACK + 32; addr += 4)
        assert(core->busRead32(core, addr) == 0xA5A5A5A5u);
}
int main(int argc, char **argv) {
    assert(argc == 2);
    uint32_t predicate = strtoul(argv[1], NULL, 0);
    size_t size = 0x1010000;
    unsigned char *rom = malloc(size);
    assert(rom && fread(rom, 1, size, stdin) == size);
    struct mCore *core = GBACoreCreate();
    assert(core && core->init(core));
    mCoreInitConfig(core, "phone-thumb-abi-probe");
    assert(core->loadROM(core, VFileFromMemory(rom, size)));
    const uint32_t results[] = {0, 1, 0xFFFFFFFFu};
    for (unsigned variant = 0; variant < 4; ++variant)
        for (unsigned stack = 0; stack < 2; ++stack)
            for (unsigned result = 0; result < 3; ++result)
                run(core, predicate, results[result], variant, STACK - stack * 8);
    core->unloadROM(core);
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    free(rom);
    puts("Phone Thumb ABI: 24 cases passed");
    return 0;
}
