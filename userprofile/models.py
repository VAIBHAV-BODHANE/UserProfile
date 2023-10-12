from django.db import models
from django.contrib.auth.models import AbstractUser

gender_choices = [
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other')
]
desi_choices = [
    ('IT', 'Information Technology'),
    ('S', 'Sales'),
    ('CS', 'Customer service'),        
]

class UserProfile(AbstractUser):
    """Custom users table"""
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    username = None
    first_name = None
    last_name = None
    dob = models.DateField()
    doj = models.DateField()
    gender = models.CharField(max_length=10, choices=gender_choices)
    designation = models.CharField(max_length=50, choices=desi_choices)
    manager = models.CharField(max_length=255, blank=True, null=True)
    pic = models.ImageField(upload_to='userprofile/images', null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
