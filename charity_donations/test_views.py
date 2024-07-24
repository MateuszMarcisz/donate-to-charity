import json
from datetime import date, time
from urllib.parse import urlparse

import pytest
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.messages import get_messages
from django.core import mail
from django.core.paginator import Paginator
from django.test import TestCase, Client
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from pytest_django.asserts import assertContains, assertTemplateUsed

from charity_donations.admin import InstitutionAdmin
from charity_donations.forms import CustomSetPasswordForm, RegistrationForm, PasswordChangeForm, UserUpdateForm
from charity_donations.models import Donation, Institution


@pytest.mark.django_db
def test_login_view():
    client = Client()
    url = reverse('Login')
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_login_view_post(user):
    client = Client()
    url = reverse('Login')
    response = client.post(url, {'username': user.username, 'password': user.password})
    assert response.status_code == 200


@pytest.mark.django_db
def test_login_view_wrong_password(user):
    client = Client()
    url = reverse('Login')
    response = client.post(url, {'username': user.username, 'password': 'inne hasło'})
    assert response.status_code == 200
    assertContains(response, reverse('Login'))
    assertContains(response, "Nieprawidłowa nazwa użytkownika lub hasło")
    assert 'error' in response.context
    assert response.context['error'] == "Nieprawidłowa nazwa użytkownika lub hasło"


@pytest.mark.django_db
def test_login_view_wrong_username(user):
    client = Client()
    url = reverse('Login')
    response = client.post(url, {'username': "wrong username", 'password': user.username})
    assert response.status_code == 302
    assert response.url == reverse('Register')


@pytest.mark.django_db
def test_login_view_inactive_user(user):
    user.is_active = False
    user.save()

    client = Client()
    url = reverse('Login')
    response = client.post(url, {'username': user.username, 'password': 'Random?1'})

    assert response.status_code == 200
    assertContains(response,
                   "Twoje konto nie zostało aktywowane. Proszę, sprawdź swojego maila i aktywuj konto poprzez kliknięcie w link aktywacyjny.")
    assert 'error' in response.context
    assert response.context[
               'error'] == "Twoje konto nie zostało aktywowane. Proszę, sprawdź swojego maila i aktywuj konto poprzez kliknięcie w link aktywacyjny."


@pytest.mark.django_db
def test_login_redirect_for_inactive_user(user):
    user.is_active = False
    user.save()

    client = Client()
    url = reverse('Login')
    response = client.post(url, {'username': user.username, 'password': 'Random?1'}, follow=True)

    assert response.status_code == 200
    assert 'Twoje konto nie zostało aktywowane. Proszę, sprawdź swojego maila i aktywuj konto poprzez kliknięcie w link aktywacyjny.' in response.content.decode(
        'utf-8')


@pytest.mark.django_db
def test_login_view_changing_user_status_active(user):
    user.is_active = False
    user.save()

    client = Client()
    url = reverse('Login')
    response = client.post(url, {'username': user.username, 'password': 'Random?1'})

    assert response.status_code == 200
    assertContains(response,
                   "Twoje konto nie zostało aktywowane. Proszę, sprawdź swojego maila i aktywuj konto poprzez kliknięcie w link aktywacyjny.")
    assert 'error' in response.context
    assert response.context[
               'error'] == "Twoje konto nie zostało aktywowane. Proszę, sprawdź swojego maila i aktywuj konto poprzez kliknięcie w link aktywacyjny."

    user.is_active = True
    user.save()
    response = client.post(url, {'username': user.username, 'password': user.password})
    assert response.status_code == 200


def test_logout_view():
    client = Client()
    url = reverse('Logout')
    response = client.post(url)
    assert response.status_code == 302
    assert response.url == reverse('LandingPage')


def test_register_view_get():
    client = Client()
    url = reverse('Register')
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'register.html')
    assertContains(response, 'name="name"')
    assertContains(response, 'name="surname"')
    assertContains(response, 'name="username"')
    assertContains(response, 'name="email"')
    assertContains(response, 'name="password"')
    assertContains(response, 'name="password2"')


@pytest.mark.django_db
def test_register_view_post():
    client = Client()
    url = reverse('Register')
    data = {
        'first_name': 'test',
        'last_name': 'test',
        'username': 'test',
        'email': 'test@gmail.com',
        'password': 'Random?1',
        'password2': 'Random?1',
    }
    response = client.post(url, data)
    assert response.status_code == 302
    assert response.url == reverse('Login')
    assert User.objects.get(username='test')

    # checking for the message
    assert User.objects.filter(username='test').exists()
    messages = list(get_messages(response.wsgi_request))
    assert len(messages) == 1
    assert str(messages[0]) == 'Prosimy o potwierdzenie konta poprzez link wysłany na podane w rejestracji adres email.'

    # checking if email was send
    assert len(mail.outbox) == 1
    email = mail.outbox[0]
    assert email.subject == 'Activate your account.'

    # checking for the correct content of email
    email_body = email.body
    assert 'Hello test,' in email_body
    assert 'Please click the link below to activate your account:' in email_body
    assert 'http://testserver/activate/' in email_body  # Checking that activation link is in the email
    assert 'Thank you!' in email_body
    # Extract the activation link from the email body
    uid = urlsafe_base64_encode(force_bytes(User.objects.get(username='test').pk))
    token = default_token_generator.make_token(User.objects.get(username='test'))
    activation_link = f'http://testserver/activate/{uid}/{token}/'


