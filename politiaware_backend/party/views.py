from django.shortcuts import render
from . models import *
from . serializers import *
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.filters import SearchFilter
class PartyView1(generics.ListAPIView):
    queryset = Party.objects.all()
    serializer_class = PartySerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_fields = ('partyname', 'abbreviation', 'partystatus')
    search_fields = ('partyname', 'abbreviation', 'partystatus')

class stateactivateparty1(generics.ListAPIView):
    queryset = statepartyactivate1.objects.all()
    serializer_class =statepartyactivateSerializers1
    filter_backends = (DjangoFilterBackend,SearchFilter)
    filter_fields = ('party','state','email')
    search_fields = ('party','state','email')
class districtactivateparty1(generics.ListAPIView):
    queryset = districtpartyactivate1.objects.all()
    serializer_class =districtpartyactivateSerializers1
    filter_backends = (DjangoFilterBackend,SearchFilter)
    filter_fields = ('party','district','email')
    search_fields = ('party','district','email')
