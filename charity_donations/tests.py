import pytest
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from pytest_django.asserts import assertContains, assertTemplateUsed


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
