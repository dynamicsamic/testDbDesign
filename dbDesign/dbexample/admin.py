from django.contrib import admin

from .models import ProductCategory

@admin.register(ProductCategory)
class AdminProductCategory(admin.ModelAdmin):
    pass

