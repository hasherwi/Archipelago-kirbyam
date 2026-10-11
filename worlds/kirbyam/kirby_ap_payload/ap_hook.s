.syntax unified
.thumb

.global ap_hook_entry
.type ap_hook_entry, %function
.extern ap_poll_mailbox_c
.extern ap_on_minor_chest_reward_popup

ap_hook_entry:
    // Legacy hook site behavior: run mailbox poll, then replay overwritten
    // instructions from 0x08152696/0x08152698.
    push {r0-r3, lr}

    bl ap_poll_mailbox_c

    pop  {r0-r3}
    mov  r7, r9
    mov  r6, r8
    pop  {pc}

.global ap_minor_chest_reward_popup_hook
.type ap_minor_chest_reward_popup_hook, %function
ap_minor_chest_reward_popup_hook:
    // The patched site replaces `ldr r4, [r2, #0x4C]; adds r0, r4, #0`.
    // Keep all caller-live scratch registers except r0, which is overwritten
    // by the displaced instructions. Four pushed registers keep SP aligned.
    // Replaying adds also restores the exact N/Z/C/V effect of the native site.
    push {r1-r3, lr}
    bl ap_on_minor_chest_reward_popup
    pop {r1-r3}
    pop {r0}
    mov lr, r0
    ldr r4, [r2, #0x4C]
    adds r0, r4, #0
    bx lr
