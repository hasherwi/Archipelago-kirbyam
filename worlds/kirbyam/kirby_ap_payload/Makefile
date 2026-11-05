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

payload.elf: ap_payload.o ap_hook.o color_payload.o shared_save.o goal_game.o
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^ -lgcc

ap_payload.o: ap_payload.c shared_save.h shared_save_logic.h statue_runtime_logic.h minor_chest_runtime_logic.h lever_runtime_logic.h vitality_runtime_logic.h hub_connection_runtime_logic.h hub_save_logic.h generated_hub_switch_tables.inc color_runtime_logic.h color_tables.h enemy_runtime_logic.h candy_runtime_logic.h transition_runtime_logic.h transition_route_logic.h
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

shared_save.o: shared_save.c shared_save.h shared_save_logic.h
	$(CC) $(CFLAGS) -c -o $@ $<

goal_game.o: goal_game.c shared_save.h shared_save_logic.h goal_game_runtime_logic.h generated_goal_game_doors.inc
	$(CC) $(CFLAGS) -c -o $@ $<
