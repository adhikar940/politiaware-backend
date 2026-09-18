from django.db import models
from django.contrib.gis.db import models as geomodels
from district.models import DistrictForeign
from party.models import Party
from person.models import person
from person.enums import ReservationCategoryEnum, enum_to_choices
from loksabha.models import LoksabhaConstituency

class AssemblyConstituency(DistrictForeign):
    loksabhaConstituency = models.ForeignKey(LoksabhaConstituency, on_delete=models.PROTECT, null=True, blank=True, default=None)
    assemblyConstituencyName = models.CharField(max_length=100)
    reservationCategory = models.CharField(
        max_length=10,
        choices=enum_to_choices(ReservationCategoryEnum),
        default=ReservationCategoryEnum.GEN.value,
    )
    isExist = models.BooleanField(default=True, null=True, blank=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['state', 'loksabhaConstituency', 'assemblyConstituencyName'],
                name='unique_assemblyconstituency'
            )
        ]

    def __str__(self):
        return self.assemblyConstituencyName


class AssemblyConstituencyMap(geomodels.Model):
    """
    Used for representing assembly constituencies
    """
    boundary = geomodels.MultiPolygonField()
    assemblyConstituency = models.ForeignKey(AssemblyConstituency, on_delete=models.SET_NULL, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['assemblyConstituency'],
                name='unique_boundary_per_assembly_constituency'
            )
        ]

    def __str__(self):
        return f"Map of {self.assemblyConstituency}" if self.assemblyConstituency else "AssemblyConstituencyMap"


class MLA(person):    
    party = models.ForeignKey(Party, on_delete=models.CASCADE, null=True, blank=True, default=None)
    isPresent = models.BooleanField(default=True, null=True, blank=True)
    constituency = models.ForeignKey(AssemblyConstituency, on_delete=models.SET_NULL, null=True, blank=True, default=None)

    class Meta:
        unique_together = ['name']

    def __str__(self):
        return f"{self.name} - {self.constituency}" if self.constituency else self.name



