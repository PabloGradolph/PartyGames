from django.urls import path
from . import views

app_name = 'blanco'

urlpatterns = [
    path('', views.index, name='index'),
    path('crear/', views.crear_partida, name='crear'),
    path('unirse/', views.unirse_partida, name='unirse'),
    path('partida/<str:codigo>/', views.partida, name='partida'),
]
