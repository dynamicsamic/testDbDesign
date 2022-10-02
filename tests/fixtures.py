import pytest
from django.core.management import call_command


@pytest.fixture
def create_super_user(django_user_model):
    return django_user_model.objects.create_superuser(
        "admin", "admin@hello.py", "password"
    )


@pytest.fixture(scope="session")
def db_fixture_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("loaddata", "prod-category_fixture.json")
