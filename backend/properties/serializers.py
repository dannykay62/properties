from rest_framework import serializers
from .models import Property, User, PaymentPlan, Payment

class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class PropertySummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ['id', 'title']


class PaymentPlanSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    property_title = serializers.CharField(source='property.title', read_only=True)
    property_id = serializers.CharField(source='property.id', read_only=True)

    class Meta:
        model = PaymentPlan
        fields = '__all__'


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta: 
        model = User
        fields = ['username', 'email', 'phone_number', 'password']

    def create(self, validate_data):
        user = User.objects.create_user(
            username=validate_data['username'],
            email=validate_data['email'],
            phone_number=validate_data['phone_number'],
            password=validate_data['password']
        )

        return user
    

# Login Serializer
class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

