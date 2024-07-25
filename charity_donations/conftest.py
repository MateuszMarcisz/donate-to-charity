from datetime import date, time

import pytest
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.test import RequestFactory
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from charity_donations.models import Category, Institution, Donation


@pytest.fixture
def user():
    return User.objects.create_user(
        username='test',
        password='Random?1',
        email='test@gmail.com',
        first_name='test',
        last_name='test'
    )


@pytest.fixture
def superusers():
    superusers = []
    for i in range(3):
        superuser = User.objects.create_user(
            username=f'test{i}',
            password='Random?1',
            email=f'test{i}@gmail.com',
            first_name='test',
            last_name='test',
            is_superuser=True,
            is_staff=True,
            is_active=True,
        )
        superusers.append(superuser)
    return superusers


@pytest.fixture
def categories():
    categories = []
    for i in range(10):
        category = Category.objects.create(name=f'category{i}')
        categories.append(category)
    return categories


@pytest.fixture
def institutions(categories):
    institutions = []
    for i in range(10):
        institution = Institution.objects.create(
            name=f'Institution {i}',
            type=Institution.FOUNDATION,
            description='Some description'
        )
        institution.categories.set(categories)
        institutions.append(institution)
    return institutions


@pytest.fixture
def donations(institutions, categories, user):
    donations = []
    for i in range(10):
        donation = Donation.objects.create(
            quantity=7,
            institution=institutions[i % len(institutions)],
            address=f'Street {i}',
            phone_number=f'123456789{i}',
            city='City',
            zip_code='12345',
            pick_up_date=date.today(),
            pick_up_time=time(hour=10, minute=0),
            pick_up_comment=f'Comment for Donation {i}',
            user=user,
            is_taken=False
        )
        donation.categories.set(categories)
        donations.append(donation)
    return donations


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.fixture
def activation_data(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return uid, token


@pytest.fixture
def activate_url(activation_data):
    uid, token = activation_data
    return reverse('ActivateAccount', kwargs={'uidb64': uid, 'token': token})
