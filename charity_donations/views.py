from django.db import models
from django.shortcuts import render
from django.views import View

from charity_donations.models import Donation, Institution


# Create your views here.

class LandingPageView(View):

    def get(self, request):

        number_of_bags = Donation.objects.aggregate(total_bags=models.Sum('quantity'))['total_bags'] or 0
        number_of_institutions = Donation.objects.values('institution').distinct().count()
        foundations = Institution.objects.filter(type=Institution.FOUNDATION)
        local_collections = Institution.objects.filter(type=Institution.LOCAL_COLLECTION)
        ngos = Institution.objects.filter(type=Institution.NGO)

        context = {
            'number_of_bags': number_of_bags,
            'number_of_institutions': number_of_institutions,
            'foundations': foundations,
            'local_collections': local_collections,
            'ngos': ngos,
        }

        return render(request, 'index.html', context)


class AddDonationView(View):
    def get(self, request):
        return render(request, 'form.html')


class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')


class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')
