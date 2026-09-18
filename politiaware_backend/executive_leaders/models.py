from django.db import models
from person.models import *
"""
To store the details of the Prime Minister, president, vicepresident, 
all parliament leaders and speakers of India
"""

house_choice = [
        ('loksabha', 'loksabha'),
        ('rajyasabha', 'rajyasabha')
    ]

leader_choice = [
    ('pm', 'pm'),
    ('president', 'president'),    
    ('vicepresident', 'vicepresident'),
    ('leader', 'leader'),
    ('opp_leader', 'opp_leader'),
    ('speaker', 'speaker'),
    ('dep_speaker', 'dep_speaker')
]


class ExecutiveLeader(person):
    """ To store the details of the Prime Minister, president, vicepresident """
    leader_type = models.CharField(max_length=20, choices=leader_choice, null=True, blank=True)    
    is_present = models.BooleanField(default=False,null=True, blank=True)
    # Many-to-many relationship with RulingPeriod
    ruling_periods = models.ManyToManyField(ruling_period, related_name='par_exc_leaders_period', null=True, blank=True)


class ParliamentLeader(ExecutiveLeader):   
    """ To store all parliament leaders and speakers of India""" 
    house = models.CharField(max_length=20, choices=house_choice, default='loksabha', null=True, blank=True)   

   
