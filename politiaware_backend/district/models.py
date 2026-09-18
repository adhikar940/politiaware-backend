from django.db import models
from django.contrib.gis.db import models as geomodels
from django.db.models import JSONField
from state.models import State, StateForeign


class District(models.Model):
    state = models.ForeignKey(State, related_name='districts', on_delete=models.CASCADE, null=True, blank=True, default=None)
    districtName = models.CharField(max_length=50)
    headquarters = models.CharField(max_length=50, null=True, blank=True)
    revenueDivisions = models.CharField(max_length=100, null=True, blank=True)
    mandals = models.CharField(max_length=100, null=True, blank=True)
    abbreviation = models.CharField(max_length=5, blank=True, null=True)

    class Meta:
        unique_together = ('state', 'districtName')

    def __str__(self):
        return self.districtName


# Backward compatibility alias
Districts = District


class DistrictMap(geomodels.Model):
    """
    Used for representing District boundary maps
    """
    feature_properties = JSONField(blank=True, null=True)
    boundary = geomodels.MultiPolygonField()
    district = models.ForeignKey(District, on_delete=models.CASCADE, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['district'],
                name='unique_boundary_per_district'
            )
        ]

    def __str__(self):
        return f"Map of {self.district}" if self.district else "DistrictMap"


class DistrictForeign(StateForeign):
    """
    Abstract base model providing foreign keys to both State and District
    (inheriting state from StateForeign).
    """
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True, default=None)

    class Meta:
        abstract = True


DistrictForeignModel = DistrictForeign
