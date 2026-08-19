from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    profile_image = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True
    )

    country = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    address = models.TextField(
        blank=True,
        null=True
    )
    
    birth_date = models.DateField(
        blank=True,
        null=True
    )

    account_activation = models.BooleanField(default=False)

    facebook_link = models.URLField(
        blank=True,
        null=True
    )
    
    # حقل المحفظة لتخزين الأموال الزائدة بأمان تام
    wallet = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00
    )

    def __str__(self):
        return self.user.username