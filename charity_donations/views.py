import json

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import models
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views import View

# from charity_donations.forms import ChangePasswordForm
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
        username = request.POST['username']
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
        username = request.POST.get('username')
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

    def post(self, request):
        donations = Donation.objects.filter(user=request.user)
        for donation in donations:
            is_taken_field = f'is_taken_{donation.id}'
            if is_taken_field in request.POST:
                donation.is_taken = True
            else:
                donation.is_taken = False
            donation.save()
        return redirect('Profile')


class SettingsView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        # update_info_form = UpdateInfoForm(instance=user)
        # change_password_form = ChangePasswordForm()
        context = {
            'user': user,
            # 'update_info_form': update_info_form,
            # 'change_password_form': change_password_form,
        }
        return render(request, 'settings.html', context)

    def post(self, request):
        user = request.user
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        form_type = request.POST.get('form_type')
        change_password = request.POST.get('change_password')
        change_password2 = request.POST.get('change_password2')

        if form_type == 'update_info':
            password_entered = request.POST.get('password')
            if user.check_password(password_entered):
                try:
                    user.username = username
                    user.email = email
                    user.first_name = first_name
                    user.last_name = last_name
                    user.save()
                    messages.success(request, 'Twoje dane zostały zmienione!')
                    return redirect('Settings')
                except Exception as e:
                    messages.error(request,
                                   'Incorrect password. Please enter your current password to update your information.')
            else:
                messages.error(request,
                               'Nieprawidłowe hasło użytkownika!')

        if form_type == 'update_password':
            confirm_password = request.POST.get('confirm_password')
            if user.check_password(confirm_password):
                if change_password == change_password2:
                    user.set_password(change_password)
                    user.save()
                    messages.success(request, 'Twoje hasło zostało zmienione!')
                else:
                    messages.error(request, 'Nowe hasła nie są zgodne')

            else:
                messages.error(request, 'Nieprawidłowe hasło użytkownika!')

        # else:
        #     messages.error(request,
        #                    'There was an error updating your information. Please correct the errors below.')

        context = {
            'user': user,
        }
        return render(request, 'settings.html', context)