@pytest.mark.django_db
def test_register_view_post_username_already_exists(user):
    client = Client()
    url = reverse('Register')
    data = {
        'first_name': 'test',
        'last_name': 'test',
        'username': 'test',
        'email': 'test@gmail.com',
        'password': 'Random?1',
        'password2': 'Random?1',
    }
    response = client.post(url, data)
    assert response.status_code == 200
    assertTemplateUsed(response, 'register.html')
    assertContains(response, reverse('Register'))
    assertContains(response, "Użytkownik o takiej nazwie już istnieje!")
    form = response.context['form']
    assert 'username' in form.errors
    assert form.errors['username'] == ['Użytkownik o takiej nazwie już istnieje!']


@pytest.mark.django_db
def test_register_view_post_email_already_exists(user):
    client = Client()
    url = reverse('Register')
    data = {
        'first_name': 'testy',
        'last_name': 'testy',
        'username': 'testy',
        'email': 'test@gmail.com',
        'password': 'Random?1',
        'password2': 'Random?1',
    }
    response = client.post(url, data)
    assert response.status_code == 200
    assertTemplateUsed(response, 'register.html')
    assertContains(response, reverse('Register'))
    assertContains(response, "Użytkownik o podanym adresie email już istnieje!")
    form = response.context['form']
    assert 'email' in form.errors
    assert form.errors['email'] == ["Użytkownik o podanym adresie email już istnieje!"]


@pytest.mark.django_db
def test_register_view_post_missing_username(user):
    client = Client()
    url = reverse('Register')
    data = {
        'first_name': 'test',
        'last_name': 'test',
        'email': 'test@gmail.com',
        'password': 'Random?1',
        'password2': 'Random?1',
    }
    response = client.post(url, data)
    assert response.status_code == 200
    print("Response content:", response.content.decode())
    assertTemplateUsed(response, 'register.html')
    assertContains(response, reverse('Register'))
    assertContains(response, 'Załóż konto')
    assertContains(response, "To pole jest wymagane.")
    form = response.context['form']
    assert 'username' in form.errors
    assert form.errors['username'] == ['To pole jest wymagane.']


@pytest.mark.django_db
def test_register_view_post_missing_name(user):
    client = Client()
    url = reverse('Register')
    data = {
        'last_name': 'testy',
        'username': 'testy',
        'email': 'test@gmail.com',
        'password': 'Random?1',
        'password2': 'Random?1',
    }
    response = client.post(url, data)
    assert response.status_code == 200
    assertTemplateUsed(response, 'register.html')
    assertContains(response, reverse('Register'))
    assertContains(response, 'Załóż konto')
    assertContains(response, "To pole jest wymagane.")
    form = response.context['form']
    assert 'first_name' in form.errors
    assert form.errors['first_name'] == ['To pole jest wymagane.']


@pytest.mark.django_db
def test_register_view_post_missing_email(user):
    client = Client()
    url = reverse('Register')
    data = {
        'first_name': 'testy',
        'last_name': 'testy',
        'username': 'testy',
        'password': 'Random?1',
        'password2': 'Random?1',
    }
    response = client.post(url, data)
    assert response.status_code == 200
    assertTemplateUsed(response, 'register.html')
    assertContains(response, reverse('Register'))
    assertContains(response, 'Załóż konto')
    assertContains(response, "To pole jest wymagane.")
    form = response.context['form']
    assert 'email' in form.errors
    assert form.errors['email'] == ['To pole jest wymagane.']


@pytest.mark.django_db
def test_register_view_post_missing_multiple_fields(user):
    client = Client()
    url = reverse('Register')
    data = {
        'name': 'test',
        'surname': 'test',
        'password': 'Random?1',
        'password2': 'Random?1',
    }
    response = client.post(url, data)
    assert response.status_code == 200
    assertTemplateUsed(response, 'register.html')
    assertContains(response, reverse('Register'))
    assertContains(response, 'Załóż konto')
    assertContains(response, "To pole jest wymagane.")
    form = response.context['form']
    expected_error_message = "To pole jest wymagane."
    required_fields = ['first_name', 'last_name', 'username', 'email']
    for field in required_fields:
        assert field in form.errors
        assert expected_error_message in form.errors[field]


@pytest.mark.django_db
def test_register_view_post_not_matching_passwords(user):
    client = Client()
    url = reverse('Register')
    data = {
        'first_name': 'testy',
        'last_name': 'testy',
        'username': 'testy',
        'email': 'test@gmail.com',
        'password': 'Random?1',
        'password2': 'Random?',
    }
    response = client.post(url, data)
    assert response.status_code == 200
    assertTemplateUsed(response, 'register.html')
    assertContains(response, reverse('Register'))
    assertContains(response, 'Załóż konto')
    assertContains(response, "Hasła nie są zgodne!")
    form = response.context['form']
    assert 'password2' in form.errors
    assert "Hasła nie są zgodne!" in form.errors['password2']


