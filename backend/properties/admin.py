from django.contrib import admin
from .models import Property, PaymentPlan, User, PaymentPlan, Payment


admin.site.register(Property)
admin.site.register(PaymentPlan)
admin.site.register(User)
admin.site.register(Payment)

