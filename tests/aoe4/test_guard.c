#define _GNU_SOURCE
#include <assert.h>
#include <fcntl.h>
#include <stdio.h>
#include "aoe_driver_compat.h"
int main(void)
{
    unsigned char abc[32] = {0xba,0x78,0x16,0xbf,0x8f,0x01,0xcf,0xea,
        0x41,0x41,0x40,0xde,0x5d,0xae,0x22,0x23,0xb0,0x03,0x61,0xa3,
        0x96,0x17,0x7a,0x9c,0xb4,0x10,0xff,0x61,0xf2,0x00,0x15,0xad};
    char path[]="/tmp/highball-aoe-guard-XXXXXX", bootstrap[64];
    int fd=mkstemp(path), pipes[2];
    const char *game="C:\\games\\RelicCardinal.exe";
    assert(fd>=0);unlink(path);
    assert(aoe_game_name("C:\\games\\RELICCARDINAL.EXE"));
    assert(aoe_game_name("/games/RelicCardinal.exe"));
    assert(!aoe_game_name(NULL) && !aoe_game_name("RelicCardinal.exe.bak"));
    unsetenv("HB_AOE4");unsetenv("HB_AOE4_DISABLED");unsetenv("HB_AOE4_ADL");
    assert(!aoe_driver_compat_allowed(1,game));
    setenv("AOELAB_CODE_CACHE_GAME","1",1); /* the old trial switch does not opt in */
    assert(!aoe_patch_requested());
    setenv("HB_AOE4","0",1);assert(!aoe_patch_requested());
    setenv("HB_AOE4","yes",1);assert(!aoe_patch_requested());
    setenv("HB_AOE4","1",1);assert(aoe_patch_requested());
    assert(aoe_driver_compat_allowed(1,game));
    assert(!aoe_driver_compat_allowed(0,game));
    assert(!aoe_driver_compat_allowed(1,"other.exe"));
    setenv("HB_AOE4_ADL","0",1);assert(!aoe_driver_compat_allowed(1,game));
    unsetenv("HB_AOE4_ADL");
    setenv("HB_AOE4_DISABLED","1",1);assert(!aoe_patch_requested());
    assert(!aoe_driver_compat_allowed(1,game));
    snprintf(bootstrap,sizeof(bootstrap),"x87sidecar.%ld",(long)getpid());
    assert(aoe_bootstrap_is_current(bootstrap));
    assert(!aoe_bootstrap_is_current(NULL) && !aoe_bootstrap_is_current("x87sidecar.0"));
    strcat(bootstrap,"junk");assert(!aoe_bootstrap_is_current(bootstrap));
    assert(!aoe_hash_fd_matches(fd,abc));
    assert(write(fd,"abc",3)==3 && lseek(fd,1,SEEK_SET)==1);
    assert(aoe_hash_fd_matches(fd,abc) && lseek(fd,0,SEEK_CUR)==1);
    assert(!aoe_hash_fd_matches(fd,aoe_supported_sha256));
    assert(pwrite(fd,"x",1,0)==1 && !aoe_hash_fd_matches(fd,abc));
    close(fd);assert(!aoe_hash_fd_matches(-1,abc));
    assert(!pipe(pipes) && !aoe_hash_fd_matches(pipes[0],abc));
    close(pipes[0]);close(pipes[1]);
    puts("PASS: executable name, opt-in flags, ADL scope, PID bootstrap, descriptor hash, file offset, refusals");
}
