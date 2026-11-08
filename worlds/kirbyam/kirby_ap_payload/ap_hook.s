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

.section .text.ap_request_entry,"ax",%progbits
.global ap_on_request_copy_ability_transition
.type ap_on_request_copy_ability_transition, %function
.thumb_func
ap_on_request_copy_ability_transition:
    // Native object swallow has Object2* in r5. Capture before the C prologue;
    // tail-call preserves the native return address and stack alignment.
    movs r2, r5
    mov r3, lr
    b ap_on_request_copy_ability_transition_c

.section .text.ap_hub_entry,"ax",%progbits
.balign 4
.global ap_after_tasks
.type ap_after_tasks, %function
.thumb_func
ap_after_tasks:
    // Eight-byte long tail call keeps the fixed payload/config window intact.
    // Preserve LR and stack alignment; the extension returns to GameLoop.
    ldr r3, 1f
    bx r3
1:  .word ap_hub_tasks
.size ap_after_tasks, .-ap_after_tasks

// Preserve native LR/arguments across long calls into the ROM extension.

.section .text.ap_transition_entries,"ax",%progbits
.balign 4
.global ap_prepare_automatic_transition_entry
.type ap_prepare_automatic_transition_entry, %function
.thumb_func
ap_prepare_automatic_transition_entry:
    ldr r3, 1f
    bx r3
1:  .word ap_prepare_automatic_transition
.size ap_prepare_automatic_transition_entry, .-ap_prepare_automatic_transition_entry

.section .text.ap_transition_entries,"ax",%progbits
.balign 4
.global ap_on_button_special_transition_entry
.type ap_on_button_special_transition_entry, %function
.thumb_func
ap_on_button_special_transition_entry:
    ldr r3, 1f
    bx r3
1:  .word ap_on_button_special_transition
.size ap_on_button_special_transition_entry, .-ap_on_button_special_transition_entry

.section .text.ap_transition_entries,"ax",%progbits
.balign 4
.global ap_on_warp_star_transition_entry
.type ap_on_warp_star_transition_entry, %function
.thumb_func
ap_on_warp_star_transition_entry:
    ldr r3, 1f
    bx r3
1:  .word ap_on_warp_star_transition
.size ap_on_warp_star_transition_entry, .-ap_on_warp_star_transition_entry

.section .text.ap_transition_entries,"ax",%progbits
.balign 4
.global ap_area_spawn_level_entry
.type ap_area_spawn_level_entry, %function
.thumb_func
ap_area_spawn_level_entry:
    push {r4, lr}
    ldr r3, 2f
    bl 1f
    cmp r0, #0
    bne 3f
    movs r0, r6
    movs r1, r7
    ldr r3, 4f
    bl 1f
3:  pop {r4}
    pop {r1}
    bx r1
1:  bx r3
.balign 4
2:  .word 0x080027E9
4:  .word ap_area_key_spawn_blocked
.size ap_area_spawn_level_entry, .-ap_area_spawn_level_entry

.section .text.ap_transition_entries,"ax",%progbits
.balign 4
.global ap_area_spawn_strip_entry
.type ap_area_spawn_strip_entry, %function
.thumb_func
ap_area_spawn_strip_entry:
    push {r4, lr}
    ldr r3, 2f
    bl 1f
    cmp r0, #0
    bne 3f
    movs r0, r5
    movs r1, r7
    ldr r3, 4f
    bl 1f
3:  pop {r4}
    pop {r1}
    bx r1
1:  bx r3
.balign 4
2:  .word 0x080027E9
4:  .word ap_area_key_spawn_blocked
.size ap_area_spawn_strip_entry, .-ap_area_spawn_strip_entry

.section .text.ap_transition_entries,"ax",%progbits
.balign 4
.global ap_area_door_decoration_entry
.type ap_area_door_decoration_entry, %function
.thumb_func
ap_area_door_decoration_entry:
    ldr r3, 1f
    bx r3
1:  .word ap_area_door_decoration
.size ap_area_door_decoration_entry, .-ap_area_door_decoration_entry

.section .text.ap_copy_room_load_entry,"ax",%progbits
.balign 4
.global ap_copy_room_load_entry
.type ap_copy_room_load_entry, %function
.thumb_func
ap_copy_room_load_entry:
    ldr r3, 1f
    bx r3
1: .word ap_copy_room_load

.section .text.ap_copy_room_clear_entry,"ax",%progbits
.balign 4
.global ap_copy_room_clear_entry
.type ap_copy_room_clear_entry, %function
.thumb_func
ap_copy_room_clear_entry:
    ldr r3, 1f
    bx r3
1: .word ap_copy_room_clear

.section .text.ap_copy_room_state_entry,"ax",%progbits
.balign 4
.global ap_copy_room_state_entry
.type ap_copy_room_state_entry, %function
.thumb_func
ap_copy_room_state_entry:
    ldr r3, 1f
    bx r3
1: .word ap_copy_room_state
