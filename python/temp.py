
class BaseEnumeration(object):
    """
    Common base class for named enumerations held in sync with Index.h values.

    Subclasses must define their own _kinds and _name_map members, as:
    _kinds = []
    _name_map = None
    These values hold the per-subclass instances and value-to-name mappings,
    respectively.

    """

    def __init__(self, value):
        if value >= len(self.__class__._kinds):
            self.__class__._kinds += [None] * (value - len(self.__class__._kinds) + 1)
        if self.__class__._kinds[value] is not None:
            raise ValueError('{0} value {1} already loaded'.format(
                str(self.__class__), value))
        self.value = value
        self.__class__._kinds[value] = self
        self.__class__._name_map = None


    def from_param(self):
        return self.value

    @property
    def name(self):
        """Get the enumeration name of this cursor kind."""
        if self._name_map is None:
            self._name_map = {}
            for key, value in self.__class__.__dict__.items():
                if isinstance(value, self.__class__):
                    self._name_map[value] = key
        return self._name_map[self]

    @classmethod
    def from_id(cls, id):
        if id >= len(cls._kinds) or cls._kinds[id] is None:
            raise ValueError('Unknown template argument kind %d' % id)
        return cls._kinds[id]

    def __repr__(self):
        return '%s.%s' % (self.__class__, self.name,)




class CursorKind(BaseEnumeration):
    """
    A CursorKind describes the kind of entity that a cursor points to.
    """

    # The required BaseEnumeration declarations.
    _kinds = []
    _name_map = None

    @staticmethod
    def get_all_kinds():
        """Return all CursorKind enumeration instances."""
        return [x for x in CursorKind._kinds if not x is None]

    def is_declaration(self):
        """Test if this is a declaration kind."""
        return conf.lib.clang_isDeclaration(self)



CursorKind.UNEXPOSED_DECL = CursorKind(1)
CursorKind.STRUCT_DECL = CursorKind(2)
CursorKind.UNION_DECL = CursorKind(3)
CursorKind.CLASS_DECL = CursorKind(4)
CursorKind.ENUM_DECL = CursorKind(5)