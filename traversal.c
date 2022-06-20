
#include <clang-c/Index.h>      // for clang-c API
#include <stdio.h>
#include <string.h>


/* Description of clang-c API entities
 *
 *  :: clang_<name> is clang functions
 *  :: CX<name> is clang types
 * 
 * CXCursor = represents any of AST nodes 
 * CXString = type to handle clang string
 * 
 * 
 * 
 * 
 * */


void print_ast_cursor(CXCursor cursor)
{
    // allocate resources and get corresponding data
    CXString displayName = clang_getCursorDisplayName(cursor);      
   
    // print current cursor name
    const char* resultName = clang_getCString(displayName);
    printf(" :: cursor name = %s", resultName);

    // free resources of CXString 
    clang_disposeString(displayName);                               
}


int main(int argc, char** argv)
{
    // provide shared context for creating translation units 
    // excludeDeclarationFromPCH = 0, displayDiagnostics = 1
    CXIndex index = clang_createIndex(0, 1);






	printf(" :: success \n");

	return 0;
}