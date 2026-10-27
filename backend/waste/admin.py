from django.contrib import admin
from .models import WasteItem, DropoffPoint


@admin.register(WasteItem)
class WasteItemAdmin(admin.ModelAdmin):
    # 1. Отображение колонок в таблице списка отходов
    list_display = ('name', 'code', 'recyclable')

    # 2. Поля, по которым работает строка поиска в админке
    search_fields = ('name', 'code', 'category')

    # 3. Фильтры справа для быстрой сортировки записей
    list_filter = ('category', 'recyclable')


@admin.register(DropoffPoint)
class DropoffPointAdmin(admin.ModelAdmin):
    # 1. Отображение колонок для точек сбора (название, адрес, график работы)
    list_display = ('name', 'address', 'working_hours')

    # 2. Поиск точек сбора по названию и адресу
    search_fields = ('name', 'address')