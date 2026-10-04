#define _GNU_SOURCE
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
typedef int BOOL;
BOOL aoe_game_verified=1;
typedef unsigned char BYTE; typedef size_t SIZE_T;
static int main_argc=1; static char *main_argv[]={"RelicCardinal.exe"};
#define GetCurrentProcess() 0
#define MEM_RESERVE 1
#define MEM_COMMIT 2
#define MEM_RELEASE 4
#define PAGE_EXECUTE_READWRITE 7
static int NtAllocateVirtualMemory(int h, void **p, int z, SIZE_T *n, int flags, int prot) {
 (void)h;(void)z;(void)flags;(void)prot;
 void *r=mmap(*p,*n,PROT_READ|PROT_WRITE|PROT_EXEC,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
 if(r==MAP_FAILED) return 1;
 if(r!=*p){munmap(r,*n);return 1;}
 *p=r;return 0;
}
static int NtFreeVirtualMemory(int h,void **p,SIZE_T *n,int flags) { (void)h;(void)n;(void)flags;return munmap(*p,262144*64); }
static SIZE_T virtual_uninterrupted_read_memory(const void *p,void *q,SIZE_T n) {memcpy(q,p,n);return n;}
#include "aoe_code_cache.h"
int main(int argc,char **argv) {
 if(argc>1 && !strcmp(argv[1],"unverified")){aoe_game_verified=0;setenv("AOELAB_CODE_CACHE_GAME","1",1);}
 if(argc>1 && !strcmp(argv[1],"other-game")){main_argv[0]="other.exe";setenv("AOELAB_CODE_CACHE_GAME","1",1);}
 if(argc>1){assert(aoe_cache_target(0x140100000ULL)==0x140100000ULL);assert(!aoe_cache_attempted);puts("PASS: cache refuses disabled / unverified / other-game profile");return 0;}
 BYTE *ring=mmap((void*)0x140100000ULL,4096,PROT_READ|PROT_WRITE|PROT_EXEC,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);assert(ring!=(void*)MAP_FAILED && ring==(void*)0x140100000ULL);
 BYTE code[]={0xb8,42,0,0,0,0xc3}; memcpy(ring,code,sizeof code);memcpy(ring+32,code,sizeof code);
 setenv("AOELAB_CODE_CACHE_GAME","1",1);setenv("AOELAB_CODE_CACHE_TEST_RING","0x140100000",1);
 uint64_t a=aoe_cache_target((uint64_t)ring),b=aoe_cache_target((uint64_t)ring+32);assert(a!=(uint64_t)ring);assert(a==b);assert(aoe_cache_used==1);
 assert(((int(*)(void))(uintptr_t)a)()==42);assert(!memcmp(ring,code,sizeof code));assert(aoe_cache_logical_pc(b+2)==(uint64_t)ring+34);
 ring[64]=0xe8;assert(aoe_cache_target((uint64_t)ring+64)==(uint64_t)ring+64);
 assert(aoe_cache_target(0x1000)==0x1000);
 puts("PASS: deduplication, executable result, original bytes, PC mapping, fallback");
}
