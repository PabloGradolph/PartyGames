from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import GameSession, GamePlayer
import secrets
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .forms import CustomUserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import logout as auth_logout
from django.views.decorators.http import require_POST
import random
from django.contrib import messages

# Create your views here.

@login_required
def index(request):
    return HttpResponse('<h2>Pantalla principal del juego Blanco</h2>')

@login_required
def crear_partida(request):
    codigo = secrets.token_urlsafe(4)[:6].upper()
    partida = GameSession.objects.create(codigo=codigo, host=request.user)
    GamePlayer.objects.create(session=partida, user=request.user)
    return render(request, 'blanco/partida_creada.html', {'codigo': codigo})

@login_required
def unirse_partida(request):
    if request.method == 'POST':
        codigo = request.POST['codigo'].upper()
        try:
            partida = GameSession.objects.get(codigo=codigo)
        except GameSession.DoesNotExist:
            messages.error(request, 'No existe ninguna partida con ese código.')
            return redirect('home')
        return redirect('blanco:partida', codigo=partida.codigo)
    return render(request, 'blanco/unirse.html')

@login_required
def partida(request, codigo):
    partida = get_object_or_404(GameSession, codigo=codigo)
    # No permitir unirse si la partida está en juego
    if partida.estado == 'en_juego' and not GamePlayer.objects.filter(session=partida, user=request.user).exists():
        return redirect('home')
    # Añadir usuario a la partida si no está
    GamePlayer.objects.get_or_create(session=partida, user=request.user)
    jugadores = [gp.user for gp in partida.players.select_related('user').all()]
    es_host = partida.host == request.user
    puede_empezar = es_host and partida.players.count() >= 4
    mensaje = None
    # Palabras de prueba para la ronda
    palabra_buena = "Gato"
    palabra_infiltrado = "Perro"
    palabra_impostor = "Tú no tienes palabra, eres el impostor."
    # Eliminar jugador
    if request.method == 'POST':
        if 'expulsar' in request.POST and es_host and partida.estado != 'en_juego':
            user_id = request.POST.get('expulsar')
            if user_id and str(request.user.id) != user_id:
                GamePlayer.objects.filter(session=partida, user_id=user_id).delete()
                mensaje = 'Jugador expulsado.'
        elif 'terminar' in request.POST and es_host:
            partida.delete()
            return redirect('home')
        elif puede_empezar and partida.estado != 'en_juego':
            # Asignar roles y palabras (empezar partida)
            players = list(partida.players.select_related('user').all())
            n = len(players)
            roles = []
            if n == 4:
                roles = ['bueno']*3 + ['infiltrado']
            elif n == 5:
                roles = ['bueno']*3 + ['infiltrado'] + ['impostor']
            elif n == 6:
                roles = ['bueno']*4 + ['infiltrado'] + ['impostor']
            elif n == 7:
                roles = ['bueno']*4 + ['infiltrado']*2 + ['impostor']
            elif n == 8:
                roles = ['bueno']*5 + ['infiltrado']*2 + ['impostor']
            elif n == 9:
                roles = ['bueno']*5 + ['infiltrado']*2 + ['impostor']*2
            else:
                mensaje = 'Número de jugadores no soportado.'
                return render(request, 'blanco/partida.html', {
                    'partida': partida,
                    'jugadores': jugadores,
                    'es_host': es_host,
                    'puede_empezar': puede_empezar,
                    'mensaje': mensaje,
                })
            random.shuffle(roles)
            for player, rol in zip(players, roles):
                if rol == 'bueno':
                    player.palabra_secreta = palabra_buena
                elif rol == 'infiltrado':
                    player.palabra_secreta = palabra_infiltrado
                else:
                    player.palabra_secreta = palabra_impostor
                player.save()
            partida.estado = 'en_juego'
            partida.save()
        elif 'nuevas_palabras' in request.POST and es_host and partida.estado == 'en_juego':
            # Reasignar roles y palabras (nueva ronda)
            players = list(partida.players.select_related('user').all())
            n = len(players)
            roles = []
            if n == 4:
                roles = ['bueno']*3 + ['infiltrado']
            elif n == 5:
                roles = ['bueno']*3 + ['infiltrado'] + ['impostor']
            elif n == 6:
                roles = ['bueno']*4 + ['infiltrado'] + ['impostor']
            elif n == 7:
                roles = ['bueno']*4 + ['infiltrado']*2 + ['impostor']
            elif n == 8:
                roles = ['bueno']*5 + ['infiltrado']*2 + ['impostor']
            elif n == 9:
                roles = ['bueno']*5 + ['infiltrado']*2 + ['impostor']*2
            else:
                mensaje = 'Número de jugadores no soportado.'
                return render(request, 'blanco/partida.html', {
                    'partida': partida,
                    'jugadores': jugadores,
                    'es_host': es_host,
                    'puede_empezar': puede_empezar,
                    'mensaje': mensaje,
                })
            random.shuffle(roles)
            for player, rol in zip(players, roles):
                if rol == 'bueno':
                    player.palabra_secreta = palabra_buena
                elif rol == 'infiltrado':
                    player.palabra_secreta = palabra_infiltrado
                else:
                    player.palabra_secreta = palabra_impostor
                player.save()
    # Si no quedan jugadores, eliminar la partida
    if partida.players.count() == 0:
        partida.delete()
        return redirect('home')
    # Mostrar palabra secreta solo si la partida está en juego
    mi_gameplayer = GamePlayer.objects.get(session=partida, user=request.user)
    palabra = mi_gameplayer.palabra_secreta if partida.estado == 'en_juego' else None
    return render(request, 'blanco/partida.html', {
        'partida': partida,
        'jugadores': jugadores,
        'es_host': es_host,
        'puede_empezar': puede_empezar,
        'mensaje': mensaje,
        'palabra': palabra,
    })

# Vista personalizada de logout para limpiar GamePlayer
@login_required
def logout_view(request):
    GamePlayer.objects.filter(user=request.user).delete()
    # Eliminar partidas sin jugadores
    for partida in GameSession.objects.all():
        if partida.players.count() == 0:
            partida.delete()
    auth_logout(request)
    return redirect('login')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})
