ENTRY(ap_hook_entry)

/*
 * Reserve the final twenty bytes in patch_rom.py's 0x16A0-byte payload window
 * for per-seed Minny, health, starting color, ability gating, and statue-pool
 * configuration. Moving the
 * location counter here also makes the linker fail if code/data grows into the
 * reserved words.
 */
AP_CONFIG_ADDR = 0x0815F68C;

SECTIONS
{
  . = 0x0815E000;

  .text : {
    /* Keep the Thumb tail entry within branch range of its C implementation. */
    KEEP(*(.text.ap_request_entry))
    *(EXCLUDE_FILE (color_payload.o) .text*)
    KEEP(*(.apinfo))
    *(EXCLUDE_FILE (color_payload.o) .rodata*)
  }

  .data : { *(.data*) }
  .bss  : { *(.bss*) *(COMMON) }

  . = AP_CONFIG_ADDR;
  .apconfig : {
    /* Explicit subsection order is the per-seed token-write ABI. */
    KEEP(*(.apconfig.minny))
    KEEP(*(.apconfig.health))
    KEEP(*(.apconfig.color))
    KEEP(*(.apconfig.gate))
    KEEP(*(.apconfig.statue))
  }
  /* Append beyond the clean 16 MiB ROM; never allocate presumed internal padding. */
  .apcolors 0x09000000 : { KEEP(*(.apcolorinfo)) color_payload.o(.text* .rodata*) *(.aphub) }
}

ASSERT(SIZEOF(.apconfig) == 20, "KirbyAM runtime config must be exactly 20 bytes")

ASSERT(SIZEOF(.apcolors) <= 0x10000, "Curated palette extension exceeds 64 KiB")
