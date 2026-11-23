from django.urls import path
from .views import points_list, points_suggest, waste_detail, waste_list

urlpatterns = [
    path("waste/", waste_list, name="waste-list"),
    path("waste/<int:pk>/", waste_detail, name="waste-detail"),
    path("points/", points_list, name="points-list"),
    path("points/suggest/", points_suggest, name="points-suggest"),
]