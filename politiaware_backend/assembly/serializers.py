from rest_framework import serializers
from . models import *
from n.models import *
class Legislative_AssemblySerializer(serializers.ModelSerializer):
    class Meta:
        model = Legislative_Assembly1
        fields = '__all__'
class Assembly_ConstituencySerializers1(serializers.ModelSerializer):
    class Meta:
        model = Assembly_Constituency1
        fields = ['id','State', 'Districts', 'Assembly_Constituency_Name']

class Legislative_AssemblySerializers1(serializers.ModelSerializer):
    state = serializers.StringRelatedField()
    District = serializers.StringRelatedField()
    Party = serializers.StringRelatedField()
    constituency_name =  serializers.StringRelatedField()
    class Meta:
        model = Legislative_Assembly1
        fields = ['id','state','District', 'constituency_name', 'MLA_name', 'party_name', 'Party', 'gender',
                  'fathers_Name', 'Spouse_Name', 'Highest_Education', 'University', 'photo', 'address',
                  'Email_address', 'Mobile', 'chldid']
class assemblypersonalSerializer1(serializers.ModelSerializer):
    mla = serializers.StringRelatedField()
    class Meta:
        model = assemblypersonal
        fields = ['parentid','id', 'profilename','mla', 'presentparty','About_Me','childhood_and_Education','Political_Career','Personal_Life','aims_Goal_and_Dream','Message_For_Followers','About_Mephoto','childhood_and_Educationphoto','Profilephoto','Political_Careerphoto','Personal_Lifephoto','aims_Goal_and_Dreamphoto','Message_For_Followersphoto']
        #extra_kwargs = {'mp': {'read_only': True}}
class assemblytermSerializers(serializers.ModelSerializer):
    class Meta:
        model = assemblyterm
        fields = ['mla','year', 'month', 'date']
