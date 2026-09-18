from . models import *
from rest_framework import serializers
class PSerializers1(serializers.ModelSerializer):
    class Meta:
        model = Party1
        fields = ['id','partyname', 'abbreviation','actvated']
class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = [
            'id',
            'partyname',
            'abbreviation',
            'partystatus',
            'party_color',
            'President',
            'founder',
            'chairperson',
            'foundeddate',
            'headquarters',
            'partyflag',
            'electionsymbol',
            'founderPhoto',
            'chairpersonPhoto',
            'PresidentPhoto',
        ]

class statepartyactivateSerializers1(serializers.ModelSerializer):
    state = serializers.StringRelatedField()
    party = serializers.StringRelatedField()
    class Meta:
        model = districtpartyactivate
        fields = ['party','state','email']
class districtpartyactivateSerializers1(serializers.ModelSerializer):
    state = serializers.StringRelatedField()
    district = serializers.StringRelatedField()
    class Meta:
        model = statepartyactivate1
        fields = ['state','party','district','email']
