from typing import Any, Optional

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> Optional[str]:
        call_command("makemigrations")
        call_command("migrate")
        call_command("loaddata", "user_db_fixture.json")
        call_command("loaddata", "customer_db_fixture.json")
        call_command("loaddata", "vendor_db_fixture.json")
        call_command("loaddata", "brand_db_fixture.json")
        call_command("loaddata", "prod_type_db_fixture.json")
        call_command("loaddata", "prod_category_fixture.json")
        call_command("loaddata", "prod_set_db_fixture.json")
        call_command("loaddata", "prod_attr_db_fixture.json")
        call_command("loaddata", "prod_attr_values_db_fixture.json")
        call_command("loaddata", "prod_item_db_fixture.json")
        call_command("loaddata", "stock_db_fixture.json")
