ENTRY(ap_hook_entry)

/*
 * Reserve the final sixteen bytes in patch_rom.py's 0x16A0-byte payload window
 * for per-seed health, starting color, ability gating, and statue-pool configuration. Moving the
 * location counter here also makes the linker fail if code/data grows into the
 * reserved words.
 */
AP_CONFIG_ADDR = 0x0815F690;

SECTIONS
{
  . = 0x0815E000;

  .text : {
    *(EXCLUDE_FILE (color_payload.o) .text*)
    KEEP(*(.apinfo))
    *(EXCLUDE_FILE (color_payload.o) .rodata*)
  }

  .data : { *(.data*) }
  .bss  : { *(.bss*) *(COMMON) }

  . = AP_CONFIG_ADDR;
  .apconfig : {
    /* Explicit subsection order is the per-seed token-write ABI. */
    KEEP(*(.apconfig.health))
    KEEP(*(.apconfig.color))
    KEEP(*(.apconfig.gate))
    KEEP(*(.apconfig.statue))
  }
  /* Append beyond the clean 16 MiB ROM; never allocate presumed internal padding. */
  .apcolors 0x09000000 : { KEEP(*(.apcolorinfo)) color_payload.o(.text* .rodata*) }
}

ASSERT(SIZEOF(.apconfig) == 16, "KirbyAM runtime config must be exactly 16 bytes")

ASSERT(SIZEOF(.apcolors) <= 0x10000, "Curated palette extension exceeds 64 KiB")

ASSERT(ADDR(.text) + SIZEOF(.text) <= AP_CONFIG_ADDR, "KirbyAM payload overlaps fixed configuration ABI")
ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "KirbyAM ROM payload must not contain writable static storage")
