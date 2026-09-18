from django.urls import include, path
from . views import *
urlpatterns = [
path('partydata/', PartyView1.as_view()),
path('stateactivateparty/', stateactivateparty1.as_view()),
path('districtactivateparty/', districtactivateparty1.as_view()),
]
