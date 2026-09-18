from django.shortcuts import render
from .models import *
from .serializers import *
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.filters import SearchFilter
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import base64
def present_pm(request):
    if request.method == 'GET':
        present_pm_details = pm.objects.filter(is_present=True).first()
        if present_pm_details:
            serializer = pmSerializer(present_pm_details)
            return JsonResponse(serializer.data, safe=False)
        else:
            return JsonResponse({'error': 'No present pm found.'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=405)
@csrf_exempt
def upload_image(request):
    if request.method == 'POST':
        try:
            id = request.POST.get('id')
            photo = request.FILES.get('photo')

            # Convert the image to Base64
            base64_image = base64.b64encode(photo.read()).decode('utf-8')
            pm_ins = pm.objects.get(id=int(id))        
            pm_ins.photo = base64_image
            pm_ins.save()
            # Confirm save
            if pm_ins.pk:  # Check if the primary key is set
                return JsonResponse({'message': 'Image uploaded successfully', 'id': pm_ins.pk}, status=201)
            else:
                return JsonResponse({'error': 'Failed to save image'}, status=500)
        except Exception as e:
            print(f"Exception occurred: {e}")
            return JsonResponse({'error': 'An error occurred during the upload process'}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

'''
class LokSabhaView1(generics.ListAPIView):
    queryset = pm.objects.all()
    serializer_class = LSerializers1
    filter_backends = (DjangoFilterBackend,SearchFilter)
    filter_fields = ('MP_name', 'state', )
    search_fields = ('MP_name', 'state','Districts', 'constituency_name','Party')
'''
