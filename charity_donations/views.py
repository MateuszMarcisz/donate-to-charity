import json

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetConfirmView
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import models
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import View

from charity_donations.forms import CustomSetPasswordForm, RegistrationForm, PasswordChangeForm, UserUpdateForm
# from charity_donations.forms import ChangePasswordForm
from charity_donations.models import Donation, Institution, Category
from config import settings


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
        # organization = Institution.objects.get(pk=organization_id)

        # If user is nasty and does something to the form using dev tools or JS
        if not (
                bags and categories_ids and organization_id and address and city and postcode and phone and date and time):
            return HttpResponseBadRequest("Missing required data")

        try:
            organization = Institution.objects.get(pk=organization_id)
        except Institution.DoesNotExist:
            return HttpResponseBadRequest("Invalid organization id")

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


class FormConfirmationView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'form-confirmation.html')


class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']

        # user = authenticate(username=username, password=password)
        # if user is not None:
        #     if user.is_active:
        #         redirect_url = request.GET.get('next', 'LandingPage')
        #         login(request, user)
        #         return redirect(redirect_url)
        #     else:
        #         error = ("""Twoje konto nie zostało aktywowane. Proszę, sprawdź swojego maila i aktywuj konto poprzez
        #                  kliknięcie w link aktywacyjny.""")
        #         return render(request, "login.html", {'error': error})
        # else:
        #     if not User.objects.filter(username=username).exists():
        #         return redirect('Register')
        #     error = "Nieprawidłowa nazwa użytkownika lub hasło"
        #     return render(request, "login.html", {'error': error})

        # Needed different approach
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # user does not exist, redirect to register
            return redirect('Register')

        # authentication
        if user.check_password(password):
            if user.is_active:
                # when user is active
                login(request, user)
                redirect_url = request.GET.get('next', 'LandingPage')
                return redirect(redirect_url)
            else:
                # when user is not active
                error = ("Twoje konto nie zostało aktywowane. Proszę, sprawdź swojego maila i aktywuj konto "
                         "poprzez kliknięcie w link aktywacyjny.")
                return render(request, "login.html", {'error': error})
        else:
            # wrong pswrd
            error = "Nieprawidłowa nazwa użytkownika lub hasło"
            return render(request, "login.html", {'error': error})


class LogoutView(View):
    def post(self, request):
        logout(request)
        return redirect('LandingPage')


class RegisterView(View):
    def get(self, request):
        form = RegistrationForm()
        return render(request, 'register.html', {'form': form})

    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')

            # Save the user with inactive status
            u = User(username=username, email=email, first_name=first_name, last_name=last_name, is_active=False)
            u.set_password(password)
            u.save()

            # Email account activation part
            current_site = get_current_site(request)
            mail_subject = 'Activate your account.'
            uid = urlsafe_base64_encode(force_bytes(u.pk))
            token = default_token_generator.make_token(u)
            message = render_to_string('activation_email.html', {
                'user': u,
                'domain': current_site.domain,
                'uid': uid,
                'token': token,
            })
            send_mail(mail_subject, message, settings.DEFAULT_FROM_EMAIL, [email])

            messages.success(request,
                             'Prosimy o potwierdzenie konta poprzez link wysłany na podane w rejestracji adres email.')
            return redirect('Login')

        return render(request, 'register.html', {'form': form})


class ActivateAccountView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            messages.success(request, 'Twoje Konto zostało aktywowane, możesz się teraz zalogować.')
            return redirect('Login')
        else:
            messages.error(request, 'Link aktywacyjny był niepoprawny!')
            return redirect('Register')


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
        password_form = PasswordChangeForm(user=user)
        user_update_form = UserUpdateForm(instance=user, user=user)
        context = {
            'user': user,
            'password_form': password_form,
            'user_update_form': user_update_form,
        }
        return render(request, 'settings.html', context)

    def post(self, request):
        user = request.user
        form_type = request.POST.get('form_type')

        if form_type == 'update_info':
            user_update_form = UserUpdateForm(request.POST, instance=user, user=user)
            if user_update_form.is_valid():
                user_update_form.save()
                messages.success(request, 'Twoje dane zostały zmienione!')
                return redirect('Settings')
            else:
                password_form = PasswordChangeForm(user=user)
                context = {
                    'user': user,
                    'password_form': password_form,
                    'user_update_form': user_update_form,
                }
                return render(request, 'settings.html', context)

        elif form_type == 'update_password':
            password_form = PasswordChangeForm(data=request.POST, user=user)
            if password_form.is_valid():
                new_password = password_form.cleaned_data['change_password']
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Twoje hasło zostało zmienione!')
                return redirect('Settings')
            else:
                user_update_form = UserUpdateForm(instance=user, user=user)
                context = {
                    'user': user,
                    'password_form': password_form,
                    'user_update_form': user_update_form,
                }
                return render(request, 'settings.html', context)

        else:
            messages.error(request, 'Nieprawidłowy typ formularza.')
            context = {
                'user': user,
                'password_form': PasswordChangeForm(user=user),
                'user_update_form': UserUpdateForm(instance=user, user=user)
            }
            return render(request, 'settings.html', context)


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = CustomSetPasswordForm
