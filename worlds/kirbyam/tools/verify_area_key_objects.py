"""Execute compiled Area Key object hooks in Unicorn with intercepted native calls.

Requires unicorn, ARM nm, a built payload and the lawful USA base ROM. This
checks ABI and RAM changes, not emulator gameplay or visible sprite acceptance.
"""
import argparse
import hashlib
import json
import struct
import subprocess
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--nm", default="arm-none-eabi-nm")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload_dir = Path(__file__).parents[1] / "kirby_ap_payload"
    base = args.rom.read_bytes()
    assert hashlib.sha1(base).hexdigest() == "274b102b6d940f46861a92b4e65f89a51815c12c"
    payload = (payload_dir / "payload.bin").read_bytes()
    extension = (payload_dir / "color_payload.bin").read_bytes()
    symbols = {p[2]: int(p[0], 16) for line in subprocess.check_output([args.nm, str(payload_dir / "payload.elf")], text=True).splitlines() if len(p := line.split()) == 3}
    rows = []
    for disabled in [False, True]:
        u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        u.mem_map(0x08000000, 0x02000000)
        u.mem_write(0x08000000, base)
        u.mem_write(0x0815DC00, payload)
        u.mem_write(0x09000000, extension)
        u.mem_map(0x02000000, 0x40000)
        u.mem_map(0x03000000, 0x8000)
        u.mem_map(0x01000000, 0x1000)
        task, obj, effect, template, tile, level = 0x03001000, 0x03001100, 0x03001500, 0x02002000, 0x02003000, 0x02023530
        stop = 0x01000000
        calls = []
        native_slot = [0]
        def w(a, fmt, v):
            u.mem_write(a, struct.pack(fmt, v))
        def r(a, fmt):
            return struct.unpack(fmt, u.mem_read(a, struct.calcsize(fmt)))[0]
        def hook(emu, addr, size, data):
            if addr == stop:
                emu.emu_stop()
                return
            value = None
            if addr in [0x08099B80, 0x08152C3C, 0x0800A6E8, 0x0800A868, 0x0802B2F4]:
                calls.append(addr)
                value = 0
                if addr == 0x0800A868:
                    native_slot[0] = 1
            elif addr == 0x080027E8:
                value = native_slot[0]
            elif addr == 0x080023E4:
                value = 0xFE
            elif addr == 0x080025AC:
                value = tile
            elif addr == 0x0808B62C:
                calls.append(addr)
                value = effect
            if value is not None:
                assert emu.reg_read(UC_ARM_REG_SP) % 8 == 0
                emu.reg_write(UC_ARM_REG_R0, value)
                emu.reg_write(UC_ARM_REG_PC, emu.reg_read(UC_ARM_REG_LR))
        u.hook_add(UC_HOOK_CODE, hook)
        def run(name, *values):
            calls.clear()
            for reg, value in zip([UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3], values):
                u.reg_write(reg, value)
            u.reg_write(UC_ARM_REG_SP, 0x03007C00)
            u.reg_write(UC_ARM_REG_LR, stop | 1)
            u.emu_start(symbols[name] | 1, 0, count=100000)
            assert u.reg_read(UC_ARM_REG_PC) == stop
            assert u.reg_read(UC_ARM_REG_SP) == 0x03007C00
            return u.reg_read(UC_ARM_REG_R0)
        w(0x0815F688, '<I', 0x414B0100 if disabled else 0x414B0101)
        w(0x030035D0, '<I', task)
        w(task + 6, '<H', obj - 0x03000000)
        w(obj + 0x60, '<H', 142)
        w(obj + 0xBE, '<H', 195)
        w(template, '<B', 1)
        w(template + 1, '<B', 0x24)
        w(template + 0xC, '<B', 0x84)
        w(template + 0x1E, '<H', 195)
        w(level + 0x5F8, '<H', 142)
        w(obj + 0xB0, '<I', template)
        w(obj + 0xB4, '<I', effect)
        w(tile + 8, '<H', 195)
        for keys in [0, 4, 0, 4]:
            w(0x0203B0C0, '<I', keys)
            allowed = disabled or keys == 4
            assert run('ap_area_key_spawn_blocked', template, level) == int(not allowed)
            w(obj + 8, '<I', 0)
            w(obj + 0xB5, '<B', 0)
            run('ap_area_warp_star_main')
            assert calls == ([0x08099B80] if allowed else [0x08152C3C])
            w(obj + 0xB4, '<I', effect)
            # Loaded, previously visited mirror can relock and reopen.
            w(obj + 0xBC, '<H', 5)
            w(obj + 0xBE, '<H', 3)
            w(template + 0x22, '<H', 0x100)
            w(obj + 8, '<I', 0)
            w(effect + 0x18, '<H', 0x294)
            w(effect + 0x26, '<B', 9)
            run('ap_area_mirror_main')
            assert r(effect + 0x26, '<B') == (9 if allowed else 6)
            assert calls == [0x08099B80]
            run('ap_area_door_decoration', obj)
            assert calls == ([0x0802B2F4] if allowed else [])
            if not allowed:
                assert r(effect + 0x26, '<B') == 6
            w(obj + 0xBE, '<H', 195)
            rows.append({'disabled': disabled, 'keys': keys, 'allowed': allowed})
        # A board is a complete frame at the foot; native interior and
        # unvisited indicators have distinct anchors when a key is received.
        if not disabled:
            for decorated in [False, True]:
                w(template + 0x22, '<H', 0x100 if decorated else 0)
                w(obj + 0x44, '<I', 560 << 8)
                w(obj + 0xB4, '<I', effect)
                w(0x0203B0C0, '<I', 0)
                run('ap_area_door_decoration', obj)
                assert r(effect + 0x26, '<B') == 6
                assert r(effect + 0x38, '<I') == 560 << 8
                w(0x0203B0C0, '<I', 4)
                run('ap_area_door_decoration', obj)
                assert calls == [0x0802B2F4]
                assert r(effect + 0x18, '<H') == (0x294 if decorated else 0x2CF)
                assert r(effect + 0x26, '<B') == (10 if decorated else 0)
                assert r(effect + 0x38, '<I') == (550 if decorated else 520) << 8
        # Special Hub mirrors stay absent before the native Hub initializer,
        # then receive a board even after the native callback has gone idle.
        w(obj + 0x82, '<B', 0x8C)
        w(obj + 0xB8, '<H', 0xFFFF)
        w(obj + 0xB4, '<I', 0)
        w(0x0203B0C0, '<I', 0)
        run('ap_area_hub_mirror_main')
        assert calls == [0x08099B80]
        assert r(obj + 0xB4, '<I') == 0
        w(obj + 0xB8, '<H', 195)
        run('ap_area_hub_mirror_main')
        assert calls == ([0x08099B80] if disabled else [0x0808B62C, 0x08099B80])
        if not disabled:
            assert r(effect + 0x26, '<B') == 6
        w(0x0203B0C0, '<I', 4)
        run('ap_area_hub_mirror_main')
        assert r(obj + 0xB4, '<I') == 0
        # Reconciliation during an already authorized flight must not free the
        # native passenger-owning object. The separate boarding guard remains.
        w(obj + 0xB5, '<B', 1)
        w(0x0203B0C0, '<I', 0)
        run('ap_area_warp_star_main')
        assert calls == [0x08099B80]
        w(obj + 0xB5, '<B', 0)
        # The actual register adapters preserve the caller's callee-saved regs.
        for name, reg in [('level', UC_ARM_REG_R6), ('strip', UC_ARM_REG_R5)]:
            u.reg_write(reg, template)
            u.reg_write(UC_ARM_REG_R7, level)
            for keys in [0, 4]:
                for occupied in [0, 1]:
                    native_slot[0] = occupied
                    w(0x0203B0C0, '<I', keys)
                    u.reg_write(UC_ARM_REG_R4, 0x44444444)
                    expected = occupied or int(not disabled and keys == 0)
                    assert run('ap_area_spawn_' + name + '_entry', 0, 0, 0) == expected
                    assert u.reg_read(UC_ARM_REG_R4) == 0x44444444
                    assert u.reg_read(reg) == template
                    assert u.reg_read(UC_ARM_REG_R7) == level
        # Repeated frame scans create one star; occupied/consumed native slots
        # and missing keys never create another. Native scheduler still runs.
        w(0x0203AD30, '<B', 1)
        w(level + 0x1E4, '<I', 0x02004000)
        w(0x02004000, '<I', template)
        native_slot[0] = 0
        w(0x0203B0C0, '<I', 0)
        run('ap_area_spawn_main')
        assert calls == [0x0800A6E8]
        w(0x0203B0C0, '<I', 4)
        run('ap_area_spawn_main')
        assert calls == ([0x0800A6E8] if disabled else [0x0800A6E8, 0x0800A868])
        run('ap_area_spawn_main')
        assert calls == [0x0800A6E8]
    report = {'scope': 'Compiled ARM with intercepted native callees; not gameplay acceptance', 'payload_sha256': hashlib.sha256(payload).hexdigest(), 'extension_sha256': hashlib.sha256(extension).hexdigest(), 'cases': rows, 'adapters_and_no_duplicate_spawn': 'passed'}
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print('PASS: compiled ARM lifecycle, sprite state, spawn adapters and duplicate prevention')


if __name__ == '__main__':
    main()
