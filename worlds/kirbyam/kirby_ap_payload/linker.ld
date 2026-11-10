ENTRY(ap_hook_entry)

/*
 * Reserve the final twenty-four bytes in patch_rom.py's 0x1AA0-byte payload window
 * for per-seed Area Keys, Minny, health, starting color, ability gating, and statue-pool
 * configuration. Moving the
 * location counter here also makes the linker fail if code/data grows into the
 * reserved words.
 */
AP_CONFIG_ADDR = 0x0815F688;

SECTIONS
{
  /* Extend backward within the retail zero-filled padding; config stays fixed. */
  . = 0x0815DC00;

  .text : {
    /* Keep the Thumb tail entry within branch range of its C implementation. */
    KEEP(*(.text.ap_request_entry))
    KEEP(*(.text.ap_request_impl))
    *(EXCLUDE_FILE (color_payload.o) .text*)
    KEEP(*(.apinfo))
    *(EXCLUDE_FILE (color_payload.o) .rodata*)
  }

  .data : { *(.data*) }
  .bss  : { *(.bss*) *(COMMON) }

  . = AP_CONFIG_ADDR;
  .apconfig : {
    /* Explicit subsection order is the per-seed token-write ABI. */
    KEEP(*(.apconfig.area_keys))
    KEEP(*(.apconfig.minny))
    KEEP(*(.apconfig.health))
    KEEP(*(.apconfig.color))
    KEEP(*(.apconfig.gate))
    KEEP(*(.apconfig.statue))
  }
  /* Append beyond the clean 16 MiB ROM; never allocate presumed internal padding. */
  .apcolors 0x09000000 : { KEEP(*(.apcolorinfo)) KEEP(*(.aphubinfo)) color_payload.o(.text* .rodata*) *(.aphub)
    ap_extension_code_end = .;
    . = 0xFFC8;
    KEEP(*(.apphoneinfo))
    . = 0xFFD4;
    KEEP(*(.apcopyinfo))
    . = 0xFFDC;
    KEEP(*(.apsourceconfig))
  }
}

ASSERT(SIZEOF(.apconfig) == 24, "KirbyAM runtime config must be exactly 24 bytes")

ASSERT(SIZEOF(.apcolors) <= 0x10000, "Curated palette extension exceeds 64 KiB")

ASSERT(ADDR(.text) + SIZEOF(.text) <= AP_CONFIG_ADDR, "KirbyAM payload overlaps fixed configuration ABI")
ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "KirbyAM ROM payload must not contain writable static storage")

ASSERT(ap_extension_code_end <= 0x0900FFC8, "Enemy source config overlaps extension code")
ASSERT(gApEnemySourceConfig == 0x0900FFDC, "Enemy source config address changed")

ASSERT(ap_copy_room_marker == 0x0900FFD4, "Copy Room marker address changed")

ASSERT(gApPhoneConfig == 0x0900FFC8, "Phone config address changed")
