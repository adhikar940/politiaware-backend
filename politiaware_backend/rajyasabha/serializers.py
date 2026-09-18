from rest_framework import serializers
from . models import *
from n.models import *
class RajyasabhaSerializers1(serializers.ModelSerializer):
    state = serializers.StringRelatedField()
    Districts = serializers.StringRelatedField()
    Party = serializers.StringRelatedField()
    class Meta:
        model = Rajyasabha1
        fields = ['MP_name','state','Districts', 'party_name', 'Party', 'gender', 'fathers_Name', 'Spouse_Name', 'Highest_Education',
                  'University', 'photo', 'address', 'elected', 'Email_address', 'Mobile', 'chldid']
class RSerializers1(serializers.ModelSerializer):
    state = serializers.StringRelatedField()
    Districts = serializers.StringRelatedField()
    Party = serializers.StringRelatedField()
    class Meta:
        model = Rajyasabha1
        fields = ['id','state','Districts', 'MP_name', 'Party',
                   'photo','presentorx','actvated','elected']
class rajyasabhapersonalSerializer1(serializers.ModelSerializer):
    mp = serializers.StringRelatedField()
    class Meta:
        model = rajyasabhapersonal1
        fields = ['id','profilename','mp', 'presentparty','About_Me','childhood_and_Education','Political_Career','Personal_Life','aims_Goal_and_Dream','Message_For_Followers','About_Mephoto','childhood_and_Educationphoto','Profilephoto','Political_Careerphoto','Personal_Lifephoto','aims_Goal_and_Dreamphoto','Message_For_Followersphoto']
class rajyasabhapersonal1Serializer1(serializers.ModelSerializer):
    #mp = serializers.StringRelatedField()
    class Meta:
        model = rajyasabhapersonal1
        fields = ['id', ]
class Rajyasabha_SessionSerializers1(serializers.ModelSerializer):
    Rajyasabha_MP_Name = serializers.StringRelatedField()
    Session_Title  = serializers.StringRelatedField()
    class Meta:
        model = Rajyasabha_Session1
        fields = ['Rajyasabha_MP_Name', 'date', 'session', 'link','Session_Title' ]

class Rajyasabha_Complete_SessionSerializers1(serializers.ModelSerializer):
    Session_Title  = serializers.StringRelatedField()
    class Meta:
        model = Rajyasabha_Complete_Session1
        fields = ['Description', 'date', 'session', 'video_link','Session_Title']
