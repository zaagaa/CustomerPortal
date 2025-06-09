from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.staff_profile, name='staff_profile'),
]
