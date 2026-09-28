from django.urls import path

from .views import waste_list


urlpatterns = [
    path("waste/", waste_list),
]