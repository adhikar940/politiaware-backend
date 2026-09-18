from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models as geomodels
from django.db.models import JSONField


class State(models.Model):
    status_choices = (
        ('State', 'State'),
        ('UT', 'UT'),
    )
    Statename = models.CharField(max_length=50, unique=True)
    capital = models.CharField(max_length=50, blank=True, default='')
    Status = models.CharField(max_length=6, choices=status_choices, default='State')
    abbreviation = models.CharField(max_length=5, blank=True, null=True)    
    oldname = models.CharField(max_length=50, unique=True, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['Statename'],
                name='unique_Statename'
            )
        ]

    def __str__(self):
        return self.Statename


class StateMap(geomodels.Model):
    """
    Used for representing State boundary maps
    """
    feature_properties = JSONField(blank=True, null=True)
    boundary = geomodels.MultiPolygonField()
    state = models.ForeignKey(State, on_delete=models.CASCADE, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['state'],
                name='unique_boundary_per_state'
            )
        ]

    def __str__(self):
        return f"Map of {self.state}" if self.state else "StateMap"


class StateForeign(models.Model):
    """
    Abstract base model providing a foreign key to State.
    """
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True, default=None)

    class Meta:
        abstract = True


StateForeignModel = StateForeign


class area(models.Model):
    formationdate = models.CharField(max_length=100, null=True, blank=True)
    areasqkm = models.IntegerField(null=True, blank=True, default=None)
    densitysqkm = models.IntegerField(null=True, blank=True, default=None)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()    

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['content_type', 'object_id'],
                name='unique_area_per_entity'
            )
        ]


class population(models.Model):
    YEAR_CHOICES = [
        (2011, '2011')
    ]
    totalpopulation = models.IntegerField(null=True, blank=True, default=None)
    malepopulation = models.IntegerField(null=True, blank=True, default=None)
    femalepopulation = models.IntegerField(null=True, blank=True, default=None)
    census_year = models.IntegerField(choices=YEAR_CHOICES, default=2011)
    DecadalGrowthRate = models.IntegerField(null=True, blank=True, default=None)
    LiteracyRate = models.IntegerField(null=True, blank=True, default=None)
    femtomaleSexRatio = models.CharField(max_length=100, null=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)    

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['content_type', 'object_id', 'census_year'],
                name='unique_entity_census_year'
            )
        ]
