from modules.kind import Kind, Type
from modules.context import Context
from modules.handler import Handler
from modules.container import Container
from modules.wrapper import Wrapper
from clang.cindex import Cursor


def is_appropriate(cursor: Cursor, unit_spelling: str):
    # location
    is_from_given_file = False
    if cursor.location.file:  # can't get file from some cursors which point to system entities
        is_from_given_file = cursor.location.file.name == unit_spelling
    # kind
    kind = Kind()
    is_appropriate_kind = cursor.kind in kind.cursorKinds
    return is_from_given_file and is_appropriate_kind


def visitor_function(parent: Cursor, unit_spelling: str, container: Container):
    for cursor in parent.get_children():
        if is_appropriate(cursor, unit_spelling):
            type_data = Handler.handle_cursor(cursor)
            # add result to container
        visitor_function(cursor, unit_spelling, container)


def parse(context: Context, container: Container):
    for translation_unit in context.parse_next_file():
        print("Processing unit = {}".format(translation_unit.spelling))
        visitor_function(translation_unit.cursor, translation_unit.spelling, container)


def generate(wrapper: Wrapper, container: Container):
    pass


def main():
    context = Context()
    container = Container()
    wrapper = Wrapper(context.outputFile)

    parse(context, container)
    generate(wrapper, container)


if __name__ == "__main__":
    main()