@pytest.mark.django_db
def test_register_view_post_password_validation_errors(user):
    client = Client()
    url = reverse('Register')

    # Scenario 1: Password too short
    data = {
        'first_name': 'testy',
        'last_name': 'testy',
        'username': 'testy',
        'email': 'test@gmail.com',
        'password': 'short',
        'password2': 'short',
    }
    response = client.post(url, data)
    assert response.status_code == 200
    assertTemplateUsed(response, 'register.html')
    assertContains(response, 'Załóż konto')
    form = response.context['form']
    assert 'password' in form.errors
    assert 'Twoje hasło musi zawierać przynajmniej 8 znaków.' in form.errors['password']

    # Scenario 2: Password missing uppercase letter
    data = {
        'first_name': 'testy',
        'last_name': 'testy',
        'username': 'testy',
        'email': 'test@gmail.com',
        'password': 'password1!',
        'password2': 'password1!',
    }
    response = client.post(url, data)
    assert response.status_code == 200
    assertTemplateUsed(response, 'register.html')
    assertContains(response, 'Załóż konto')
    form = response.context['form']
    assert 'password' in form.errors
    assert 'Hasło musi zawierać co najmniej jedną wielką literę.' in form.errors['password']

    # Scenario 3: Password missing lowercase letter
    data = {
        'first_name': 'testy',
        'last_name': 'testy',
        'username': 'testy',
        'email': 'test@gmail.com',
        'password': 'PASSWORD1!',
        'password2': 'PASSWORD1!',
    }
    response = client.post(url, data)
    assert response.status_code == 200
    assertTemplateUsed(response, 'register.html')
    assertContains(response, 'Załóż konto')
    form = response.context['form']
    assert 'password' in form.errors
    assert 'Hasło musi zawierać co najmniej jedną małą literę.' in form.errors['password']

    # Scenario 4: Password missing number
    data = {
        'first_name': 'testy',
        'last_name': 'testy',
        'username': 'testy',
        'email': 'test@gmail.com',
        'password': 'Password!',
        'password2': 'Password!',
    }
    response = client.post(url, data)
    assert response.status_code == 200
    assertTemplateUsed(response, 'register.html')
    assertContains(response, 'Załóż konto')
    form = response.context['form']
    assert 'password' in form.errors
    assert 'Hasło musi zawierać co najmniej jedną cyfrę.' in form.errors['password']

    # Scenario 5: Password missing special character
    data = {
        'first_name': 'testy',
        'last_name': 'testy',
        'username': 'testy',
        'email': 'test@gmail.com',
        'password': 'Password1',
        'password2': 'Password1',
    }
    response = client.post(url, data)
    assert response.status_code == 200
    assertTemplateUsed(response, 'register.html')
    assertContains(response, 'Załóż konto')
    form = response.context['form']
    assert 'password' in form.errors
    assert 'Hasło musi zawierać co najmniej jeden znak specjalny.' in form.errors['password']

    # Scenario 6: Passwords match but still fail validation
    data = {
        'first_name': 'testy',
        'last_name': 'testy',
        'username': 'testy',
        'email': 'test@gmail.com',
        'password': 'P@ssw1',
        'password2': 'P@ssw1',
    }
    response = client.post(url, data)
    assert response.status_code == 200
    assertTemplateUsed(response, 'register.html')
    assertContains(response, 'Załóż konto')
    form = response.context['form']
    assert 'password' in form.errors
    assert 'Twoje hasło musi zawierać przynajmniej 8 znaków.' in form.errors['password']


@pytest.mark.django_db
def test_landing_page_view_get_display_numbers(donations):
    client = Client()
    url = reverse('LandingPage')
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'index.html')

    # checking number of bags
    expected_number_of_bags = sum(donation.quantity for donation in donations)
    assertContains(response, f'<em>{expected_number_of_bags}</em><h3>Oddanych worków</h3>', html=True)

    # checking number of helped institutions
    expected_number_of_institutions = Donation.objects.values('institution').distinct().count()
    assertContains(response, f'<em>{expected_number_of_institutions}</em><h3>Wspartych organizacji</h3>', html=True)


@pytest.mark.django_db
def test_landing_page_view_get_pagination(donations, request_factory):
    client = Client()
    url = reverse('LandingPage')
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'index.html')

    request = request_factory.get(url)

    # checking pagination
    foundations = Institution.objects.filter(type=Institution.FOUNDATION)
    paginator = Paginator(foundations, 3)
    assert paginator.num_pages == 4  # 10 objects, 3 per page

    page_number = request.GET.get('page_foundations')
    page_object = paginator.get_page(page_number)

    for institution in page_object:
        assertContains(response, institution.name)

    if page_object.has_previous():
        assertContains(response, f'href="?page_foundations={page_object.previous_page_number}"')
    assertContains(response, f'Strona {page_object.number} z {paginator.num_pages}')


@pytest.mark.django_db
def test_add_donation_view_get(user):
    client = Client()
    client.login(username='test', password='Random?1')
    url = reverse('AddDonation')
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'form.html')


@pytest.mark.django_db
def test_add_donation_view_not_logged(user):
    client = Client()
    url = reverse('AddDonation')
    response = client.get(url)
    assert response.status_code == 302
    assert response.url.startswith(reverse('Login'))
    assert 'next=/donation/' in response.url


@pytest.mark.django_db
def test_add_donation_view_get_check_for_context_in_form(user, donations, institutions, categories):
    client = Client()
    client.force_login(user)
    url = reverse('AddDonation')
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'form.html')

    categories_in_context = response.context['categories']
    assert len(categories_in_context) == len(categories)
    for category in categories_in_context:
        assert category in categories

    organizations_in_context = response.context['organizations']
    assert len(organizations_in_context) == len(institutions)
    for organization in organizations_in_context:
        assert organization in institutions

    for organization in organizations_in_context:
        category_ids = list(organization.categories.values_list('id', flat=True))
        assert organization.category_ids_json == json.dumps(category_ids)


