from django.db import models
from person.models import person
from state.models import State
from party.models import Party

class cm_ruling_period(models.Model):
    startdate = models.DateField(null=True, blank=True)
    enddate = models.DateField(null=True, blank=True)

class cm(person):
    """ To store the details of chief ministers """
    ispresent = models.BooleanField(default=False,null=True, blank=True)
    rulingperiods = models.ForeignKey(cm_ruling_period, on_delete=models.SET_NULL,null=True, blank=True)
    party = models.ForeignKey(Party,on_delete=models.SET_NULL,related_name='cm_party', null=True, blank=True)
    rulingstate = models.ForeignKey(State,related_name='cm_ruling_state', on_delete=models.SET_NULL,null=True, blank=True)

