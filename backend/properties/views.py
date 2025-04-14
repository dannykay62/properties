from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import PasswordResetForm

from .models import Property, User, PaymentPlan, Payment
from .serializers import PropertySerializer, UserRegisterSerializer, UserLoginSerializer, PaymentPlanSerializer, UserSerializer, PaymentSerializer


# USER REGISTRATION VIEW
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    if request.method == 'POST':
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"message": "User created successfully!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

# USER LOGIN VIEW
@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    if request.method == 'POST':
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(username=username, password=password)
            if user:
                token, created = Token.objects.get_or_create(user=user)
                return Response({"token": token.key}, status=status.HTTP_200_OK)
            return Response({"message": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# PUBLIC FUNCTION BASED VIEW
@api_view(['GET'])
@permission_classes([AllowAny])
def property_list(request):
    properties = Property.objects.all()
    serializer = PropertySerializer(properties, many=True)
    return Response(serializer.data)


# USER LOGOUT VIEW
@api_view(['POST'])
def logout_user(request):
    if request.method == 'POST':
        request.user.auth_token.delete() # Delete the auth token for logout
        return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
    

# PASSWORD RESET VIEW
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    if request.method == 'POST':
        email = request.data.get('email')
        form = PasswordResetForm(data={'email': email})
        if form.is_valid():
            form.save()
            return Response({"message": "Password reset email sent."}, status=status.HTTP_200_OK)
        return Response({"message": "Invalid email address."}, status=status.HTTP_400_BAD_REQUEST)


class PaymentPlanViewSet(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        payment_plans = PaymentPlan.objects.all().order_by('-created_at')
        serializer = PaymentPlanSerializer(payment_plans, many=True, context={'request' : request})
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, method=['post'], url_path='make-payment')  # Frontend can call: POST /api/payment-plans/{id}/make-payment/
    def make_payment(self, request, pk=None):
        payment_plan = self.get_object()
        amount = request.data.get('amount')

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return Response({"error": "Invalid amount."}, status=status.HTTP_400_BAD_REQUEST)
        
        if amount <= 0:
            return Response({"error": "Amount must be greater than 0."}, status=status.HTTP_400_BAD_REQUEST)
        
        if payment_plan.amount + amount > payment_plan.total_amount:
            return Response({"error": "Payment exceeds total amount."}, status=status.HTTP_400_BAD_REQUEST)
        
        payment_plan.amount_paid += amount
        payment_plan.save()

        return Response({
            "message": "Payment successful.",
            "new_balance": payment_plan.balance()
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def property_detail(request, pk):
    property = get_object_or_404(Property, pk=pk)
    serializer = PropertySerializer(property)
    return Response(serializer.data)


# CLASS-BASED VIEW: PUBLIC LIST
class PropertyListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        properties = Property.objects.all().order_by('-date_posted')
        serializer = PropertySerializer(properties, many=True, context={'request' : request})
        return Response(serializer.data)

    


class MakePayment(viewsets.ModelViewSet):
    @action(detail=True, method=['post'], url_path='make-payment')  # Frontend can call: POST /api/payment-plans/{id}/make-payment/
    def make_payment(self, request, pk=None):
        payment_plan = self.get_object()
        amount = request.data.get('amount')

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return Response({"error": "Invalid amount."}, status=status.HTTP_400_BAD_REQUEST)
        
        if amount <= 0:
            return Response({"error": "Amount must be greater than 0."}, status=status.HTTP_400_BAD_REQUEST)
        
        if payment_plan.amount + amount > payment_plan.total_amount:
            return Response({"error": "Payment exceeds total amount."}, status=status.HTTP_400_BAD_REQUEST)
        
        payment_plan.amount_paid += amount
        payment_plan.save()

        return Response({
            "message": "Payment successful.",
            "new_balance": payment_plan.balance()
        }, status=status.HTTP_200_OK)


class UsersList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = User.objects.all().order_by('-date_joined')
        serializer = UserSerializer(users, many=True, context={'request': request})
        return Response(serializer.data)


# CLASS-BASED VIEW: PROTECTED UPLOAD
class PropertyUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        serializer = PropertySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors) # To debug
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
