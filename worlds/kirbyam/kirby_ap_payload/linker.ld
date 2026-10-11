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
    *(.text*)
    KEEP(*(.apinfo))
    *(.rodata*)
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
}

ASSERT(SIZEOF(.apconfig) == 16, "KirbyAM runtime config must be exactly 16 bytes")
