#include "parse_unit.h"

/* NOTES
 * 
 * Libclang errors might appear in execution process, e.g.: 
 * "variable has incomplete type" and like this. It's OK and
 * made in purpose of parcing only given files without
 * managing both system and users header files.
 *
 * */

// TBD: fix problem with duplicating when typedef (see may be canonical)  // check previous structure (if the same then skip)
// TBD: parse macros = clang_Cursor_isMacroFunctionLike() 
// TBD: enum constants value = clang_getEnumConstantDeclValue()
// TBD: add callback logic
// TBD: parse underlying typedef type = clang_getTypedefDeclUnderlyingType()
// TBD: (?) combine visitor callbacks into one function
// TBD: rename parent to parent, child to child

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
    // main settings
    const char* unitName = "examples/unit.c";               // TBD: add list of units to be parsed
    const char* argsList[] = { "-I./examples/include" };    // -I<headers_path> 
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
        _TRACE_("CXTranslationUnit, fail");
    }
    else
    {
        _TRACE_("CXTranslationUnit, success");

        // prepare client data
        ClientData cData = { unit };
        CXClientData clangData = (CXClientData)&cData;

        // initiate traversal
        CXCursor root = clang_getTranslationUnitCursor(unit);
        // clang_visitChildren(root, visitor_parent_callback, clangData);
         clang_visitChildren(root, visitor_callback, clangData);
    }

    // free resources
    clang_disposeTranslationUnit(unit);
    clang_disposeIndex(index);

    return 0;
}