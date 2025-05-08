from django.urls import path, include
from . import views
from .views import PropertyUploadView, edit_property, PaymentPlanView, PaymentViewSet, UserPaymentPlansView, PaymentByProperties
from djoser.views import UserViewSet
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'users', UserViewSet)
# router.register(r'payment-plans', delete_property, PaymentPlanViewSet, basename='payment-plan')
router.register(r'payments', PaymentViewSet)

urlpatterns = [
    path('', views.property_list, name='property_list'),
    path('edit-property/<int:pk>/', views.edit_property, name='edit_property'),
    path('<int:pk>/delete/', views.delete_property, name='delete_property'),
    # path('all-properties/', views.PropertyListView.as_view(), name='property-list'),
    path('<int:pk>/', views.property_detail, name='property_detail'),
    path('upload-property/', PropertyUploadView.as_view(), name='upload-property'),

    # Authentication
    path('api/auth/token/', obtain_auth_token, name='auth-token'), # or logging in a user and receiving an authentication token.
    path('api/', include(router.urls)), # handles user-related operations like registration, password reset, and user info retrieval.

    path('auth/register/', views.register_user, name='register_user'),
    path('auth/login/', views.login_user, name='login_user'),
    path('auth/logout/', views.logout_user, name='logout_user'),
    path('auth/password-reset/', views.reset_password, name='password_reset'),

    # Payment
    # path('api/', include(router.urls)),
    path('payment-plan-list/', views.PaymentPlanView.as_view()),
    path('payment-plans/<int:plan_id>/make-payment/', views.make_payment, name='make-payment'),
    path('payment-plans/<int:plan_id>/', views.PaymentPlanView.as_view(), name='make-payment'),
    path('payments-list/', views.PaymentView.as_view()),
    path('payments/payment-plans/user/<int:pk>/', views.UserPaymentPlansView.as_view(), name='user-payment-plans'),
    path('payments/payments-by-property/<int:property_id>/', views.PaymentByProperties.as_view(), name='payments-by-property'),
    # path('payments/property/<int:property_id>/', ),

    # Reports
    path('report-summary/', views.report_summary, name='report-summary'),

    # User List
    path('user-list/', views.UsersList.as_view()),
    path('user-list/<int:pk>/', views.UsersList.as_view())
]