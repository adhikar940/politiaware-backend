from django.shortcuts import render
from .models import *
from .serializers import *
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.filters import SearchFilter
class RajyaSabhaView(generics.ListAPIView):
    queryset = Rajyasabha1.objects.all()
    serializer_class = RSerializers1
    filter_backends = (DjangoFilterBackend,SearchFilter)
    filter_fields = ('MP_name','state' )
    search_fields = ('MP_name','state' )
class RajyaSabhaView1(generics.ListAPIView):
    queryset = Rajyasabha1.objects.all()
    serializer_class = RajyasabhaSerializers1
    filter_backends = (DjangoFilterBackend,SearchFilter)
    filter_fields = ('id','MP_name','state' )
    search_fields = ('MP_name','state' )
# sessions
class RajyaSabhaSessionView1(generics.ListAPIView):
    queryset = Rajyasabha_Session1.objects.all()
    serializer_class = Rajyasabha_SessionSerializers1
    filter_backends = (DjangoFilterBackend,SearchFilter)
    filter_fields = ('Rajyasabha_MP_Name', 'Session_Title','date', )
    search_fields = ('Rajyasabha_MP_Name','Session_Title','date', )
class RajyaSabhacompleteSessionView1(generics.ListAPIView):
    queryset = Rajyasabha_Complete_Session1.objects.all()
    serializer_class =  Rajyasabha_Complete_SessionSerializers1
    filter_backends = (DjangoFilterBackend,SearchFilter)
    filter_fields = ('Session_Title', 'date', )
    search_fields = ('Session_Title','date', )
