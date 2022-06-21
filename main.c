#include "parse_unit.h"


// TBD: fix problem with duplicating when typedef
// TBD: parse macros

/*--------------------------------------------------------------*
 *                          DEFINES                             *
 *--------------------------------------------------------------*/

#ifdef __linux__
#define SEP '/'
#elif _WIN32
#define SEP '\\'
#endif

// trace macro
#define __FILENAME__ (strrchr(__FILE__, SEP) ? strrchr(__FILE__, SEP) + 1 : __FILE__)
#define _TRACE_(message) printf(" :: [%s] :: %s - %s - %d \n", message, __FILENAME__, __func__,  __LINE__)


/*--------------------------------------------------------------*
 *                            MAIN                              *
 *--------------------------------------------------------------*/

int main(int argc, char** argv)
{
    // settings
    const char* unitName = "examples/unit.c";     // TBD: add list of units to be parsed
    const char** argsList = NULL;                 // if any args, transform to:  const char* argsList[] = {..., ...};
    int argsNumber = 0;                           // if any args, transform to:  int argsNumber = sizeof(argsList);

    // provide shared context for creating translation units 
    // excludeDeclarationFromPCH = 0, displayDiagnostics = 1
    CXIndex index = clang_createIndex(0, 1);

    // parse specified unit (if error returns NULL without specifying error)  // TBD: parse list of units in a loop
    CXTranslationUnit unit = clang_parseTranslationUnit(
        index,          // CXIndex                  context
        unitName,       // const char*              name of unit to parse (might be pass through the 'argv' in the same form as here)     
        argsList,       // const char**             array of arguments to pass to parser
        argsNumber,     // int                      number of arguments to pass to parser
        0,              // struct CXUnsavedFile     unsaved files to parse
        0,              // unsigned int             number of unsaved files to parse
        CXTranslationUnit_SkipFunctionBodies        // enum CXTranslationUnit_Flags
    );

    if (!unit)
    {
        _TRACE_("CXTranslationUnit, fail");
    }
    else
    {
        _TRACE_("CXTranslationUnit, success");

        CXCursor root = clang_getTranslationUnitCursor(unit);
        clang_visitChildren(root, visitor_callback, NULL);
    }

    // free resources
    clang_disposeTranslationUnit(unit);
    clang_disposeIndex(index);

    return 0;
}