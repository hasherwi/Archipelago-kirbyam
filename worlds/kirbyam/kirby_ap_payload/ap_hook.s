.syntax unified
.thumb

.global ap_hook_entry
.type ap_hook_entry, %function
.extern ap_poll_mailbox_c

ap_hook_entry:
    // Save r0-r3 and LR.
    // Thumb-1 cannot POP {.., lr}, so we manage LR manually.
    push {r0-r3, lr}

    bl ap_poll_mailbox_c

    // Restore r0-r3 and LR:
    pop  {r0-r3}      // restores r0-r3
    pop  {r4}         // restore saved LR into r4 (temporary)
    mov  lr, r4       // move it back to LR

    // Re-run overwritten instructions from 0x08152696/0x08152698:
    mov r7, r9
    mov r6, r8

    bx lr
