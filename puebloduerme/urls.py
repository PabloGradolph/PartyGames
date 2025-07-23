from django.urls import path
from . import views

app_name = 'puebloduerme'

urlpatterns = [
    path('', views.index, name='index'),
]