@pytest.mark.django_db
def test_add_donation_view_post(user, categories, institutions, donations):
    client = Client()
    client.force_login(user)

    initial_donation_count = Donation.objects.count()

    organization = institutions[0]
    data = {
        'bags': 5,
        'categories': [category.id for category in categories[:2]],
        'organization': organization.id,
        'address': 'Test Address',
        'city': 'Test City',
        'postcode': '12345',
        'phone': '1234567890',
        'date': str(date.today()),
        'time': str(time(10, 30)),
        'more_info': 'Some additional information'
    }

    url = reverse('AddDonation')
    response = client.post(url, data)
    assert response.status_code == 302
    assert response.url == reverse('FormConfirmation')
    assert Donation.objects.count() == initial_donation_count + 1

    donation = Donation.objects.get(
        quantity=data['bags'],
        institution=organization,
        address=data['address'],
        city=data['city'],
        zip_code=data['postcode'],
        phone_number=data['phone'],
        pick_up_date=date.today(),
        pick_up_time=time(10, 30),
        pick_up_comment=data['more_info'],
        user=user
    )
    assert donation.quantity == data['bags']
    assert donation.institution == organization
    assert donation.address == data['address']
    assert donation.city == data['city']
    assert donation.zip_code == data['postcode']
    assert donation.phone_number == data['phone']
    assert donation.pick_up_date == date.today()
    assert donation.pick_up_time == time(10, 30)
    assert donation.pick_up_comment == data['more_info']
    assert donation.user == user

    assert list(donation.categories.all().values_list('id', flat=True)) == data['categories']


@pytest.mark.django_db
def test_add_donation_view_post_missing_data(user, categories, institutions):
    client = Client()
    client.force_login(user)

    initial_donation_count = Donation.objects.count()

    organization = institutions[0]

    # no bags
    data = {
        'categories': [category.id for category in categories[:2]],
        'organization': organization.id,
        'address': 'Test Address',
        'city': 'Test City',
        'postcode': '12345',
        'phone': '1234567890',
        'date': str(date.today()),
        'time': str(time(10, 30)),
        'more_info': 'Some additional information'
    }
    url = reverse('AddDonation')
    response = client.post(url, data)
    assert response.status_code == 400
    assert response.content.decode('utf-8') == "Missing required data"
    assert Donation.objects.count() == initial_donation_count

    # no categories
    data = {
        'bags': 5,
        'organization': organization.id,
        'address': 'Test Address',
        'city': 'Test City',
        'postcode': '12345',
        'phone': '1234567890',
        'date': str(date.today()),
        'time': str(time(10, 30)),
        'more_info': 'Some additional information'
    }
    url = reverse('AddDonation')
    response = client.post(url, data)
    assert response.status_code == 400
    assert response.content.decode('utf-8') == "Missing required data"
    assert Donation.objects.count() == initial_donation_count

    # no organization
    data = {
        'bags': 5,
        'categories': [category.id for category in categories[:2]],
        'address': 'Test Address',
        'city': 'Test City',
        'postcode': '12345',
        'phone': '1234567890',
        'date': str(date.today()),
        'time': str(time(10, 30)),
        'more_info': 'Some additional information'
    }
    url = reverse('AddDonation')
    response = client.post(url, data)
    assert response.status_code == 400
    assert response.content.decode('utf-8') == "Missing required data"
    assert Donation.objects.count() == initial_donation_count

    # no phone
    data = {
        'bags': 5,
        'categories': [category.id for category in categories[:2]],
        'organization': organization.id,
        'address': 'Test Address',
        'city': 'Test City',
        'postcode': '12345',
        'date': str(date.today()),
        'time': str(time(10, 30)),
        'more_info': 'Some additional information'
    }
    url = reverse('AddDonation')
    response = client.post(url, data)
    assert response.status_code == 400
    assert response.content.decode('utf-8') == "Missing required data"
    assert Donation.objects.count() == initial_donation_count

    # no date
    data = {
        'bags': 5,
        'categories': [category.id for category in categories[:2]],
        'organization': organization.id,
        'address': 'Test Address',
        'city': 'Test City',
        'postcode': '12345',
        'phone': '1234567890',
        'time': str(time(10, 30)),
        'more_info': 'Some additional information'
    }
    url = reverse('AddDonation')
    response = client.post(url, data)
    assert response.status_code == 400
    assert response.content.decode('utf-8') == "Missing required data"
    assert Donation.objects.count() == initial_donation_count


@pytest.mark.django_db
def test_confirmation_view(user):
    client = Client()
    client.force_login(user)
    url = reverse('FormConfirmation')
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'form-confirmation.html')


@pytest.mark.django_db
def test_confirmation_view_not_logged(user):
    client = Client()
    url = reverse('FormConfirmation')
    response = client.get(url)
    assert response.status_code == 302
    assert response.url.startswith(reverse('Login'))
    assert 'next=/donation/form-confirmation/' in response.url


@pytest.mark.django_db
def test_profile_view_get(user):
    client = Client()
    client.force_login(user)
    url = reverse('Profile')
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'profile.html')


