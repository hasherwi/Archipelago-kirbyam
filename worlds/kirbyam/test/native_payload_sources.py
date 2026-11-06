"""Link shipping payload modules into mapped-memory host harnesses."""
from pathlib import Path


def link_payload_modules(source: str, payload: Path, *, native_start: str | None = None) -> str:
    # Keep native shared-save/Goal Game logic in these regressions. The harness
    # adapts only the native startup call when testing its color-order behavior.
    for name in ('shared_save.c', 'goal_game.c'):
        path = payload / name
        if path.exists():
            module = path.read_text()
            if native_start is not None:
                module = module.replace('0x080332BDu', '&' + native_start)
            source += '\n' + module
    source = 'static void host_shared_active(void);\n' + source
    source += r"""
/* Establish a genuine active-context fixture without replacing its validator. */
static void host_shared_active(void) {
    uint32_t task=*(uint32_t*)0x02020FACu;
    if (!task) task=0x03001200u;
    *(uint32_t*)0x02020FACu=task;
    *(uint16_t*)(task+2)=1; *(uint16_t*)(task+4)=1;
    *(uint16_t*)(task+6)=0x6000; *(uint32_t*)(task+8)=0x0803EE19u;
    *(uint16_t*)(task+16)=0x3000; *(uint16_t*)(task+18)=0;
    *(uint8_t*)0x03006000u=0;
    *(uint16_t*)0x0203AD48u=0;
    *(uint8_t*)0x0203AD30u=1; *(uint8_t*)0x0203AD3Cu=0;
    *(uint32_t*)0x0203AD10u=0;
    ap_shared_record_init((volatile uint32_t*)0x02028C68u,
                          (volatile uint32_t*)0x08F00000u);
    *AP_SHARED_CONTEXT=(struct ApSharedContext){1,1,0,0,0,task,0,0x41505331u,0};
}
"""
    return source
