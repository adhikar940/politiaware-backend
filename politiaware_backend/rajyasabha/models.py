from django.db import models
from state.models import StateForeign
from party.models import Party
from person.models import person

class RajyasabhaMP(person, StateForeign):
    choice = (
        ('Legislature', 'Legislature'),
        ('President', 'President')
    )
    nomination_choices = (
        ('Literature', 'Literature'),
        ('Science', 'Science'),
        ('Art', 'Art'),
        ('Social Service', 'Social Service'),
    )
    # state is inherited from StateForeign
    party = models.ForeignKey(Party, on_delete=models.CASCADE, null=True, blank=True, default=None)
    elected = models.CharField(max_length=500, choices=choice, default='Legislature')
    nominationCategory = models.CharField(max_length=100, choices=nomination_choices, null=True, blank=True)
    isPresent = models.BooleanField(default=True, null=True, blank=True)

    class Meta:
        unique_together = ['name']
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.state}" if self.state else self.name

'''class rajyasabhapersonal1(personal):
    mp = models.ForeignKey(Rajyasabha1, on_delete=models.SET_NULL, null=True,)
    class Meta:
        unique_together = ['mp']

    def __str__(self):
        return '%s' % (self.mp)'''



#$#### SESSIONS
# Rajyasabha Individual Sessions
'''class Rajyasabha_Session1(models.Model):
    Rajyasabha_MP_Name = models.ForeignKey(Rajyasabha1, on_delete=models.SET_NULL, null=True, default='')
    Session_Title = models.ForeignKey(Sessions, on_delete=models.CASCADE, null=True, default='')
    date = models.DateField()
    session = models.TextField(default='')
    link =  models.CharField(max_length=1000, default='')

    def __str__(self):
        return str(self.Session_Title)
    class Meta:
        ordering = ['-date']
# Rajyasabha Complete Sessions
class Rajyasabha_Complete_Session1(models.Model):
    Session_Title = models.ForeignKey(Sessions,on_delete=models.CASCADE, null=True, default='')
    Description = models.CharField(max_length=100, default='')
    date = models.DateField()
    session = models.TextField(default='')
    video_link = models.CharField(max_length=1000, default='')

    def __str__(self):
        return str(self.Session_Title)+'-'+str(self.date)
    class Meta:
        ordering = ['-date']'''
