from django.urls import include, path
from . views import *
urlpatterns = [
path('Rajyasabha_Candidates_api/', RajyaSabhaView.as_view()),
path('Rajyasabhaindividualcandidates/', RajyaSabhaView1.as_view()),
path('RajyasabhaindividualSessionapi/', RajyaSabhaSessionView1.as_view()),
path('RajyasabhacompleteSessionapi/', RajyaSabhacompleteSessionView1.as_view()),
]
