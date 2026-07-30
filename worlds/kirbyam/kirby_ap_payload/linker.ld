ENTRY(ap_hook_entry)

/*
 * Reserve the final eight bytes in patch_rom.py's 0x16A0-byte payload window
 * for per-seed ability gating and statue-pool configuration. Moving the
 * location counter here also makes the linker fail if code/data grows into the
 * reserved words.
 */
AP_CONFIG_ADDR = 0x0815F698;

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
    KEEP(*(.apconfig.gate))
    KEEP(*(.apconfig.statue))
  }
}

ASSERT(SIZEOF(.apconfig) == 8, "KirbyAM ability runtime config must be exactly 8 bytes")
