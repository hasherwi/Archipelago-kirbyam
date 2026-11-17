.syntax unified
.cpu arm7tdmi
/* Native BL sites have dead LR (saved by their containing functions). All
 * remaining registers and incoming flags are saved before calling C. */
.section .text.battery_entries,"ax",%progbits
.thumb
.balign 4
.global ap_battery_hud_init
.type ap_battery_hud_init,%function
.thumb_func
ap_battery_hud_init:
.global ap_battery_hud_compare
.type ap_battery_hud_compare,%function
.thumb_func
ap_battery_hud_compare:
.global ap_battery_hud_cache
.type ap_battery_hud_cache,%function
.thumb_func
ap_battery_hud_cache:
.global ap_battery_hud_alt_compare
.type ap_battery_hud_alt_compare,%function
.thumb_func
ap_battery_hud_alt_compare:
.global ap_battery_hud_alt_cache
.type ap_battery_hud_alt_cache,%function
.thumb_func
ap_battery_hud_alt_cache:
.global ap_battery_hud_render
.type ap_battery_hud_render,%function
.thumb_func
ap_battery_hud_render:
.global ap_battery_refill_a
.type ap_battery_refill_a,%function
.thumb_func
ap_battery_refill_a:
.global ap_battery_refill_b
.type ap_battery_refill_b,%function
.thumb_func
ap_battery_refill_b:
.global ap_battery_death_a
.type ap_battery_death_a,%function
.thumb_func
ap_battery_death_a:
.global ap_battery_death_b
.type ap_battery_death_b,%function
.thumb_func
ap_battery_death_b:
.global ap_battery_spend
.type ap_battery_spend,%function
.thumb_func
ap_battery_spend:
.global ap_battery_pickup
.type ap_battery_pickup,%function
.thumb_func
ap_battery_pickup:
.global ap_battery_goal_pickup
.type ap_battery_goal_pickup,%function
.thumb_func
ap_battery_goal_pickup:
    push {r3}
    ldr r3, 1f
    bx r3
    .balign 4
