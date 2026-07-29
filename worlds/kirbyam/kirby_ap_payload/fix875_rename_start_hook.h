#ifndef KIRBYAM_FIX875_RENAME_START_HOOK_H
#define KIRBYAM_FIX875_RENAME_START_HOOK_H

/*
 * The fix-statues branch already defines the Issue #874 transition-start hook
 * in ap_payload.c.  Issue #875 needs a superset of that behavior.  Rename the
 * old symbol only while compiling ap_payload.c so the replacement in
 * statue_transition_fix.c owns the public symbol that patch_rom.py resolves.
 *
 * With -ffunction-sections and --gc-sections, the renamed implementation has
 * no references and is omitted from the final payload binary.
 */
#define ap_on_start_copy_ability_transition issue874_old_start_copy_ability_transition

#endif
