from django.db import models
from django.contrib.gis.db import models as geomodels
from django.db.models import JSONField
from district.models import DistrictForeign


class City(DistrictForeign):
    cityName = models.CharField(max_length=100, unique=True)
    abbreviation = models.CharField(max_length=5, blank=True, null=True)

    def __str__(self):
        return self.cityName


class CityMap(geomodels.Model):
    """
    Used for representing City boundary maps
    """
    feature_properties = JSONField(blank=True, null=True)
    boundary = geomodels.MultiPolygonField()
    city = models.ForeignKey(City, on_delete=models.CASCADE, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['city'],
                name='unique_boundary_per_city'
            )
        ]

    def __str__(self):
        return f"Map of {self.city}" if self.city else "CityMap"