@pytest.mark.django_db
def test_profile_view_get_not_logged(user):
    client = Client()
    url = reverse('Profile')
    response = client.get(url)
    assert response.status_code == 302
    assert response.url.startswith(reverse('Login'))
    assert '/login/?next=/profile/' in response.url


@pytest.mark.django_db
def test_profile_view_get_display_donations(user, institutions, categories):
    client = Client()
    client.force_login(user)
    url = reverse('Profile')
    initial_donation_count = Donation.objects.count()

    donation1 = Donation.objects.create(
        quantity=5,
        institution=institutions[0],
        pick_up_date=date(2024, 7, 18),
        pick_up_time=time(10, 0),
        user=user,
        is_taken=False,
        address='Street',
        phone_number='123456789',
        city='City',
        zip_code='12345',
        pick_up_comment=f'Comment for Donation'
    )
    donation1.categories.set(categories)

    response = client.get(url)
    assert response.status_code == 200
    assert 'Brak przekazanych darów.' not in response.content.decode('utf-8')

    assert Donation.objects.count() == initial_donation_count + 1

    donation2 = Donation.objects.create(
        quantity=7,
        institution=institutions[1],
        pick_up_date=date(2024, 8, 28),
        pick_up_time=time(17, 15),
        user=user,
        is_taken=False,
        address='Street',
        phone_number='123456789',
        city='City',
        zip_code='12345',
        pick_up_comment=f'Comment for Donation'
    )
    donation2.categories.set(categories)
    response = client.get(url)
    assert response.status_code == 200
    assert 'Brak przekazanych darów.' not in response.content.decode('utf-8')
    assert Donation.objects.count() == initial_donation_count + 2


