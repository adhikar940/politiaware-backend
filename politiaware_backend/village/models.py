from django.db import models
from django.contrib.gis.db import models as geomodels
from django.db.models import JSONField
from district.models import DistrictForeign


class Village(DistrictForeign):
    panchayat = models.ForeignKey('panchayat.Panchayat', on_delete=models.SET_NULL, null=True, blank=True, default=None)
    villageName = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['district', 'villageName'],
                name='unique_village_per_district'
            )
        ]

    def __str__(self):
        return self.villageName


class VillageMap(geomodels.Model):
    """
    Used for representing Village boundary maps
    """
    feature_properties = JSONField(blank=True, null=True)
    boundary = geomodels.MultiPolygonField()
    village = models.ForeignKey(Village, on_delete=models.CASCADE, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['village'],
                name='unique_boundary_per_village'
            )
        ]

    def __str__(self):
        return f"Map of {self.village}" if self.village else "VillageMap"

