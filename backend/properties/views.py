from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import PasswordResetForm
from decimal import Decimal, InvalidOperation
from django.db.models import Sum, Count

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


class PaymentPlanView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        payment_plans = PaymentPlan.objects.all().order_by('-created_at')
        serializer = PaymentPlanSerializer(payment_plans, many=True, context={'request' : request})
        return Response(serializer.data)
    
    def delete(self, request, plan_id=None, *args, **kwargs):
        try:
            plan = PaymentPlan.objects.get(pk=plan_id)
            plan.delete()
            return Response({'detail': 'Payment plan deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)
        except PaymentPlan.DoesNotExist:
            return Response({'error': 'Payment plan not found.'}, status=status.HTTP_404_NOT_FOUND)


class UserPaymentPlansView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        # Allow registered user to see user's payment plan unless staff
        if request.user.id != pk and not request.user.is_staff:
            return Response({'error': 'Unauthorized access.'}, status=403)
        
        payment_plans = PaymentPlan.objects.filter(user__id=pk).order_by('-created_at')
        serializer = PaymentPlanSerializer(payment_plans, many=True, context={'request': request})
        return Response(serializer.data)


class PaymentByProperties(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, property_id):
        payments = Payment.objects.filter(payment_plan__property__id=property_id, status='successful')
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)


class PaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        payments = Payment.objects.all().order_by('-payment_date')
        serializer = PaymentSerializer(payments, many=True, context={'request': request})
        return Response(serializer.data)


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all().order_by('-payment_date')
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def make_payment(request, plan_id):
    payment_plan = get_object_or_404(PaymentPlan, pk=plan_id)
    amount = request.data.get('amount')
    try:
        amount = Decimal(str(amount))
    except (TypeError, ValueError):
        return Response({"error": "Invalid amount."}, status=status.HTTP_400_BAD_REQUEST)
    
    if amount <= 0:
        return Response({"error": "Amount must be greater than 0."}, status=status.HTTP_400_BAD_REQUEST)
    
    if payment_plan.amount_paid + amount > payment_plan.total_amount:
        return Response({"error": "Payment exceeds total amount."}, status=status.HTTP_400_BAD_REQUEST)
    
    payment = Payment.objects.create(
        payment_plan=payment_plan,
        amount=amount,
        method=request.data.get('method', 'bank_transfer'),
        reference=request.data.get('reference', ''),
        status='successful'
    )

    payment_plan.amount_paid += amount
    payment_plan.save()

    return Response({
        "message": "Payment successful.",
        "new_balance": payment_plan.total_amount - payment_plan.amount_paid
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def report_summary(request):
    total_properties = Property.objects.count()
    total_plans = PaymentPlan.objects.count()
    total_users = User.objects.count()
    total_amount_paid = Payment.objects.filter(status='successful').aggregate(total=Sum('amount'))['total'] or 0

    successful_count = Payment.objects.filter(status='successful').count()
    pending_count = Payment.objects.filter(status='pending').count()
    failed_count = Payment.objects.filter(status='failed').count()

    recent_payments = Payment.objects.select_related('payment_plan').order_by('-payment_date')[:10]
    recent_data = [
        {
            "user": payment.payment_plan.user.username if hasattr(payment.payment_plan, 'user') else 'N/A',
            "amount": float(payment.amount),
            "method": payment.method,
            "status": payment.status,
            "date": payment.payment_date.strftime('%Y-%m-%d'),
        }
        for payment in recent_payments
    ]

    return Response({
        "total_properties": total_properties,
        "total_payment_plans": total_plans,
        "total_users": total_users,
        "total_amount_paid": float(total_amount_paid),
        "failed_payments": failed_count,
        "recent_payments": recent_data
    })

