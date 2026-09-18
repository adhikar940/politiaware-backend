from django.db import models
from django.contrib.auth.models import User
from n.models import *
class citizenuserprofile(models.Model):
    Gender = (
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Not Mentioned', 'Not Mentioned')
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    State = models.ForeignKey(State, on_delete=models.SET_NULL, null=True)
    Districts = models.ForeignKey(Districts, on_delete=models.SET_NULL, null=True)
    City = models.ForeignKey(City, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=50)
    DOB = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=15, choices=Gender, default='Not Mentioned')
    fathers_Name = models.CharField(max_length=100, default='')
    Spouse_Name = models.CharField(max_length=100, default='')
    Education = models.CharField(max_length=100, default='')
    Workingat = models.CharField(max_length=100, default='')
    photo = models.ImageField(upload_to='photo/', null=True, blank=True)
    address = models.TextField(max_length=600, default='')
    Mobile = models.CharField(max_length=100, default='')
    def __str__(self):
        return self.name
class msg(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    msg = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
class feeling(models.Model):
    feel = (
        ('happy', 'happy'),
        ('angry', 'angry'),
        ('sad', 'sad'),
        ('scared', 'scared'),
        ('proud', 'proud'),
        ('excited', 'excited'),
        ('disappointed', 'disappointed')
    )
    msg = models.ForeignKey(msg, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    feeling = models.CharField(max_length=20,choices=feel, null=True)
class comments(models.Model):
    msg = models.ForeignKey(msg, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.CharField(max_length=50,blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
class chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    msg = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
