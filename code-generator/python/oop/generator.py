from modules import Kinds, Writer, Parser
from clang.cindex import CursorKind


# TODO: remove logic with typedefs replacement
# TODO: add logic of nested structures handling
# TODO: add logic of handling only once to nested structures handling


def register_type(cursor, types_registrator):
    # transparent for first typedefs iteration
    if cursor.type == CursorKind.TYPEDEF_DECL:
        return True
    # avoid double handling
    elif cursor not in types_registrator:
        types_registrator.append(cursor)
        return True


def is_appropriate(cursor, unit_spelling, kinds, types_registrator):
    # location
    is_from_given_file = False
    if cursor.location.file:  # can't get file from some cursors which points to system entities
        is_from_given_file = cursor.location.file.name == unit_spelling
    # kind
    is_appropriate_kind = cursor.kind in kinds
    # registered
    is_registered = register_type(cursor, types_registrator)
    return is_from_given_file and is_appropriate_kind and is_registered


def visitor_function(parent, parser, writer, kinds, types_registrator):
    for cursor in parent.get_children():
        if is_appropriate(cursor, parser.currentUnit.spelling, kinds, types_registrator):
            type_instance = Kinds().get_instance(cursor, parser.currentUnit)
            type_instance.handle()
            if type_instance.name is not None:  # some instances should be skipped
                writer.update_containers(type_instance)
        visitor_function(cursor, parser, writer, kinds, types_registrator)


def traverse_ast(parser, writer, kinds, types_registrator):
    for translation_unit in parser.parse_next_file():
        visitor_function(translation_unit.cursor, parser, writer, kinds, types_registrator)


def main():
    parser = Parser()
    writer = Writer()
    types_registrator = list()

    print(":: Preparing. Processing typedefs ")
    traverse_ast(parser, writer, [CursorKind.TYPEDEF_DECL], types_registrator)

    print(":: Processing macros, user types and functions ")
    traverse_ast(parser, writer, [kind for kind in Kinds.cursorKinds.keys() if kind != CursorKind.TYPEDEF_DECL], types_registrator)

    print(":: Generating wrapper")
    writer.generate_output(parser.outputFile, parser.files, parser.project)


if __name__ == "__main__":
    main()
