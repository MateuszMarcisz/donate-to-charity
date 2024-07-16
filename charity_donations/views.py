from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import models
from django.shortcuts import render, redirect
from django.views import View

from charity_donations.models import Donation, Institution


# Create your views here.

class LandingPageView(View):

    def get(self, request):
        number_of_bags = Donation.objects.aggregate(total_bags=models.Sum('quantity'))['total_bags'] or 0
        number_of_institutions = Donation.objects.values('institution').distinct().count()

        foundations = Institution.objects.filter(type=Institution.FOUNDATION)
        paginator_foundations = Paginator(foundations, 5)
        page_number_foundations = request.GET.get('page_foundations')
        page_object_foundations = paginator_foundations.get_page(page_number_foundations)

        local_collections = Institution.objects.filter(type=Institution.LOCAL_COLLECTION)
        paginator_local_collections = Paginator(local_collections, 5)
        page_number_local_collections = request.GET.get('page_local_collections')
        page_object_local_collections = paginator_local_collections.get_page(page_number_local_collections)

        ngos = Institution.objects.filter(type=Institution.NGO)
        paginator_ngos = Paginator(ngos, 5)
        page_number_ngos = request.GET.get('page_ngos')
        page_object_ngos = paginator_ngos.get_page(page_number_ngos)

        context = {
            'number_of_bags': number_of_bags,
            'number_of_institutions': number_of_institutions,
            'foundations': page_object_foundations,
            'local_collections': page_object_local_collections,
            'ngos': page_object_ngos,
        }

        return render(request, 'index.html', context)


class AddDonationView(View):
    def get(self, request):
        return render(request, 'form.html')


class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        username = request.POST['email']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        if user is not None:
            redirect_url = request.GET.get('next', 'LandingPage')
            login(request, user)
            return redirect(redirect_url)
        else:
            if not User.objects.filter(username=username).exists():
                return redirect('Register')
            error = "Nieprawidłowa nazwa użytkownika lub hasło"
            return render(request, "login.html", {'error': error})


class LogoutView(View):
    def post(self, request):
        logout(request)
        return redirect('LandingPage')


class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        first_name = request.POST.get('name')
        last_name = request.POST.get('surname')
        username = request.POST.get('email')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        if password != "" and password == password2:
            if User.objects.filter(username=username).exists():
                return render(request, 'register.html', {'error': 'Użytkownik o podanym adresie email już istnieje'})
            u = User(username=username, email=email, first_name=first_name, last_name=last_name)
            u.set_password(password)
            u.save()
            return redirect('Login')
        return render(request, 'register.html', {'error': 'Hasła nie są zgodne'})
