from django.db import models
from django.contrib.auth.models import User

class Movie(models.Model):
    name = models.CharField(max_length=200)
    time =models.TimeField(max_length=200)
    ticket_amount =models.DecimalField(max_digits=6,decimal_places=2)
    poster =models.ImageField(upload_to='posters/')
    description =models.TextField(blank=True,null=True)
    is_active =models.BooleanField(default=True)

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    booking_date = models.DateTimeField(auto_now_add=True)
    tickets = models.PositiveBigIntegerField(default=1)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    qr_image = models.ImageField(blank=True, null=True, upload_to='QRCode')
    date = models.DateField(default='2024-01-01')


def __str__(self):
        return f"Booking {self.id} for {self.event_name}"