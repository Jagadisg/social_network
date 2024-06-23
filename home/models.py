from django.db import models
from django.utils import timezone
from django.core.validators import MaxValueValidator


class Address(models.Model):
    address_line1 = models.CharField(max_length=120)
    address_line2 = models.CharField(max_length=120)
    city = models.CharField(max_length=50)
    
    def __str__(self) -> str:
        return f'{self.address_line1},{self.city}'

    
class Customer(models.Model):
    username = models.CharField(max_length=120)
    email = models.EmailField(max_length = 254)
    password = models.CharField(max_length=254)
    profile_picture = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    phone = models.IntegerField(validators=[MaxValueValidator(10)])
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, related_name='users') 
    joined_on = models.DateTimeField(default=timezone.now, null=False)
    last_login = models.DateTimeField(null=True)
    
    def __str__(self):
        return self.username    


class FriendRequest(models.Model):
    from_user = models.ForeignKey(Customer, related_name='sent_friend_requests', on_delete=models.CASCADE)
    to_user = models.ForeignKey(Customer, related_name='received_friend_requests', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=(('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')), default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Friend request from {self.from_user} to {self.to_user}"