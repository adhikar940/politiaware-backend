from django.db import models
from django.contrib.gis.db import models as geomodels
from django.db.models import JSONField
from district.models import DistrictForeign


class Panchayat(DistrictForeign):
    taluk = models.ForeignKey('taluk.Taluk', on_delete=models.SET_NULL, null=True, blank=True, default=None)
    panchayatName = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['district', 'panchayatName'],
                name='unique_panchayat_per_district'
            )
        ]

    def __str__(self):
        return self.panchayatName


class PanchayatMap(geomodels.Model):
    """
    Used for representing Panchayat boundary maps
    """
    feature_properties = JSONField(blank=True, null=True)
    boundary = geomodels.MultiPolygonField()
    panchayat = models.ForeignKey(Panchayat, on_delete=models.CASCADE, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['panchayat'],
                name='unique_boundary_per_panchayat'
            )
        ]

    def __str__(self):
        return f"Map of {self.panchayat}" if self.panchayat else "PanchayatMap"

