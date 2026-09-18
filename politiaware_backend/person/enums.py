# enums.py
from enum import Enum

class CasteCategoryEnum(Enum):
    OBC = "OBC"
    SC = "SC"
    ST = "ST"
    OC = "OC"

class GenderEnum(Enum):
    MALE = "Male"
    FEMALE = "Female"

class ReligionEnum(Enum):
    HINDU = "Hindu"
    MUSLIM = "Muslim"
    SIKH = "Sikh"
    CHRISTIAN = "Christian"
    BUDDHIST = "Buddhist"

class ReservationCategoryEnum(Enum):
    GEN = "GEN"
    SC = "SC"
    ST = "ST"

def enum_to_choices(enum_cls):
    # Helper to convert enum to Django choices
    # Ex Gender = (
    #     ('Male', 'Male'),
    #     ('Female', 'Female')
    # )
    return [(tag.value, tag.value) for tag in enum_cls]
