from datetime import date, time

import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory

from charity_donations.models import Category, Institution, Donation


@pytest.fixture
def user():
    return User.objects.create_user(
        username='test user',
        password='test password',
        email='test@gmail.com',
        first_name='test',
        last_name='test'
    )


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
