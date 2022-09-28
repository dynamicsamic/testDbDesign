from django.db import models
from django.utils.translation import gettext_lazy as _


class ProductCategory(models.Model):
    name = models.CharField(
        _('product category name'),
        max_length=100,
        unique=True,
        help_text=_('required, max_len: 100'),
    )
    slug = models.SlugField(
        _('product category url'),
        max_length=150,
        unique=True,
        help_text=_('required, [letters, numbers, hyphens, underscore], max_len: 150'),
    )
    is_active = models.BooleanField(
        _('product category active status'),
        default=True,
        help_text=_('optional, defalut: True')
    )

    def __str__(self):
        return self.name

