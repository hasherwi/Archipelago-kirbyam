ENTRY(ap_hook_entry)

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
}
