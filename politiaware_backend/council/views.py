from django.shortcuts import render
from .models import *
from .serializers import *
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.filters import SearchFilter
class Legislative_councils(generics.ListAPIView):
    queryset = Legislative_councils1.objects.all()
    serializer_class = Legislative_councilsSerializer1
    filter_backends = (DjangoFilterBackend,SearchFilter)
    filter_fields = ('id','state', 'Districts', 'constituency_name', 'MLC_name',)
    search_fields = ('id','state', 'Districts', 'constituency_name', 'MLC_name', )
class councilpersonal(generics.ListAPIView):
    queryset = councilpersonal1.objects.all()
    serializer_class =  councilpersonalSerializer1
    filter_backends = (DjangoFilterBackend,SearchFilter)
    filter_fields = ('mlc',)
    search_fields = ('mlc')
class councilterm(generics.ListAPIView):
    queryset = councilterm.objects.all()
    serializer_class =  counciltermSerializers
    filter_backends = (DjangoFilterBackend,SearchFilter)
    filter_fields = ('mlc',)
    search_fields = ('mlc',)
