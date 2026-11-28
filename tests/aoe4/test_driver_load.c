/* Build with x86_64-w64-mingw32-gcc -O2 -static, then copy to RelicCardinal.exe
 * and OtherGameProbe.exe. With HB_AOE4=1 HB_AOE4_CACHE=0, the game probe takes
 * "present [child Windows path]"; the other probe takes no arguments. With
 * HB_AOE4_ADL=0, run the game probe without arguments. Keep ADL out of this folder. */
#include <windows.h>
#include <stdio.h>
#include <string.h>

struct versions { char driver[256], catalyst[256], web_link[256]; };
typedef int (__cdecl *versions_fn)(struct versions *);

int main(int argc, char **argv)
{
    HMODULE module = LoadLibraryA("atiadlxx.dll");
    struct versions info = {{0}};
    versions_fn query;
    int present = argc >= 2 && !strcmp(argv[1], "present");
    if (!module)
    {
        printf("atiadlxx absent, error=%lu\n", GetLastError());
        return present ? 1 : 0;
    }
    if (!present) { puts("FAIL: private ADL exposed to a launch outside its gate"); return 2; }
    query = (versions_fn)GetProcAddress(module, "ADL_Graphics_Versions_Get");
    if (!query || query(&info) || strncmp(info.driver, "99.", 3)) return 3;
    printf("PASS: gated ADL reports %s\n", info.driver);
    if (argc == 3)
    {
        STARTUPINFOA startup = {sizeof(startup)};
        PROCESS_INFORMATION process;
        DWORD code;
        char command[32768];
        snprintf(command, sizeof(command), "\"%s\"", argv[2]);
        if (!CreateProcessA(NULL, command, NULL, NULL, FALSE, 0, NULL, NULL, &startup, &process)) return 4;
        WaitForSingleObject(process.hProcess, INFINITE);
        if (!GetExitCodeProcess(process.hProcess, &code)) return 5;
        CloseHandle(process.hThread);
        CloseHandle(process.hProcess);
        if (code) return 6;
        puts("PASS: child inherits the environment but cannot load the private ADL");
    }
    FreeLibrary(module);
    return 0;
}
