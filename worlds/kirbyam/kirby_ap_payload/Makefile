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


CFLAGS  := -mthumb -mcpu=arm7tdmi -Os -ffreestanding -fno-builtin -fno-jump-tables -fno-tree-switch-conversion -nostdlib -Wall -Wextra
LDFLAGS := -T linker.ld -nostdlib

all: payload.bin color_payload.bin

payload.elf: ap_payload.o ap_hook.o color_payload.o
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^ -lgcc

ap_payload.o: ap_payload.c statue_runtime_logic.h minor_chest_runtime_logic.h lever_runtime_logic.h vitality_runtime_logic.h color_runtime_logic.h color_tables.h
	$(CC) $(CFLAGS) -c -o $@ $<

ap_hook.o: ap_hook.s
	$(CC) $(CFLAGS) -c -o $@ $<

payload.bin: payload.elf
	$(OBJCOPY) -O binary --remove-section=.apcolors $< $@

clean:
	-$(RM) *.o payload.elf payload.bin color_payload.bin

color_tables.h: ../data/colors.json ../color_registry.py generate_colors.py
	python3 generate_colors.py

color_payload.o: color_payload.c color_runtime_logic.h color_tables.h
	$(CC) $(CFLAGS) -c -o $@ $<

color_payload.bin: payload.elf
	$(OBJCOPY) -O binary --only-section=.apcolors $< $@
