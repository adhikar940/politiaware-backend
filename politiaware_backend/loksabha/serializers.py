from rest_framework import serializers
from . models import *
from n.models import *
# LOKSABHA
class LokSabhaSerializers1(serializers.ModelSerializer):
    state = serializers.StringRelatedField()
    Districts = serializers.StringRelatedField()
    Party = serializers.StringRelatedField()
    class Meta:
        model = LokSabha1
        fields = ['state','Districts', 'constituency_name', 'MP_name', 'party_name', 'Party', 'gender', 'fathers_Name',
                  'Spouse_Name', 'Highest_Education', 'University', 'photo', 'address', 'Email_address', 'Mobile','chldid']

class LSerializers1(serializers.ModelSerializer):
    state = serializers.StringRelatedField()
    Districts = serializers.StringRelatedField()
    Party = serializers.StringRelatedField()
    class Meta:
        model = LokSabha
        fields = ['id','state','Districts', 'constituency_name', 'MP_name', 'Party',
                   'photo','presentorx','actvated','chldid']

class loksabhapersonalSerializer1(serializers.ModelSerializer):
    mp = serializers.StringRelatedField()
    class Meta:
        model = loksabhapersonal1
        fields = ['id', 'profilename','mp', 'presentparty','About_Me','childhood_and_Education','Political_Career','Personal_Life','aims_Goal_and_Dream','Message_For_Followers','About_Mephoto','childhood_and_Educationphoto','Profilephoto','Political_Careerphoto','Personal_Lifephoto','aims_Goal_and_Dreamphoto','Message_For_Followersphoto']
        #extra_kwargs = {'mp': {'read_only': True}}
############################    Loksabha Sessions   #####################################################
class Loksabha_SessionSerializers1(serializers.ModelSerializer):
    Loksabha_MP_Name = serializers.StringRelatedField()
    Session_Title = serializers.StringRelatedField()
    class Meta:
        model = Loksabha_Session1
        fields = ['Loksabha_MP_Name', 'date', 'session', 'link','Session_Title' ]

class Loksabha_Complete_SessionSerializers1(serializers.ModelSerializer):
    Loksabha_Session_Title = serializers.StringRelatedField()
    class Meta:
        model = Loksabha_Complete_Session1
        fields = ['Loksabha_Session_Title','Description', 'date', 'session', 'video_link']
