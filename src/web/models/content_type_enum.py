from enum import StrEnum, auto

class ContentTypeEnum(StrEnum):
    MARKDOWN = auto()
    # DATAFRAME = auto()
    # EXCEPTION = auto()
    # MATPLOTLIB = auto()
    # IMAGE = auto()
    FILE = auto()

__all__ = ["ContentTypeEnum"]