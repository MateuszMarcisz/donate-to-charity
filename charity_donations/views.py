import json

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import models
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views import View

from charity_donations.models import Donation, Institution, Category


# Create your views here.

class LandingPageView(View):

    def get(self, request):
        number_of_bags = Donation.objects.aggregate(total_bags=models.Sum('quantity'))['total_bags'] or 0
        number_of_institutions = Donation.objects.values('institution').distinct().count()

        foundations = Institution.objects.filter(type=Institution.FOUNDATION)
        paginator_foundations = Paginator(foundations, 3)
        page_number_foundations = request.GET.get('page_foundations')
        page_object_foundations = paginator_foundations.get_page(page_number_foundations)

        local_collections = Institution.objects.filter(type=Institution.LOCAL_COLLECTION)
        paginator_local_collections = Paginator(local_collections, 3)
        page_number_local_collections = request.GET.get('page_local_collections')
        page_object_local_collections = paginator_local_collections.get_page(page_number_local_collections)

        ngos = Institution.objects.filter(type=Institution.NGO)
        paginator_ngos = Paginator(ngos, 3)
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


class AddDonationView(LoginRequiredMixin, View):
    def get(self, request):
        categories = Category.objects.all()
        organizations = Institution.objects.all()
        for organization in organizations:
            category_ids = list(organization.categories.values_list('id', flat=True))
            organization.category_ids_json = json.dumps(category_ids)

        context = {
            'categories': categories,
            'organizations': organizations,
        }

        return render(request, 'form.html', context)

    def post(self, request):
        bags = request.POST.get('bags')
        categories_ids = request.POST.getlist('categories')
        organization_id = request.POST.get('organization')
        address = request.POST.get('address')
        city = request.POST.get('city')
        postcode = request.POST.get('postcode')
        phone = request.POST.get('phone')
        date = request.POST.get('date')
        time = request.POST.get('time')
        more_info = request.POST.get('more_info')
        organization = Institution.objects.get(pk=organization_id)

        try:
            donation = Donation.objects.create(
                quantity=bags,
                institution=organization,
                address=address,
                phone_number=phone,
                city=city,
                zip_code=postcode,
                pick_up_date=date,
                pick_up_time=time,
                pick_up_comment=more_info,
                user=request.user
            )
            donation.categories.add(*categories_ids)

            return redirect('FormConfirmation')

        except Exception as e:
            return render(request, 'form.html', {'error_message': str(e)})


class FormConfirmationView(View):
    def get(self, request):
        return render(request, 'form-confirmation.html')


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


class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        donations = Donation.objects.filter(user=request.user)
        context = {
            'donations': donations,
        }

        return render(request, 'profile.html', context)
