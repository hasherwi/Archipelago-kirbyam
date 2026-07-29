ENTRY(ap_hook_entry)

/* Final 4 bytes of patch_rom.py's 0x16A0-byte payload window. */
AP_CONFIG_ADDR = 0x0815F69C;

SECTIONS
{
  . = 0x0815E000;

  .text : {
    /* Hook targets are found by symbol name rather than normal relocations. */
    KEEP(*(.text.ap_hook_entry))
    KEEP(*(.text.ap_on_*))
    *(.text*)
    KEEP(*(.apinfo))
    *(.rodata*)
  }

  .data : { *(.data*) }
  .bss  : { *(.bss*) *(COMMON) }

  /* Moving the location counter here fails the link if code grows into the
   * reserved per-seed configuration word. */
  . = AP_CONFIG_ADDR;
  .apconfig : {
    KEEP(*(.apconfig))
  }
}

ASSERT(SIZEOF(.apconfig) == 4, "KirbyAM AP ROM config must be exactly 4 bytes")
