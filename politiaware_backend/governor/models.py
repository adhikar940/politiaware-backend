from django.db import models
from person.models import person
from state.models import State

class governor_ruling_period(models.Model):
    startdate = models.DateField(null=True, blank=True)
    enddate = models.DateField(null=True, blank=True)

class governor(person):
    """ To store the details of Governor """
    ispresent = models.BooleanField(default=False,null=True, blank=True)
    rulingperiods = models.ForeignKey(governor_ruling_period, on_delete=models.PROTECT, null=True, blank=True)# raises error when referenced object is deleted
    rulingstate = models.ForeignKey(State, related_name='governor_ruling_state',  on_delete=models.PROTECT, null=True, blank=True)# raises error when referenced object is deleted
