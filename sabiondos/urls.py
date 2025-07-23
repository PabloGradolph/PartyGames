from django.urls import path
from . import views

app_name = 'sabiondos'

urlpatterns = [
    path('', views.index, name='index'),
]
