import pytest

from dbexample import models

#@pytest.mark.dbfixture
#@pytest.mark.parametrize(
#    'id, name, slug, is_active',
#    [
#        (1, 'desktops', 'desktop', True),
#        (2, 'laptops', 'laptop', True),
#        (3, 'accessories', 'accessories', True),
#    ],
#)
#def test_product_category_fixture(
#    db, id, name, slug, is_active
#):
#    pass

@pytest.mark.parametrize(
    'name, slug, is_active',
    [
        ('desktops', 'desktop', True),
        ('laptops', 'laptop', True),
        ('accessories', 'accessories', True)
    ],
)
@pytest.mark.django_db
def test_product_db_category_insert_data(
    db, product_category_factory, name, slug, is_active
):
    result = product_category_factory.create(name=name, slug=slug, is_active=is_active)
    assert result.name == name
    assert result.slug == slug
    assert result.is_active == is_active

