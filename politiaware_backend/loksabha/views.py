from django.shortcuts import render
from .models import *
from .serializers import *
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.filters import SearchFilter
class LokSabhaView1(generics.ListAPIView):
    queryset = LokSabha.objects.all()
    serializer_class = LSerializers1
    filter_backends = (DjangoFilterBackend,SearchFilter)
    filter_fields = ('MP_name', 'state', )
    search_fields = ('MP_name', 'state','Districts', 'constituency_name','Party')
'''class LokSabhaSessionView1(generics.ListAPIView):
    queryset = Loksabha_Session1.objects.all()
    serializer_class =  Loksabha_SessionSerializers1
    filter_backends = (DjangoFilterBackend,SearchFilter)
    filter_fields = ('Loksabha_MP_Name', 'Session_Title', 'date',)
    search_fields = ('Loksabha_MP_Name','Session_Title','date', )
class LokSabhacompleteSessionView1(generics.ListAPIView):
    queryset = Loksabha_Complete_Session1.objects.all()
    serializer_class =  Loksabha_Complete_SessionSerializers1
    filter_backends = (DjangoFilterBackend,SearchFilter)
    filter_fields = ('Loksabha_Session_Title', 'date', )
    search_fields = ('Loksabha_Session_Title', 'date',)'''
