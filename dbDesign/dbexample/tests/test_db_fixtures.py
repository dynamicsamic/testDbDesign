import pytest
from dbexample import models

# @pytest.mark.dbfixture
# @pytest.mark.parametrize(
#    'id, name, slug, is_active',
#    [
#        (1, 'desktops', 'desktop', True),
#        (2, 'laptops', 'laptop', True),
#        (3, 'accessories', 'accessories', True),
#    ],
# )
# def test_product_category_fixture(
#    db, id, name, slug, is_active
# ):
#    pass


@pytest.mark.parametrize(
    "name, slug, is_active",
    [
        ("cat-1", "cat_1", True),
        ("cat-2", "cat_2", True),
        ("cat-3", "cat_3", True),
    ],
)
def test_product_db_category_insert_data(
    db, product_category_factory, name, slug, is_active
):
    result = product_category_factory.create(
        name=name, slug=slug, is_active=is_active
    )
    assert result.name == name
    assert result.slug == slug
    assert result.is_active == is_active


@pytest.mark.django_db
@pytest.mark.parametrize(
    "id, web_id, name, slug, description, is_active, created_at, updated_at",
    [
        (
            1,
            "44280",
            "Lenovo ThinkPad X12",
            "lenovo-thinkpad-x12",
            "Some generic laptop description",
            True,
            "2022-09-29 08:13:20",
            "2022-09-30 00:13:20",
        )
    ],
)
def test_product_db_product_set_dbfixture(
    db,
    # db_fixture_setup,
    id,
    web_id,
    name,
    slug,
    description,
    is_active,
    created_at,
    updated_at,
):
    #    result = models.ProductSet.objects.get(id=id)
    result = models.ProductSet.objects.create(
        id=id,
        web_id=web_id,
        name=name,
        slug=slug,
        description=description,
        is_active=is_active,
        created_at=created_at,
        updated_at=updated_at
    )
    assert result.web_id == web_id
