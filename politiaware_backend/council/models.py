from django.db import models
from state.models import StateForeign
from party.models import Party
from person.models import person

# ==============================================================================
# State Legislative Councils in India (Vidhan Parishad):
# Under Articles 168, 169, and 171 of the Constitution of India, currently only 
# 6 out of 28 Indian states have a bicameral legislature with an active 
# Legislative Council (Vidhan Parishad):
#
# 1. Andhra Pradesh    - 58 seats (revived in 2007; originally 1958-1985)
# 2. Bihar             - 75 seats (established in 1912)
# 3. Karnataka         - 75 seats (established in 1956 as Mysore LC)
# 4. Maharashtra       - 78 seats (established in 1960)
# 5. Telangana         - 40 seats (constituted in 2014)
# 6. Uttar Pradesh     - 100 seats (established in 1935)
#
# Historical Note / Abolished Councils:
# - Jammu & Kashmir had a 36-seat Legislative Council until 2019 (abolished under J&K Reorganisation Act, 2019).
# - Tamil Nadu abolished its Legislative Council in 1986.
# - West Bengal abolished its Legislative Council in 1969.
# - Punjab abolished its Legislative Council in 1970.
# - Assam abolished its Legislative Council in 1969.
# ==============================================================================
class MLC(person, StateForeign):
    choice = (
        ('Members of Local Body', 'Members of Local Body'),
        ('Members of legislative body', 'Members of Legislative Body'),
        ('Governor', 'Governor'),
        ('Graduates of three years', 'Graduates of three years'),
        ('University teacher of three years', 'University teacher of three years')
    )
    nomination_choices = (
        ('Literature', 'Literature'),
        ('Science', 'Science'),
        ('Art', 'Art'),
        ('Social Service', 'Social Service'),
        ('Co-operative Movement', 'Co-operative Movement'),
    )
    # state is inherited from StateForeign
    party = models.ForeignKey(Party, on_delete=models.CASCADE, null=True, blank=True, default=None)
    elected = models.CharField(max_length=500, choices=choice, default='Governor')
    nominationCategory = models.CharField(max_length=100, choices=nomination_choices, null=True, blank=True)
    constituency_name = models.CharField(max_length=200, null=True, blank=True)
    isPresent = models.BooleanField(default=True, null=True, blank=True)

    class Meta:
        unique_together = ['name']
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.state}" if self.state else self.name



