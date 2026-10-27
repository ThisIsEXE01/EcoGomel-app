from django.contrib import admin
from .models import WasteItem, DropoffPoint

@admin.register(WasteItem)
class WasteItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'recyclable')
    search_fields = ('name', 'code', 'category')
    list_filter = ('category', 'recyclable')

@admin.register(DropoffPoint)
class DropoffPointAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'working_hours')
    search_fields = ('name', 'address')