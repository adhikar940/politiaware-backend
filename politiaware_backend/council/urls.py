from django.urls import include, path
from . views import *
urlpatterns = [
path('Legislative_councils/', Legislative_councils.as_view()),
path('councilpersonal/', councilpersonal.as_view()),
path('councilterm/', councilterm.as_view()),
]
