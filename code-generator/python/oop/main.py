from modules.context import Context
from modules.handler import Handler
from modules.container import Container
from modules.wrapper import Wrapper
from clang.cindex import Cursor


def visitor_function(cursor: Cursor, unit_spelling: str, container: Container):
    pass


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
