#ifnde HEADER2
#define HEADER2


#ifdef __linux__
#define MACROINT 0
#else
#define MACROINT 1
#endif

#ifdef _WIN32
#define MACROSTR "windows"
#else
#define MACROSTR "linux"
#endif

int justForCheckThatFileParsed;


#endif