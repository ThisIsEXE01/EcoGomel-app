from django.contrib import admin
from .models import WasteItem, DropoffPoint


@admin.register(WasteItem)
class WasteItemAdmin(admin.ModelAdmin):
    # 1. Отображение колонок: название, код маркировки, перерабатываемость
    list_display = ('name', 'code', 'recyclable')

    # 3. Поиск по названию и фильтрация по категориям/перерабатываемости
    search_fields = ('name',)
    list_filter = ('category', 'recyclable')


@admin.register(DropoffPoint)
class DropoffPointAdmin(admin.ModelAdmin):
    # 2. Отображение колонок: название, адрес, режим работы
    list_display = ('name', 'address', 'working_hours')

    # 3. Поиск по названию
    search_fields = ('name',)