ENTRY(ap_hook_entry)

/*
 * Reserve the final twenty-four bytes in patch_rom.py's 0x1BA0-byte payload window
 * for per-seed Area Keys, Minny, health, starting color, ability gating, and statue-pool
 * configuration. Moving the
 * location counter here also makes the linker fail if code/data grows into the
 * reserved words.
 */
AP_CONFIG_ADDR = 0x0815F688;

SECTIONS
{
  /* Extend backward within the retail zero-filled padding; config stays fixed. */
  . = 0x0815DB00;

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
  .apcolors 0x09000000 : { KEEP(*(.apcolorinfo)) KEEP(*(.aphubinfo)) KEEP(*(.apgoalinfo)) KEEP(*(.apfullinfo)) KEEP(*(.apcueinfo)) KEEP(*(.apvisualinfo)) color_payload.o(.text* .rodata*) *(.aphub)
    KEEP(*(.aphubboards))
    KEEP(*(.apchestart))
    KEEP(*(.aprewardfx))
    KEEP(*(.apvisitdata))
    KEEP(*(.aphubteleportdata))
    KEEP(*(.apstatuefx))
    KEEP(*(.apstatuefx_data))
    ap_extension_code_end = .;
    /* The shared pickup art table includes native statue frames at E388..ED07. */
    . = 0xED10;
    KEEP(*(.apstatueart))
    . = 0xEE00;
    KEEP(*(.apstatueconfig))
    . = 0xF000;
    KEEP(*(.aprewardconfig))
    . = 0xFFBC;
    KEEP(*(.aproomvisitconfig))
    . = 0xFFC0;
    KEEP(*(.apnarcolepsyinfo))
    KEEP(*(.aprandomteleportinfo))
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

ASSERT(ap_extension_code_end <= 0x09007000, "Animated shard art overlaps extension code")
ASSERT(gApRewardArtConfig == 0x0900F000, "Reward art config address changed")
ASSERT(gApVisitRoomArtConfig == 0x0900FFBC, "Room visit config address changed")
ASSERT(gApNarcolepsyInfo == 0x0900FFC0, "Narcolepsy marker address changed")
ASSERT(gApRandomTeleportInfo == 0x0900FFC4, "Random Teleport marker address changed")
ASSERT(gApEnemySourceConfig == 0x0900FFDC, "Enemy source config address changed")

ASSERT(ap_full_completion_marker == 0x09000018, "Full completion marker address changed")
ASSERT(ap_copy_room_marker == 0x0900FFD4, "Copy Room marker address changed")

ASSERT(gApGoalInfo == 0x09000010, "Goal Game marker address changed")
ASSERT(gApPhoneConfig == 0x0900FFC8, "Phone config address changed")

ASSERT(gApReceiptCueInfo == 0x09000020, "Receipt cue marker address changed")

ASSERT(gApWorldStatueLogo == 0x0900ED10, "World-statue logo address changed")
ASSERT(gApWorldStatueConfig == 0x0900EE00, "World-statue seed config address changed")
ASSERT(gApReceiptVisualInfo == 0x09000028, "Receipt visual marker address changed")
