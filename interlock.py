from typing import List


class Indication:
    def __init__(self, rank, path, desc, role, expected_val_pre, expected_val_post ):
        if role not in ['initiator', 'final_element', 'both']:
            raise TypeError(f"Indicator role must be one of the following strings: initiator, final_element, both')")
        self.rank = rank  # 0 for indication of physical process condition; > 0 for surrogate indications
        self.path = path
        self.expected_val_pre = expected_val_pre
        self.expected_val_post = expected_val_post
        self.role = role
        self.desc = desc

    def __repr__(self):
        return f"{self.__class__.__name__}({self.rank!r}, {self.path!r}, {self.desc!r}, " \
               f"{self.role!r}, {self.expected_val_pre!r}, {self.expected_val_post!r})"


class Component:
    def __init__(self, name, indications: List[Indication], desc=''):
        if len(indications) == 0:
            raise TypeError("Component's indications list may not be empty")
        self.name = name
        self.desc = desc
        self.indications = indications

    @property
    def role(self):
        """Determine component role by interrogating roles of indications"""
        if len(set([i.role for i in self.indications])) == 1:
            return self.indications[0].role
        else:
            return 'both'

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name!r}, {self.indications!r}, {self.desc!r})"


class Interlock:
    def __init__(self, name, components: List[Component], desc):
        self.name = name
        self.components = components
        self.desc = desc

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name!r}, {self.components!r}, {self.desc!r})"
