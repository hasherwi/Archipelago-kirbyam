/* Standalone position-independent Thumb guard, appended by statue_art.py only
 * for Completely Random statue visuals. No shared base-patch rebuild required.
 * Input r0 = native Sprite*. Only custom animation 0x384, variant 37 clears
 * Sprite::unk8 horizontal flip (0x400). ObjectBase flags remain untouched.
 * The displaced USA DisplaySprite prologue is replayed exactly before resuming.
 * Assemble for ARM7TDMI and objcopy .text to verify STATUE_FACING_HOOK bytes.
 */
.syntax unified
.cpu arm7tdmi
.thumb
.text
.align 2
.global ap_statue_facing
.thumb_func
ap_statue_facing:
    ldrh r1, [r0, #12]
    movs r2, #0xe1
    lsls r2, r2, #2
    cmp r1, r2
    bne original
    ldrb r1, [r0, #26]
    cmp r1, #37
    bne original
    ldr r1, [r0, #8]
    movs r2, #4
    lsls r2, r2, #8
    bics r1, r2
    str r1, [r0, #8]
original:
    push {r4, r5, r6, r7, lr}
    mov r7, r10
    mov r6, r9
    mov r5, r8
    ldr r3, resume
    bx r3
.align 2
resume:
    .word 0x08156055
