from django.urls import include, path
from . views import *
urlpatterns = [
path('loksbhadata/', LokSabhaView1.as_view()),
path('LoksabhaindividualSessionapi/', LokSabhaSessionView1.as_view()),
path('LoksabhaCompleteSessionapi/', LokSabhacompleteSessionView1.as_view()),
]
