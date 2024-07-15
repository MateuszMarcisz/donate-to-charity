from django.urls import path

from charity_donations import views

urlpatterns = [
    path('', views.LandingPageView.as_view(), name='LandingPage'),
    path('donation/', views.AddDonationView.as_view(), name='AddDonation'),
    path('login/', views.LoginView.as_view(), name='Login'),
    path('register/', views.RegisterView.as_view(), name='Register'),
]