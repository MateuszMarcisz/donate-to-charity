import json
from datetime import date, time

import pytest
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.core import mail
from django.core.paginator import Paginator
from django.test import TestCase, Client
from django.urls import reverse
from pytest_django.asserts import assertContains, assertTemplateUsed

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
    response = client.post(url, {'username': user.username, 'password': 'test password'})

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
    response = client.post(url, {'username': user.username, 'password': 'test password'}, follow=True)

    assert response.status_code == 200
    assert 'Twoje konto nie zostało aktywowane. Proszę, sprawdź swojego maila i aktywuj konto poprzez kliknięcie w link aktywacyjny.' in response.content.decode(
        'utf-8')


@pytest.mark.django_db
def test_login_view_changing_user_status_active(user):
    user.is_active = False
    user.save()

    client = Client()
    url = reverse('Login')
    response = client.post(url, {'username': user.username, 'password': 'test password'})

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
        'name': 'test',
        'surname': 'test',
        'username': 'test user',
        'email': 'test@gmail.com',
        'password': 'test password',
        'password2': 'test password',
    }
    response = client.post(url, data)
    assert response.status_code == 302
    assert response.url == reverse('Login')
    assert User.objects.get(username='test user')

    # checking for the message
    assert User.objects.filter(username='test user').exists()
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


@pytest.mark.django_db
def test_register_view_post_username_already_exists(user):
    client = Client()
    url = reverse('Register')
    data = {
        'name': 'test',
        'surname': 'test',
        'username': 'test user',
        'email': 'testowy@gmail.com',
        'password': 'test password',
        'password2': 'test password',
    }
    response = client.post(url, data)
    assert response.status_code == 200
    assertTemplateUsed(response, 'register.html')
    assertContains(response, reverse('Register'))
    assertContains(response, "Użytkownik o takiej nazwie już istnieje!")
    assert 'error' in response.context
    assert response.context['error'] == "Użytkownik o takiej nazwie już istnieje!"


@pytest.mark.django_db
def test_register_view_post_email_already_exists(user):
    client = Client()
    url = reverse('Register')
    data = {
        'name': 'test',
        'surname': 'test',
        'username': 'user',
        'email': 'test@gmail.com',
        'password': 'test password',
        'password2': 'test password',
    }
    response = client.post(url, data)
    assert response.status_code == 200
    assertTemplateUsed(response, 'register.html')
    assertContains(response, reverse('Register'))
    assertContains(response, "Użytkownik o podanym adresie email już istnieje!")
    assert 'error' in response.context
    assert response.context['error'] == "Użytkownik o podanym adresie email już istnieje!"


@pytest.mark.django_db
def test_register_view_post_missing_username(user):
    client = Client()
    url = reverse('Register')
    data = {
        'name': 'test',
        'surname': 'test',
        'email': 'test@gmail.com',
        'password': 'test password',
        'password2': 'test password',
    }
    response = client.post(url, data)
    assert response.status_code == 200
    assertTemplateUsed(response, 'register.html')
    assertContains(response, reverse('Register'))
    assertContains(response, "Wszystkie pola są wymagane!")
    assert 'error' in response.context
    assert response.context['error'] == "Wszystkie pola są wymagane!"


@pytest.mark.django_db
def test_register_view_post_missing_name(user):
    client = Client()
    url = reverse('Register')
    data = {
        'surname': 'test',
        'username': 'user',
        'email': 'test@gmail.com',
        'password': 'test password',
        'password2': 'test password',
    }
    response = client.post(url, data)
    assert response.status_code == 200
    assertTemplateUsed(response, 'register.html')
    assertContains(response, reverse('Register'))
    assertContains(response, "Wszystkie pola są wymagane!")
    assert 'error' in response.context
    assert response.context['error'] == "Wszystkie pola są wymagane!"


@pytest.mark.django_db
def test_register_view_post_missing_email(user):
    client = Client()
    url = reverse('Register')
    data = {
        'name': 'test',
        'surname': 'test',
        'username': 'user',
        'password': 'test password',
        'password2': 'test password',
    }
    response = client.post(url, data)
    assert response.status_code == 200
    assertTemplateUsed(response, 'register.html')
    assertContains(response, reverse('Register'))
    assertContains(response, "Wszystkie pola są wymagane!")
    assert 'error' in response.context
    assert response.context['error'] == "Wszystkie pola są wymagane!"


@pytest.mark.django_db
def test_register_view_post_missing_multiple_fields(user):
    client = Client()
    url = reverse('Register')
    data = {
        'name': 'test',
        'surname': 'test',
        'password': 'test password',
        'password2': 'test password',
    }
    response = client.post(url, data)
    assert response.status_code == 200
    assertTemplateUsed(response, 'register.html')
    assertContains(response, reverse('Register'))
    assertContains(response, "Wszystkie pola są wymagane!")
    assert 'error' in response.context
    assert response.context['error'] == "Wszystkie pola są wymagane!"


@pytest.mark.django_db
def test_register_view_post_not_matching_passwords(user):
    client = Client()
    url = reverse('Register')
    data = {
        'name': 'test',
        'surname': 'test',
        'username': 'user',
        'email': 'test@gmail.com',
        'password': 'test password',
        'password2': 'test password2',
    }
    response = client.post(url, data)
    assert response.status_code == 200
    assertTemplateUsed(response, 'register.html')
    assertContains(response, reverse('Register'))
    assertContains(response, "Hasła nie są zgodne!")
    assert 'error' in response.context
    assert response.context['error'] == "Hasła nie są zgodne!"


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
    client.login(username='test user', password='test password')
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
        'password': 'test password',
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

    messages = list(get_messages(response.wsgi_request))
    assert any("Nieprawidłowe hasło użytkownika!" in str(message) for message in messages)


@pytest.mark.django_db
def test_settings_post_password_change(user):
    client = Client()
    client.force_login(user)
    url = reverse('Settings')

    post_data = {
        'form_type': 'update_password',
        'change_password': 'newpassword',
        'change_password2': 'newpassword',
        'confirm_password': 'test password',
    }

    response = client.post(url, post_data, follow=True)
    user.refresh_from_db()

    assert response.status_code == 200
    assert user.check_password('newpassword')

    messages = list(get_messages(response.wsgi_request))
    assert any("Twoje hasło zostało zmienione!" in str(message) for message in messages)


@pytest.mark.django_db
def test_settings_post_password_change_non_matching_new_passwords(user):
    client = Client()
    client.force_login(user)
    url = reverse('Settings')

    post_data = {
        'form_type': 'update_password',
        'change_password': 'newpassword',
        'change_password2': 'differentnewpassword',
        'confirm_password': 'test password',
    }

    response = client.post(url, post_data, follow=True)
    user.refresh_from_db()

    assert response.status_code == 200
    assert not user.check_password('newpassword')
    assert not user.check_password('differentnewpassword')

    messages = list(get_messages(response.wsgi_request))
    assert any("Nowe hasła nie są zgodne" in str(message) for message in messages)


@pytest.mark.django_db
def test_settings_post_password_change_incorrect_current_password(user):
    client = Client()
    client.force_login(user)
    url = reverse('Settings')

    post_data = {
        'form_type': 'update_password',
        'change_password': 'newpassword',
        'change_password2': 'newpassword',
        'confirm_password': 'wrongpassword',
    }

    response = client.post(url, post_data, follow=True)
    user.refresh_from_db()

    assert response.status_code == 200
    assert not user.check_password('newpassword')

    messages = list(get_messages(response.wsgi_request))
    assert any("Nieprawidłowe hasło użytkownika!" in str(message) for message in messages)
