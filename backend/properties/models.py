from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.username


class Property(models.Model):
    title = models.CharField(max_length=250)
    description = models.TextField(null=True, blank=True)
    location = models.CharField(max_length=250, blank=True, null=True)
    choices_listing_type = (
      ('House', 'House'),
      ('Apartment', 'Apartment'),
      ('Office', 'Office'),
      ('Land', 'Land'),
    )
    listing_type = models.CharField(max_length=50, blank=True, null=True, choices=choices_listing_type)
    choices_property_status = (
      ('Sale', 'Sale'),
      ('Rent', 'Rent'),
      ('Lease', 'Lease'),
      ('Instalment', 'Instalment'),
      ('RTO', 'RTO'), # Rent To Own
      ('Gone', 'Gone'),
    )
    property_status = models.CharField(max_length=20, blank=True, null=True, choices=choices_property_status)
    price = models.DecimalField(max_digits=50, decimal_places=0, null=True, blank=True)
    choices_rental_frequency = (
      ('Year', 'Year'),
      ('Month', 'Month'),
      ('Week', 'Week'),
      ('Day', 'Day'),
    )
    rental_frequency = models.CharField(max_length=20, blank=True, null=True, choices=choices_rental_frequency)
    rooms = models.IntegerField(blank=True, null=True)
    furnished = models.BooleanField(default=False)
    pool = models.BooleanField(default=False)
    elevator = models.BooleanField(default=False)
    cctv = models.BooleanField(default=False)
    parking = models.BooleanField(default=False)
    date_posted = models.DateTimeField(default=timezone.now)
    picture1 = models.ImageField(null=True, blank=True, upload_to="pictures/%Y/%m/%d/")
    picture2 = models.ImageField(null=True, blank=True, upload_to="pictures/%Y/%m/%d/")
    picture3 = models.ImageField(null=True, blank=True, upload_to="pictures/%Y/%m/%d/")
    picture4 = models.ImageField(null=True, blank=True, upload_to="pictures/%Y/%m/%d/")
    picture5 = models.ImageField(null=True, blank=True, upload_to="pictures/%Y/%m/%d/")


    def __str__(self):
        return self.title


class PaymentPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_plan')
    PLAN_CHOICES = (
        ('Instalment', 'Instalment'),
        ('Sponsorship', 'Sponsorship'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_plans')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='payment_plan')
    plan_type = models.CharField(max_length=50, choices=PLAN_CHOICES)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    installments = models.PositiveIntegerField(help_text="Number of installments")
    next_due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def balance(self):
      return self.total_amount - self.amount_paid

    def __str__(self):
      return f"{self.user.username} - {self.plan_type} - {self.property.title}"


class Payment(models.Model):
    payment_plan = models.ForeignKey('PaymentPlan', on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateTimeField(default=timezone.now)
    method = models.CharField(max_length=50, choices=[
      ('bank_transfer', 'Bank Transfer'),
      ('card', 'Card'),
      ('cash', 'Cash'),
      ('ussd', 'USSD'),
    ])
    reference = models.CharField(max_length=100, blank=True, null=True)  # Transaction ID etc
    status = models.CharField(max_length=50, choices=[
      ('pending', 'Pending'),
      ('successful', 'Successful'),
      ('failed', 'Failed'),
    ], default='successfull')

    def __str__(self):
        return f"{self.payment_plan.user.username} - {self.amount} on {self.payment_date.strftime('%Y-%m%d')}"
   
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        successful_payments = self.payment_plan.payments.filter(status='successful')
        total_paid = sum(p.amount for p in successful_payments)
        self.payment_plan.amount_paid = total_paid
        self.payment_plan.save()