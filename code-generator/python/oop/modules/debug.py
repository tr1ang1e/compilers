from clang.cindex import Cursor


def print_cursor_info(cursor: Cursor):
    print("{:<15} {:<15} {:<15}".format(cursor.displayname,
                                        cursor.type.spelling,
                                        cursor.type.get_canonical().spelling))