@pytest.mark.django_db
def test_profile_view_post_method(user, donations):
    client = Client()
    client.force_login(user)
    url = reverse('Profile')

    post_data = {f'is_taken_{donation.id}': 'true' for donation in donations}

    response = client.post(url, post_data, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain[-1][0] == reverse('Profile')

    for donation in donations:
        donation.refresh_from_db()
        assert donation.is_taken is True


@pytest.mark.django_db
def test_profile_view_post_method_another_case(user, donations):
    client = Client()
    client.force_login(user)
    url = reverse('Profile')

    post_data = {}
    for donation in donations:
        if donation.id in [donations[2].id, donations[6].id]:
            post_data[f'is_taken_{donation.id}'] = 'true'

    response = client.post(url, post_data, follow=True)

    assert response.status_code == 200
    assert response.redirect_chain[-1][0] == reverse('Profile')

    for donation in donations:
        donation.refresh_from_db()
        if donation.id in [donations[2].id, donations[6].id]:
            assert donation.is_taken is True
        else:
            assert donation.is_taken is False


@pytest.mark.django_db
def test_settings_view_get(user):
    client = Client()
    client.force_login(user)
    url = reverse('Settings')
    response = client.get(url)
    assert response.status_code == 200
    assertTemplateUsed(response, 'settings.html')


@pytest.mark.django_db
def test_profile_view_not_logged(user):
    client = Client()
    url = reverse('Settings')
    response = client.get(url)
    assert response.status_code == 302
    assert response.url.startswith(reverse('Login'))
    assert '/login/?next=/settings/' in response.url


@pytest.mark.django_db
def test_settings_view_get_user_details(user):
    client = Client()
    client.force_login(user)
    url = reverse('Settings')
    response = client.get(url)
    assert 'user' in response.context
    assert response.context['user'] == user

    content = response.content.decode()
    assert user.username in content
    assert user.email in content
    assert user.first_name in content
    assert user.last_name in content


@pytest.mark.django_db
def test_settings_post_info_update(user):
    client = Client()
    client.force_login(user)
    url = reverse('Settings')

    post_data = {
        'form_type': 'update_info',
        'username': 'newusername',
        'email': 'newemail@example.com',
        'first_name': 'NewFirstName',
        'last_name': 'NewLastName',
        'password': 'Random?1',
    }

    response = client.post(url, post_data, follow=True)
    user.refresh_from_db()

    assert response.status_code == 200
    assert user.username == 'newusername'
    assert user.email == 'newemail@example.com'
    assert user.first_name == 'NewFirstName'
    assert user.last_name == 'NewLastName'

    messages = list(get_messages(response.wsgi_request))
    assert any("Twoje dane zostały zmienione!" in str(message) for message in messages)


@pytest.mark.django_db
def test_settings_post_info_update_wrong_password(user):
    client = Client()
    client.force_login(user)
    url = reverse('Settings')

    post_data = {
        'form_type': 'update_info',
        'username': 'newusername',
        'email': 'newemail@example.com',
        'first_name': 'NewFirstName',
        'last_name': 'NewLastName',
        'password': 'wrongpassword',  # Incorrect password
    }

    response = client.post(url, post_data, follow=True)
    user.refresh_from_db()

    assert response.status_code == 200
    assert user.username != 'newusername'
    assert user.email != 'newemail@example.com'
    assert user.first_name != 'NewFirstName'
    assert user.last_name != 'NewLastName'

    form = response.context['user_update_form']
    assert form.errors
    assert 'Nieprawidłowe hasło użytkownika!' in form.errors.get('password', [])


@pytest.mark.django_db
def test_settings_post_info_update_existing_username(user):
    # Create another user with the same username
    User.objects.create_user(
        username='existingusername',
        email='existing@example.com',
        password='password123'
    )

    client = Client()
    client.force_login(user)
    url = reverse('Settings')

    post_data = {
        'form_type': 'update_info',
        'username': 'existingusername',  # Username that already exists
        'email': 'newemail@example.com',
        'first_name': 'NewFirstName',
        'last_name': 'NewLastName',
        'password': 'Random?1',
    }

    response = client.post(url, post_data, follow=True)
    user.refresh_from_db()

    assert response.status_code == 200
    assert user.username != 'existingusername'
    assert user.email != 'newemail@example.com'
    assert user.first_name != 'NewFirstName'
    assert user.last_name != 'NewLastName'

    form = response.context['user_update_form']
    assert form.errors
    assert 'Użytkownik o takiej nazwie już istnieje!' in form.errors.get('username', [])


@pytest.mark.django_db
def test_settings_post_info_update_existing_email(user):
    # Create another user with the same email
    User.objects.create_user(
        username='anotheruser',
        email='existing@example.com',
        password='password123'
    )

    client = Client()
    client.force_login(user)
    url = reverse('Settings')

    post_data = {
        'form_type': 'update_info',
        'username': 'newusername',
        'email': 'existing@example.com',  # Email that already exists
        'first_name': 'NewFirstName',
        'last_name': 'NewLastName',
        'password': 'Random?1',
    }

    response = client.post(url, post_data, follow=True)
    user.refresh_from_db()

    assert response.status_code == 200
    assert user.username != 'newusername'
    assert user.email != 'existing@example.com'
    assert user.first_name != 'NewFirstName'
    assert user.last_name != 'NewLastName'

    form = response.context['user_update_form']
    assert form.errors
    assert 'Użytkownik o podanym adresie email już istnieje!' in form.errors.get('email', [])


@pytest.mark.django_db
def test_settings_post_password_change(user):
    client = Client()
    client.force_login(user)
    url = reverse('Settings')

    post_data = {
        'form_type': 'update_password',
        'change_password': 'Newpassword?1',
        'change_password2': 'Newpassword?1',
        'confirm_password': 'Random?1',
    }

    response = client.post(url, post_data, follow=True)
    user.refresh_from_db()

    assert response.status_code == 200
    assert user.check_password('Newpassword?1')

    messages = list(get_messages(response.wsgi_request))
    assert any("Twoje hasło zostało zmienione!" in str(message) for message in messages)


@pytest.mark.django_db
def test_settings_post_password_change_non_matching_new_passwords(user):
    client = Client()
    client.force_login(user)
    url = reverse('Settings')

    post_data = {
        'form_type': 'update_password',
        'change_password': 'New0ne1?69',
        'change_password2': 'New0ne1?6',
        'confirm_password': 'Random?1',
    }

    response = client.post(url, post_data, follow=True)
    user.refresh_from_db()
    assert response.status_code == 200
    assert not user.check_password('New0ne1?69')
    assert not user.check_password('New0ne1?6')

    form = response.context['password_form']
    assert form.errors
    assert 'Nowe hasła nie są zgodne.' in form.errors.get('change_password2', [])


@pytest.mark.django_db
def test_settings_post_password_validation_errors(user):
    client = Client()
    client.force_login(user)
    url = reverse('Settings')

    # Scenario 1: Password too short
    data = {
        'form_type': 'update_password',
        'change_password': 'short',
        'change_password2': 'short',
        'confirm_password': 'CurrentValidPassword1!'
    }
    response = client.post(url, data, follow=True)
    assert response.status_code == 200
    assert 'change_password' in response.context['password_form'].errors
    assert 'Twoje hasło musi zawierać przynajmniej 8 znaków.' in response.context['password_form'].errors[
        'change_password']

    # Scenario 2: Password missing uppercase letter
    data = {
        'form_type': 'update_password',
        'change_password': 'lowercase1!',
        'change_password2': 'lowercase1!',
        'confirm_password': 'CurrentValidPassword1!'
    }
    response = client.post(url, data, follow=True)
    assert response.status_code == 200
    assert 'change_password' in response.context['password_form'].errors
    assert 'Hasło musi zawierać co najmniej jedną wielką literę.' in response.context['password_form'].errors[
        'change_password']

    # Scenario 3: Password missing lowercase letter
    data = {
        'form_type': 'update_password',
        'change_password': 'UPPERCASE1!',
        'change_password2': 'UPPERCASE1!',
        'confirm_password': 'CurrentValidPassword1!'
    }
    response = client.post(url, data, follow=True)
    assert response.status_code == 200
    assert 'change_password' in response.context['password_form'].errors
    assert 'Hasło musi zawierać co najmniej jedną małą literę.' in response.context['password_form'].errors[
        'change_password']

    # Scenario 4: Password missing number
    data = {
        'form_type': 'update_password',
        'change_password': 'NoNumber!',
        'change_password2': 'NoNumber!',
        'confirm_password': 'CurrentValidPassword1!'
    }
    response = client.post(url, data, follow=True)
    assert response.status_code == 200
    assert 'change_password' in response.context['password_form'].errors
    assert 'Hasło musi zawierać co najmniej jedną cyfrę.' in response.context['password_form'].errors['change_password']

    # Scenario 5: Password missing special character
    data = {
        'form_type': 'update_password',
        'change_password': 'NoSpecialChar1',
        'change_password2': 'NoSpecialChar1',
        'confirm_password': 'CurrentValidPassword1!'
    }
    response = client.post(url, data, follow=True)
    assert response.status_code == 200
    assert 'change_password' in response.context['password_form'].errors
    assert 'Hasło musi zawierać co najmniej jeden znak specjalny.' in response.context['password_form'].errors[
        'change_password']


@pytest.mark.django_db
def test_settings_post_password_change_incorrect_current_password(user):
    client = Client()
    client.force_login(user)
    url = reverse('Settings')

    post_data = {
        'form_type': 'update_password',
        'change_password': 'Newpassword1!',
        'change_password2': 'Newpassword1!',
        'confirm_password': 'wrongpassword',
    }

    response = client.post(url, post_data, follow=True)
    user.refresh_from_db()

    assert response.status_code == 200
    assert not user.check_password('Newpassword1!')

    form = response.context['password_form']
    assert form.errors
    assert 'Nieprawidłowe hasło użytkownika!' in form.errors.get('confirm_password', [])


# testing admin.py
@pytest.mark.django_db
def test_institution_admin_list_display(user, institutions):
    user.is_superuser = True
    user.is_staff = True
    user.save()

    client = Client()
    client.force_login(user)
    url = reverse('admin:%s_%s_changelist' % (
        Institution._meta.app_label, Institution._meta.model_name
    ))
    response = client.get(url)
    assert response.status_code == 200
    assert any(inst.name in response.content.decode() for inst in institutions)
    assert any(inst.description in response.content.decode() for inst in institutions)

    # searching
    search_url = f"{url}?q=Institution 0"
    response = client.get(search_url)
    assert response.status_code == 200
    assert 'Institution 0' in response.content.decode()

    # Filtering
    filter_url = f"{url}?type={Institution.FOUNDATION}"
    response = client.get(filter_url)
    assert response.status_code == 200
    assert all(inst.type == Institution.FOUNDATION for inst in institutions)

    admin_instance = InstitutionAdmin(Institution, admin.site)
    for institution in institutions:
        display = admin_instance.type_display(institution)
        assert display == 'Fundacja'


@pytest.mark.django_db
def test_custom_password_reset_confirm_view(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    client = Client()
    url = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})

    response = client.get(url)
    assert response.status_code == 302
    redirect_url = response['Location']
    expected_redirect_url = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': 'set-password'})
    parsed_redirect_url = urlparse(redirect_url)
    parsed_expected_url = urlparse(expected_redirect_url)
    response = client.get(redirect_url)
    assert response.status_code == 200
    assert 'new_password1' in response.content.decode()
    assert 'new_password2' in response.content.decode()


