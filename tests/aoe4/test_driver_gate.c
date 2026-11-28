#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include "aoe_driver_compat.h"

int main(void)
{
    const char *game = "C:\\games\\RelicCardinal.exe";
    unsetenv("HB_AOE4");
    unsetenv("HB_AOE4_DISABLED");
    unsetenv("HB_AOE4_ADL");
    assert(!aoe_driver_compat_allowed(1, game));
    setenv("HB_AOE4", "1", 1);
    assert(aoe_driver_compat_allowed(1, game));
    assert(aoe_driver_compat_allowed(1, "C:\\games\\RELICCARDINAL.EXE"));
    assert(!aoe_driver_compat_allowed(0, game));
    assert(!aoe_driver_compat_allowed(1, "C:\\games\\other.exe"));
    assert(!aoe_driver_compat_allowed(1, "RelicCardinal.exe.bak"));
    assert(!aoe_driver_compat_allowed(1, NULL));
    setenv("HB_AOE4_SOFTFAULT_BRIDGE", "1", 1);
    assert(!aoe_driver_compat_allowed(0, game)); /* inherited markers do not verify a child */
    setenv("HB_AOE4_ADL", "0", 1);
    assert(!aoe_driver_compat_allowed(1, game));
    setenv("HB_AOE4_ADL", "1", 1);
    assert(aoe_driver_compat_allowed(1, game));
    setenv("HB_AOE4_DISABLED", "1", 1);
    assert(!aoe_driver_compat_allowed(1, game));
    unsetenv("HB_AOE4_DISABLED");
    setenv("HB_AOE4", "0", 1);
    assert(!aoe_driver_compat_allowed(1, game));
    puts("PASS: ADL requires the verified AoE image and opt-in; other games, children and off switches stay off");
}
