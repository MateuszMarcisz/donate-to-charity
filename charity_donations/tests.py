import json

import pytest
from django.contrib.auth.models import User
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