# testing forms.py

@pytest.mark.django_db
def test_custom_set_password_form(user):
    user.set_password('InitialPassword1!')
    user.save()

    # Testing valid password change
    form = CustomSetPasswordForm(user=user, data={
        'new_password1': 'NewPassword1!',
        'new_password2': 'NewPassword1!'
    })
    assert form.is_valid()
    form.save()
    assert user.check_password('NewPassword1!')

    # Testing password mismatch
    form = CustomSetPasswordForm(user=user, data={
        'new_password1': 'NewPassword1!',
        'new_password2': 'DifferentPassword2!'
    })
    assert not form.is_valid()
    assert form.errors['new_password2'] == ['Nowe hasła nie są takie same.']

    # Testing invalid password
    form = CustomSetPasswordForm(user=user, data={
        'new_password1': 'short',
        'new_password2': 'short'
    })
    assert not form.is_valid()
    assert 'new_password2' in form.errors


@pytest.mark.django_db
def test_registration_form(user):
    # Testing valid registration
    form = RegistrationForm(data={
        'first_name': 'John',
        'last_name': 'Doe',
        'username': 'johndoe',
        'email': 'johndoe@example.com',
        'password': 'ValidPassword1!',
        'password2': 'ValidPassword1!'
    })
    assert form.is_valid()
    user = form.save()
    assert User.objects.filter(username='johndoe').exists()

    # Testing password mismatch
    form = RegistrationForm(data={
        'first_name': 'John',
        'last_name': 'Doe',
        'username': 'johndoe',
        'email': 'johndoe@example.com',
        'password': 'ValidPassword1!',
        'password2': 'DifferentPassword1!'
    })
    assert not form.is_valid()
    assert form.errors['password2'] == ['Hasła nie są zgodne!']

    # Testing existing email
    User.objects.create_user(username='existinguser', email='johndoe@example.com', password='Password1!')
    form = RegistrationForm(data={
        'first_name': 'John',
        'last_name': 'Doe',
        'username': 'newuser',
        'email': 'johndoe@example.com',
        'password': 'ValidPassword1!',
        'password2': 'ValidPassword1!'
    })
    assert not form.is_valid()
    assert form.errors['email'] == ['Użytkownik o podanym adresie email już istnieje!']

    # Testing existing username
    form = RegistrationForm(data={
        'first_name': 'John',
        'last_name': 'Doe',
        'username': 'existinguser',
        'email': 'newemail@example.com',
        'password': 'ValidPassword1!',
        'password2': 'ValidPassword1!'
    })
    assert not form.is_valid()
    assert form.errors['username'] == ['Użytkownik o takiej nazwie już istnieje!']


