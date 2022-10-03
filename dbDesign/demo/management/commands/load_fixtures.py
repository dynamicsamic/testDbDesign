from typing import Any, Optional

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> Optional[str]:
        call_command("makemigrations")
        call_command("migrate")
        call_command("loaddata", "prod-category_fixture.json")
        call_command("loaddata", "productset_db_fixture.json")
