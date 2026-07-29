PREFIX  :=
CC      := arm-none-eabi-gcc
OBJCOPY := arm-none-eabi-objcopy

# GNU make defaults RM to `rm -f`; on native Windows hosts, prefer cmd's `del`.
ifeq ($(OS),Windows_NT)
RM := cmd /C del /Q /F
endif

# Preserve existing local devkitPro defaults when installed at the historical path.
ifneq ("$(wildcard C:/devkitPro/devkitARM/bin/arm-none-eabi-gcc.exe)","")
CC      := C:/devkitPro/devkitARM/bin/arm-none-eabi-gcc.exe
OBJCOPY := C:/devkitPro/devkitARM/bin/arm-none-eabi-objcopy.exe
endif


CFLAGS  := -mthumb -mcpu=arm7tdmi -Os -ffreestanding -fno-builtin -fno-jump-tables -fno-tree-switch-conversion -ffunction-sections -fdata-sections -nostdlib -Wall -Wextra
LDFLAGS := -T linker.ld -nostdlib -Wl,--gc-sections

all: payload.bin

payload.elf: ap_payload.o statue_transition_fix.o ap_hook.o
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^ -lgcc

# Rename the Issue #874 implementation only in the original translation unit.
# statue_transition_fix.c exports the public replacement used by patch_rom.py.
ap_payload.o: ap_payload.c fix875_rename_start_hook.h
	$(CC) $(CFLAGS) -include fix875_rename_start_hook.h -c -o $@ $<

statue_transition_fix.o: statue_transition_fix.c
	$(CC) $(CFLAGS) -c -o $@ $<

ap_hook.o: ap_hook.s
	$(CC) $(CFLAGS) -c -o $@ $<

payload.bin: payload.elf
	$(OBJCOPY) -O binary $< $@

clean:
	-$(RM) *.o payload.elf payload.bin