@pytest.mark.django_db
def test_registration_form(user):
    # Testing valid registration
    form = RegistrationForm(data={
        'first_name': 'John',
        'last_name': 'Doe',
        'username': 'johndoe',
        'email': 'johndoe@example.com',
        'password': 'ValidPassword1!',
        'password2': 'ValidPassword1!'
    })
    assert form.is_valid()
    user = form.save()
    assert User.objects.filter(username='johndoe').exists()

    # Testing password mismatch
    form = RegistrationForm(data={
        'first_name': 'John',
        'last_name': 'Doe',
        'username': 'johndoe',
        'email': 'johndoe@example.com',
        'password': 'ValidPassword1!',
        'password2': 'DifferentPassword1!'
    })
    assert not form.is_valid()
    assert form.errors['password2'] == ['Hasła nie są zgodne!']

    # Testing existing email
    User.objects.create_user(username='existinguser', email='johndoe@example.com', password='Password1!')
    form = RegistrationForm(data={
        'first_name': 'John',
        'last_name': 'Doe',
        'username': 'newuser',
        'email': 'johndoe@example.com',
        'password': 'ValidPassword1!',
        'password2': 'ValidPassword1!'
    })
    assert not form.is_valid()
    assert form.errors['email'] == ['Użytkownik o podanym adresie email już istnieje!']

    # Testing existing username
    form = RegistrationForm(data={
        'first_name': 'John',
        'last_name': 'Doe',
        'username': 'existinguser',
        'email': 'newemail@example.com',
        'password': 'ValidPassword1!',
        'password2': 'ValidPassword1!'
    })
    assert not form.is_valid()
    assert form.errors['username'] == ['Użytkownik o takiej nazwie już istnieje!']


@pytest.mark.django_db
def test_password_change_form(user):
    user.set_password('OldPassword1!')
    user.save()

    # Testing valid password change
    form = PasswordChangeForm(user=user, data={
        'change_password': 'NewPassword1!',
        'change_password2': 'NewPassword1!',
        'confirm_password': 'OldPassword1!'
    })

    if form.is_valid():
        password = form.cleaned_data['change_password']
        user.set_password(password)
        user.save()

    user.refresh_from_db()
    assert user.check_password('NewPassword1!')

    # Testing password mismatch
    form = PasswordChangeForm(user=user, data={
        'change_password': 'NewPassword1!',
        'change_password2': 'DifferentPassword2!',
        'confirm_password': 'OldPassword1!'
    })
    assert not form.is_valid()
    assert form.errors['change_password2'] == ['Nowe hasła nie są zgodne.']

    # Testing incorrect current password
    form = PasswordChangeForm(user=user, data={
        'change_password': 'NewPassword1!',
        'change_password2': 'NewPassword1!',
        'confirm_password': 'WrongPassword!'
    })
    assert not form.is_valid()
    assert form.errors['confirm_password'] == ['Nieprawidłowe hasło użytkownika!']


@pytest.mark.django_db
def test_user_update_form(user):
    user.set_password('OldPassword1!')
    user.save()

    # Testing valid update
    form = UserUpdateForm(user=user, data={
        'username': 'newusername',
        'email': 'newemail@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'password': 'OldPassword1!'
    })
    assert form.is_valid()
    cleaned_data = form.cleaned_data
    user.username = cleaned_data['username']
    user.email = cleaned_data['email']
    user.first_name = cleaned_data['first_name']
    user.last_name = cleaned_data['last_name']
    user.save()
    user.refresh_from_db()
    assert user.username == 'newusername'
    assert user.email == 'newemail@example.com'
    assert user.first_name == 'John'
    assert user.last_name == 'Doe'

    # Testing invalid password
    form = UserUpdateForm(user=user, data={
        'username': 'newusername',
        'email': 'newemail@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'password': 'WrongPassword!'
    })
    assert not form.is_valid()
    assert form.errors['password'] == ['Nieprawidłowe hasło użytkownika!']

    # Testing existing username
    existing_user = User.objects.create_user(username='existinguser', email='existing@example.com',
                                             password='Password1!')
    form = UserUpdateForm(user=user, data={
        'username': 'existinguser',
        'email': 'newemail@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'password': 'OldPassword1!'
    })
    assert not form.is_valid()
    assert form.errors['username'] == ['Użytkownik o takiej nazwie już istnieje!']

    # Testing existing email
    form = UserUpdateForm(user=user, data={
        'username': 'newusername',
        'email': 'existing@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'password': 'OldPassword1!'
    })
    assert not form.is_valid()
    assert form.errors['email'] == ['Użytkownik o podanym adresie email już istnieje!']


# Testing superuser deleting restrains (deletion of last superuser)

@pytest.mark.django_db
def test_delete_last_superuser(superusers):
    client = Client()
    # Test that we can delete a superuser if more than one exists
    if len(superusers) > 1:
        client.force_login(superusers[0])

        user_to_delete = superusers[1]
        url = reverse('admin:auth_user_delete', args=[user_to_delete.id])
        response = client.post(url, {'post': 'yes'}, follow=True)
        assert response.status_code == 200
        assert not User.objects.filter(id=user_to_delete.id).exists()

    # Now test the case where only one superuser exists
    if len(superusers) == 1:
        client.login(username=superusers[0].username, password='Random?1')
        url = reverse('admin:auth_user_delete', args=[superusers[0].id])
        response = client.post(url, {'post': 'yes'}, follow=True)

        assert response.status_code == 403
        assert User.objects.filter(id=superusers[0].id).exists()
