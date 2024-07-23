from django.urls import path
from django.contrib.auth import views as auth_views
from charity_donations import views

urlpatterns = [
    path('', views.LandingPageView.as_view(), name='LandingPage'),
    path('donation/', views.AddDonationView.as_view(), name='AddDonation'),
    path('login/', views.LoginView.as_view(), name='Login'),
    path('register/', views.RegisterView.as_view(), name='Register'),
    path('logout/', views.LogoutView.as_view(), name='Logout'),
    path('donation/form-confirmation/', views.FormConfirmationView.as_view(), name='FormConfirmation'),
    path('profile/', views.ProfileView.as_view(), name='Profile'),
    path('settings/', views.SettingsView.as_view(), name='Settings'),
    path('activate/<uidb64>/<token>/', views.ActivateAccountView.as_view(), name='ActivateAccount'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
