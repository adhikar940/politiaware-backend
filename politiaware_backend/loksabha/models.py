from django.db import models
from django.contrib.gis.db import models as geomodels
from district.models import DistrictForeign
from party.models import Party
from person.models import person
from person.enums import ReservationCategoryEnum, enum_to_choices
from django.core.exceptions import ValidationError

class LoksabhaConstituency(DistrictForeign):
    loksabhaConstituencyName = models.CharField(max_length=100)
    reservationCategory = models.CharField(
        max_length=10,
        choices=enum_to_choices(ReservationCategoryEnum),
        default=ReservationCategoryEnum.GEN.value,
    )
    isExist = models.BooleanField(default=True, null=True, blank=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['state', 'district', 'loksabhaConstituencyName'],
                name='unique_loksabhaconstituency'
            )
        ]

    def __str__(self):
        return self.loksabhaConstituencyName

class LoksabhaConstituencyMap(geomodels.Model):
    """
    Used for representing loksabha constituencies
    """    
    boundary = geomodels.MultiPolygonField()
    loksabhaConstituency = models.ForeignKey(LoksabhaConstituency, on_delete=models.SET_NULL, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['loksabhaConstituency'],
                name='unique_boundary_per_constituency'
            )
        ]

    def __str__(self):
        return f"Map of {self.loksabhaConstituency}" if self.loksabhaConstituency else "LoksabhaConstituencyMap"


class LokSabhaMP(person):    
    party = models.ForeignKey(Party, on_delete=models.CASCADE, null=True, blank=True, default=None)
    isPresent = models.BooleanField(default=True, null=True, blank=True)
    constituency = models.ForeignKey(LoksabhaConstituency, on_delete=models.SET_NULL, null=True, blank=True, default=None)
    class Meta:
        unique_together = ['name']

    def __str__(self):
        return f"{self.name} - {self.constituency}" if self.constituency else self.name
    
'''class loksabhapersonal1(personal):
    mp = models.ForeignKey(LokSabha, on_delete=models.SET_NULL, null=True,)
    class Meta:
        unique_together = ['mp']
    def __str__(self):
        return '%s' % (self.mp)'''
###############################################################################################################
#           SESSIONS MODELS- Loksabha
###############################################################################################################
# Loksabha Individual Sessions
'''class Loksabha_Session(models.Model):
    Loksabha_MP_Name = models.ForeignKey(LokSabha, on_delete=models.SET_NULL, null=True, default='')
    Session_Title = models.ForeignKey(Sessions,on_delete=models.CASCADE, null=True, default='')
    date = models.DateField()
    session = models.TextField(default='')
    link = models.CharField(max_length=1000, default='')

    def __str__(self):
        k = str(self.Loksabha_MP_Name)+'-'+str(self.Session_Title)+'-'+str(self.date)
        return (k)
    class Meta:
        ordering = ['-date']
# Loksabha Complete Sessions
class Loksabha_Complete_Session1(models.Model):
    Loksabha_Session_Title = models.ForeignKey(Sessions,on_delete=models.CASCADE, null=True, default='')

    Description = models.CharField(max_length=100, default='')
    date = models.DateField()
    session = models.TextField(default='')
    video_link = models.CharField(max_length=1000, default='')

    def __str__(self):
        return str(self.Loksabha_Session_Title)+'-'+str(self.date)
    class Meta:
        ordering = ['-date']'''

