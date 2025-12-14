from django.utils import timezone
import random
from django.db import models
from django.contrib.auth.models import User
# Create your models here.
# creating a model for the superadmin
from django.contrib.auth.hashers import make_password,check_password


#Brand model
class Brand(models.Model):
    Tyre_brand_name=models.CharField(max_length=10, unique=True)
    name=models.CharField(max_length=50)    
    class meta:
        ordering=['name']
        
    def __str__(self):
        return self.name
    




class SubUserLogin(models.Model):
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=20)

    def __str__(self):
        return self.username

# ===============================
# OTP model linked to Django User
# ===============================
class UserOTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='otp_data')
    otp = models.CharField(max_length=6, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_otp(self):
        otp = str(random.randint(1000, 9999))
        self.otp = otp
        self.created_at = timezone.now()
        self.save()
        return otp

    def verify_otp(self, otp):
        # check if OTP matches and not expired (5 min)
        if self.otp != otp:
            return False
        if timezone.now() - self.created_at > timezone.timedelta(minutes=5):
            return False
        # delete OTP after successful verification
        self.delete()
        return True

    def __str__(self):
        return f"OTP for {self.user.username}"
# ===============================

class DistributorLogin(models.Model):
    shop_name=models.CharField(max_length=50, unique=True)
    mobile_no = models.CharField(max_length=10, unique=True),
    UserOTP=models.CharField(max_length=4, null=True, blank=True)
# creating a model for the distributor

## distributor model made by superadmin
class CreateDistributor(models.Model):
    id = models.AutoField(primary_key=True)
    Shop_name = models.CharField(max_length=50)
    Address = models.CharField(max_length=100)
    email = models.EmailField(unique=True, null=True, blank=True)
    mobileNo = models.CharField(max_length=10, unique=True)
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at = models.DateTimeField(default=timezone.now, null=True, blank=True)
    added_date = models.DateTimeField(auto_now=True)
    end_date = models.DateField()
    brands=models.ManyToManyField('Brand',related_name='distributors', blank=True)
    def __str__(self):
        return self.Shop_name

# sub user model
class CreateSubUser(models.Model):
    id = models.AutoField(primary_key=True)    
    Shop_Name = models.CharField(max_length=50, unique=True, null=True, blank=True)
    Email = models.EmailField(max_length=50, unique=True, null=True, blank=True)
    password = models.CharField(max_length=128)
    mobileNo = models.CharField(max_length=10)
    discount_percantage = models.FloatField(max_length=5)
    added_date = models.DateTimeField(auto_now=True)
    City = models.CharField(max_length=50, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    distributor = models.ForeignKey(
        CreateDistributor, on_delete=models.CASCADE,
        related_name="subusers", null=True, blank=True
    )
    
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.Shop_Name

class TyreModel(models.Model):
    id = models.AutoField(primary_key=True)
    width = models.CharField(max_length=10,default='0')
    ratio = models.CharField(max_length=10,default='0')
    rim = models.CharField(max_length=10,default='0')
    Tyre_type_Choices = [
    ('radial', 'Radial'),
    ('nylon', 'Nylon'),
    ('notSelected', 'Not Selected'),
]
    tyreType = models.CharField(max_length=50, choices=Tyre_type_Choices, default='notSelected')

    added_date=models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.tyreType == 'redial':
            return f"{self.width}/{self.ratio}R{self.rim}"
        else:
            return f"{self.width}/{self.ratio}/{self.rim}"
class TyrePattern(models.Model):
    tyre = models.ForeignKey(TyreModel, related_name='patterns', on_delete=models.CASCADE)
    brand=models.ForeignKey(Brand,related_name='patterns', on_delete=models.PROTECT, null=True, blank=True)
    name = models.CharField(max_length=50,)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    image = models.ImageField(upload_to='apiapp/images/', blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.tyre}"






    

