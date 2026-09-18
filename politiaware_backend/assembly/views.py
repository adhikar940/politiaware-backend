from django.shortcuts import render
from django.http import HttpResponse
from .models import *
from .models import Legislative_Assembly1 as la
from .serializers import *
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.filters import SearchFilter
import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
import uuid
from datetime import datetime
from django.http import JsonResponse
from n.models import *
from io import BytesIO
from django_pandas.io import read_frame
import time
from datetime import datetime
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
class Assembly_Constituency(generics.ListAPIView):
    queryset = Assembly_Constituency1.objects.all()
    serializer_class = Assembly_ConstituencySerializers1
    filter_backends = (DjangoFilterBackend,SearchFilter)
    filter_fields = ('State', 'Districts', 'Assembly_Constituency_Name' )
    search_fields = ('State', 'Districts', 'Assembly_Constituency_Name' )
class Legislative_Assembly1(generics.ListAPIView):
    queryset = Legislative_Assembly1.objects.all()
    serializer_class =  Legislative_AssemblySerializers1
    filter_backends = (DjangoFilterBackend,SearchFilter)
    filter_fields = ('state','District', 'constituency_name', 'MLA_name',)
    search_fields = ('state','District', 'constituency_name', 'MLA_name', )
class assemblypersonal1(generics.ListAPIView):
    queryset = assemblypersonal1.objects.all()
    serializer_class =  assemblypersonalSerializer1
    filter_backends = (DjangoFilterBackend,SearchFilter)
    filter_fields = ('mla' )
    search_fields = ('mla')
class assemblyterm(generics.ListAPIView):
    queryset = assemblyterm.objects.all()
    serializer_class =  assemblytermSerializers
    filter_backends = (DjangoFilterBackend,SearchFilter)
    filter_fields = ('mla' )
    search_fields = ('mla')
########### MLA EMAIL Sendiing ###################
class mlaemailsent(APIView):
    def get(self, request):
        output = BytesIO()
        state = request.query_params.get('state')
        party = request.query_params.get('state')
        district = request.query_params.get('district')
        if(district and party):
            qs = la.objects.all().filter(Party = party,District = district)
        elif(state and party):
            qs = la.objects.all().filter(state = state,Party = party)
        elif(district):
            qs = la.objects.all().filter(District = district)
        elif(state):
            qs = la.objects.all().filter(state = state)
        elif(party):
            qs = la.objects.all().filter(Party = party)
        else:
            return Response({'msg':"Provide state or district or party"})
        sendstatus = []
        j=[]
        # alert mail for whom the mail is sending
        t = 60*10
        send_mail(
            # title:
            "Sending email for assembly-state"+state+"party-"+party+"District-"+district,
            # message:
            "Email will send after"+t+"min.",
            # from:
            'adhikar869@gmail.com',
            # to:
            ['kathi.mohangoud@gmail.com',]
        )
        sub = "Sending email for assembly-state"+state+"party-"+party+"District-"+district
        msg = "the email that is going to send"
        # the content of the mail that is going to send
        send_mail(
            # title:
            sub,
            # message:
            msg,
            # from:
            'adhikar869@gmail.com',
            # to:
            ['kathi.mohangoud@gmail.com',]
        )
        time.sleep(t)
        e = emailsend.objects.all()
        if en in e :
            if(e.confirmsend == 'no'):
                return Response({'msg':"Email sending permission is not activated"})
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        print("date and time =", dt_string)
        s = "Sending email for assembly-state"+state+"party-"+party+"District-"+district
        for i in qs :
            print(i.Email_address)
            try :
                send_mail(
                    # title:
                    sub,
                    # message:
                    msg,
                    # from:
                    'adhikar869@gmail.com',
                    # to:
                    [i.Email_address,]
                )
                sendstatus.append('sent')
            except :
                sendstatus.append('Not sent')
        df = read_frame(qs)
        df['sendstatus'] = sendstatus
        del df["id"]
        z=df.to_excel(output)
        #path = default_storage.save('z',ContentFile(b'mn'))
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="output.xlsx"'
        response.write(output.getvalue())
        '''for i in data :
            print(i.MLA_name)
            print(i.Email_address)
        return Response({'msg':'ok'})'''
        return response
'''class mlaemailsent(generics.ListAPIView):
    serializer_class =  Legislative_AssemblySerializers1
    def get_queryset(self,request):
        s = request.data['state']
        print(s)
        return Legislative_Assembly1.objects.filter(state=s)'''
def export11(request):
    la = Legislative_Assembly1.objects.filter(state=39)
    return JsonResponse({'status':200})
class ExportImportExcelView(APIView):
    def get(self,request):
        #m = request.GET.get('k')
        Legislative_Assembly1_objs =Legislative_Assembly1.objects.filter(state=10)
        serializer = Legislative_AssemblySerializer(Legislative_Assembly1_objs,many=True)
        df = pd.DataFrame(serializer.data)
        z = df.to_dict()
        print(z)
        #excelupload.objects.create(excelfileupload = "/media/mohan/mn/mnew/m/123.xlsx")
        return Response({'k':z})
