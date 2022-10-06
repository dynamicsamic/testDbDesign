from typing import Any, Optional

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> Optional[str]:
        call_command("makemigrations")
        call_command("migrate")
        call_command("loaddata", "suppliers.json")
        call_command("loaddata", "brands.json")
        call_command("loaddata", "prod_type.json")
        call_command("loaddata", "prod-category_fixture.json")
        call_command("loaddata", "small_prod_set.json")
        call_command("loaddata", "prod_attrs.json")
        call_command("loaddata", "prod_attrs_values.json")
        call_command("loaddata", "product_item_fixture.json")
        # call_command("loaddata", "prod_attr_link_table.json")
        # call_command("loaddata", "productset_db_fixture.json")
