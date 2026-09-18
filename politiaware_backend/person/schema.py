"""
Strawberry GraphQL Enum queries for Politiaware Backend.
"""

from typing import List
import strawberry
from .enums import CasteCategoryEnum, GenderEnum, ReligionEnum


@strawberry.type
class EnumQuery:
    @strawberry.field
    def caste_categories(self) -> List[str]:
        return [e.value for e in CasteCategoryEnum]

    @strawberry.field
    def genders(self) -> List[str]:
        return [e.value for e in GenderEnum]

    @strawberry.field
    def religions(self) -> List[str]:
        return [e.value for e in ReligionEnum]