#include "parse_unit.h"

/* NOTES
 * 
 * libclang errors might appear in execution process, e.g.: 
 * "variable has incomplete type" and like this. It's OK and
 * made in purpose of parcing only given files without
 * managing both system and users header files.
 *
 * */

// TBD: add list of units to be parsed
// TBD: reimplement contatiners from separate variables to iterable array


/*--------------------------------------------------------------*
 *                          DEFINES                             *
 *--------------------------------------------------------------*/

#ifdef __linux__
#define SEP '/'
#elif _WIN32
#define SEP '\\'
#else
#endif

// trace macro
#define __FILENAME__ (strrchr(__FILE__, SEP) ? strrchr(__FILE__, SEP) + 1 : __FILE__)
#define _TRACE_(message) printf(" :: [%s] :: %s - %s - %d \n", message, __FILENAME__, __func__,  __LINE__)


/*--------------------------------------------------------------*
 *                            MAIN                              *
 *--------------------------------------------------------------*/

int main(int argc, char** argv)
{
    const char* unitName = "examples/unit.c"; 

    const char* argsList[] =  // https://gcc.gnu.org/onlinedocs/gcc/Preprocessor-Options.html
    { 
        "-I./examples/include",          
        "-D__linux__",
        "-U_WIN32",
        // additional = `clang -print-targets` , clang.llvm.org/docs/CrossCompilation.html
    };   
    
    int argsNumber = ARRAY_SIZE(argsList);                  

    // additional parser settings (add CXTranslationUnit_SingleFileParse to avoid includes parsing)
    enum CXTranslationUnit_Flags options = CXTranslationUnit_DetailedPreprocessingRecord | CXTranslationUnit_SkipFunctionBodies; 

    // provide shared context for creating translation units 
    // excludeDeclarationFromPCH = 0, displayDiagnostics = 1
    CXIndex index = clang_createIndex(0, 1);

    // parse specified unit (if error returns NULL without specifying error)  // TBD: parse list of units in a loop
    CXTranslationUnit unit = clang_parseTranslationUnit(
        index,          // CXIndex                          context
        unitName,       // const char*                      name of unit to parse (might be pass through the 'argv' in the same form as here)     
        argsList,       // const char**                     array of arguments to pass to parser
        argsNumber,     // int                              number of arguments to pass to parser
        0,              // struct CXUnsavedFile             unsaved files to parse
        0,              // unsigned int                     number of unsaved files to parse
        options         // enum CXTranslationUnit_Flags     additional parser settings
    );

    if (!unit)
    {
        _TRACE_("CXTranslationUnit, fail \n");
    }
    else
    {
        // prepare client data
        ClientData cData = { unit };
        CXClientData clangData = (CXClientData)&cData;

        // initiate traversal
        CXCursor root = clang_getTranslationUnitCursor(unit);
        clang_visitChildren(root, visitor_callback, clangData);
    }

    // free clang resources
    clang_disposeTranslationUnit(unit);
    clang_disposeIndex(index);

    // debug
    print_lists();

    // free programm resources
    dispose_containers();

    return 0;
}