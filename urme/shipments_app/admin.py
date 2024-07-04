from django.contrib import admin
from shipments_app.models import CartProducts, Shipments, Transports


class TransportsInline(admin.TabularInline):
    model = Transports
    fields = ['transport_number', 'train_company', 'driver', 'change_ownership',
              'train_trailer', 'train_customer', 'unload_point']
    extra = 0


class CartProductsInline(admin.TabularInline):
    model = CartProducts
    fields = ['positions', 'product', 'bottling_date', 'quantity', 'price_for_one',
              'form1', 'form2_old', 'form2_new']
    extra = 0


@admin.register(Shipments)
class ShipmentsAdmin(admin.ModelAdmin):
    list_display = ['num', 'condition', 'date_creation', 'date_fixation', 'client']
    list_filter = ['condition', 'date_creation', 'client']
    inlines = [TransportsInline, CartProductsInline]