1:  .word ap_battery_dispatch_arm
.section .aphub,"ax",%progbits
.arm
.balign 4
ap_battery_dispatch_arm:
    stmdb sp!, {r0-r12,lr}
    ldr r3, [sp,#56]
    str r3, [sp,#12]
    mrs r3, cpsr
    stmdb sp!, {r3}
    ldr r3, =0x08033A03
    cmp lr, r3
    beq ap_battery_hud_init_arm
    ldr r3, =0x08033F0B
    cmp lr, r3
    beq ap_battery_hud_compare_arm
    ldr r3, =0x08034005
    cmp lr, r3
    beq ap_battery_hud_cache_arm
    ldr r3, =0x08034121
    cmp lr, r3
    beq ap_battery_hud_alt_compare_arm
    ldr r3, =0x0803415F
    cmp lr, r3
    beq ap_battery_hud_alt_cache_arm
    ldr r3, =0x08034D9F
    cmp lr, r3
    beq ap_battery_hud_render_arm
    ldr r3, =0x0804FFE9
    cmp lr, r3
    beq ap_battery_refill_a_arm
    ldr r3, =0x080501B1
    cmp lr, r3
    beq ap_battery_refill_b_arm
    ldr r3, =0x080501BF
    cmp lr, r3
    beq ap_battery_death_a_arm
    ldr r3, =0x08050831
    cmp lr, r3
    beq ap_battery_death_b_arm
    ldr r3, =0x0805735F
    cmp lr, r3
    beq ap_battery_spend_arm
    ldr r3, =0x081231F7
    cmp lr, r3
    beq ap_battery_pickup_arm
    ldr r3, =0x0801B2E7
    cmp lr, r3
    beq ap_battery_goal_pickup_arm
    /* Not an API: an unknown callsite performs no memory operation. */
    ldmia sp!, {ip}
    msr cpsr_f, ip
    ldmia sp!, {r0-r12,lr}
    add sp, sp, #4
    bx lr
    .ltorg
.macro ENTRY name
.arm
.balign 4
\name\()_arm:
.endm
.macro CALL target
    ldr ip, =\target
    mov lr, pc
    bx ip
.endm
.macro RETURN
    ldmia sp!, {ip}
    msr cpsr_f, ip
    ldmia sp!, {r0-r12,lr}
    add sp, sp, #4
    bx lr
    .ltorg
.endm

ENTRY ap_battery_hud_init
    ldr r0, [sp,#4]
    CALL ap_battery_visible
    str r0, [sp,#4]
    ldr r1, [sp,#28]
    strb r0, [r1,#12]
    RETURN

ENTRY ap_battery_hud_compare
    ldr r0, [sp,#12]
    CALL ap_battery_visible
    str r0, [sp,#12]
    ldr r1, [sp,#4]
    ldr r2, [sp,#12]
    cmp r1, r2
    mrs r1, cpsr
    str r1, [sp]
    RETURN

ENTRY ap_battery_hud_cache
    ldr r0, [sp,#16]
    CALL ap_battery_visible
    str r0, [sp,#4]
    ldr r1, [sp,#24]
    strb r0, [r1,#12]
    RETURN

ENTRY ap_battery_hud_alt_compare
    ldr r0, [sp,#20]
    CALL ap_battery_visible
    str r0, [sp,#4]
    ldr r1, [sp,#8]
    ldr r2, [sp,#4]
    cmp r1, r2
    mrs r1, cpsr
    str r1, [sp]
    RETURN

ENTRY ap_battery_hud_alt_cache
    ldr r0, [sp,#20]
    CALL ap_battery_visible
    str r0, [sp,#4]
    ldr r1, [sp,#28]
    strb r0, [r1,#12]
    RETURN

ENTRY ap_battery_hud_render
    ldr r0, [sp,#4]
    CALL ap_battery_visible
    str r0, [sp,#4]
    ldr r1, [sp,#4]
    cmp r1, #1
    mrs r1, cpsr
    str r1, [sp]
    RETURN

ENTRY ap_battery_refill_a
    ldr r0, [sp,#8]
    mov r1, #0
    CALL ap_battery_native
    ldr r2, [sp]
    msr cpsr_f, r2
    movs r2, #3
    mrs r2, cpsr
    str r2, [sp]
    str r0, [sp,#4]
    RETURN

ENTRY ap_battery_refill_b
    ldr r0, [sp,#20]
    mov r1, #0
    CALL ap_battery_native
    ldr r2, [sp]
    msr cpsr_f, r2
    movs r2, #3
    mrs r2, cpsr
    str r2, [sp]
    str r0, [sp,#4]
    RETURN

ENTRY ap_battery_death_a
    ldr r0, [sp,#20]
    mov r1, #1
    CALL ap_battery_native
    ldr r2, [sp]
    msr cpsr_f, r2
    movs r2, #1
    mrs r2, cpsr
    str r2, [sp]
    str r0, [sp,#4]
    RETURN

ENTRY ap_battery_death_b
    ldr r0, [sp,#8]
    mov r1, #1
    CALL ap_battery_native
    ldr r2, [sp]
    msr cpsr_f, r2
    movs r2, #1
    mrs r2, cpsr
    str r2, [sp]
    str r0, [sp,#4]
    RETURN

ENTRY ap_battery_spend
    ldr r0, [sp,#4]
    mov r1, #2
    CALL ap_battery_native
    ldr r2, [sp,#8]
    subs r2, r2, #1
    mrs r2, cpsr
    str r2, [sp]
    str r0, [sp,#8]
    RETURN

ENTRY ap_battery_pickup
    ldr r0, [sp,#8]
    mov r1, #3
    CALL ap_battery_native
    ldr r2, [sp,#4]
    adds r2, r2, #1
    mrs r2, cpsr
    str r2, [sp]
    str r0, [sp,#4]
    RETURN

ENTRY ap_battery_goal_pickup
    ldr r0, [sp,#8]
    mov r1, #3
    CALL ap_battery_native
    ldr r2, [sp,#4]
    adds r2, r2, #1
    mrs r2, cpsr
    str r2, [sp]
    str r0, [sp,#4]
    RETURN
