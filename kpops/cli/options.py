from enum import Enum


class FilterType(str, Enum):
    INCLUDE = "include"
    EXCLUDE = "exclude"
