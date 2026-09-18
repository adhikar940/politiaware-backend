from rest_framework import serializers
from . models import *
from n.models import *
class Legislative_councilsSerializer1(serializers.ModelSerializer):
    state = serializers.StringRelatedField()
    Districts = serializers.StringRelatedField()
    party = serializers.StringRelatedField()
    class Meta:
        model = Legislative_councils1
        fields = ['id','state', 'Districts', 'constituency_name', 'MLC_name', 'elected', 'presentorx',
                  'actvated','party','party_name','gender', 'fathers_Name', 'Spouse_Name', 'Highest_Education', 'University', 'photo', 'address',
                   'Email_address', 'Mobile','chldid']
class LCSerializers1(serializers.ModelSerializer):
    state = serializers.StringRelatedField()
    Districts = serializers.StringRelatedField()
    party = serializers.StringRelatedField()
    class Meta:
        model = Legislative_councils1
        fields = ['id','state','Districts', 'constituency_name', 'MLC_name', 'party',
                   'photo','presentorx','actvated','elected']

class councilpersonalSerializer1(serializers.ModelSerializer):
    mlc = serializers.StringRelatedField()
    class Meta:
        model = councilpersonal1
        fields = ['id', 'profilename','mlc', 'presentparty','About_Me','childhood_and_Education','Political_Career','Personal_Life','aims_Goal_and_Dream','Message_For_Followers','About_Mephoto','childhood_and_Educationphoto','Profilephoto','Political_Careerphoto','Personal_Lifephoto','aims_Goal_and_Dreamphoto','Message_For_Followersphoto']
        #extra_kwargs = {'mp': {'read_only': True}}
class counciltermSerializers(serializers.ModelSerializer):
    class Meta:
        model = councilterm
        fields = ['mlc','year', 'month', 'date']
