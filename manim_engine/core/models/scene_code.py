from dataclasses import dataclass
from typing import Any


@dataclass
class VariableInfo:
    name: str
    value: Any
    var_type: str  # "int", "float", "str", "color", "tuple", "list", "bool"
    line_number: int
    editable: bool
