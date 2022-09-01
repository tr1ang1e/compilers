from modules import Kinds, Writer, Parser
from clang.cindex import Cursor, CursorKind


# TODO: remove logic with typedefs replacement
# TODO: add logic of nested structures handling
# TODO: add logic of handling only once to nested structures handling


def is_appropriate(cursor, parser, kinds):
    # location
    is_from_given_file = False
    if cursor.location.file:  # can't get file from some cursors which points to system entities
        is_from_given_file = cursor.location.file.name == parser.currentUnit.spelling
    # kind
    is_appropriate_kind = cursor.kind in kinds
    # registered
    is_registered = parser.register_cursor(cursor)
    return is_from_given_file and is_appropriate_kind and is_registered


def visitor_function(parent, parser, writer, kinds):
    for cursor in parent.get_children():
        if is_appropriate(cursor, parser, kinds):
            type_instance = Kinds().get_instance(cursor, parser, writer)    # keep instance context
            type_instance.handle()
            if type_instance.name is not None:  # some instances should be skipped
                writer.update_containers(type_instance)
        visitor_function(cursor, parser, writer, kinds)


def traverse_ast(parser, writer, kinds):
    for translation_unit in parser.parse_next_file():
        visitor_function(translation_unit.cursor, parser, writer, kinds)


def main():
    parser = Parser()
    writer = Writer()

    print(":: Preparing. Processing typedefs ")
    traverse_ast(parser, writer, [CursorKind.TYPEDEF_DECL])

    print(":: Processing macros, user types and functions ")
    # traverse_ast(parser, writer, [kind for kind in Kinds.cursorKinds.keys() if kind != CursorKind.TYPEDEF_DECL])
    #
    # new
    kinds = [kind for key in Kinds.cursorKinds.keys() if key != (CursorKind.TYPEDEF_DECL, ) for kind in key]
    traverse_ast(parser, writer, kinds)


    print(":: Generating wrapper")
    writer.generate_output(parser.outputFile, parser.files, parser.project)


if __name__ == "__main__":
    main()
