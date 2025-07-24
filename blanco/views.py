from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import GameSession, GamePlayer, PalabraPar
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
import unicodedata
import re

# Create your views here.

def normalizar_texto(texto):
    """Normaliza texto: convierte a minúsculas y quita acentos"""
    # Convertir a minúsculas
    texto = texto.lower()
    # Normalizar unicode (quitar acentos)
    texto = unicodedata.normalize('NFD', texto)
    # Quitar caracteres diacríticos (acentos)
    texto = re.sub(r'[^\w\s]', '', texto)
    # Quitar espacios extra
    texto = texto.strip()
    return texto

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
            if partida.estado == 'en_juego':
                messages.error(request, 'No puedes unirte a una partida que ya está en juego.')
                return redirect('home')
        except GameSession.DoesNotExist:
            messages.error(request, 'No existe ninguna partida con ese código.')
            return redirect('home')
        return redirect('blanco:partida', codigo=partida.codigo)
    return render(request, 'blanco/unirse.html')

def asignar_roles_y_palabras(partida, palabra_buena, palabra_infiltrado):
    """Asigna roles y palabras a todos los jugadores de la partida"""
    players = list(partida.players.all())
    n = len(players)
    
    # Definir distribución de roles según número de jugadores
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
        return False, "Número de jugadores no soportado."
    
    random.shuffle(roles)
    
    for player, rol in zip(players, roles):
        player.eliminado = False
        player.es_impostor = False
        player.es_infiltrado = False
        player.es_bueno = False
        player.ya_intento_adivinar = False  # Resetear el intento de adivinación
        
        if rol == 'bueno':
            player.palabra_secreta = palabra_buena
            player.es_bueno = True
        elif rol == 'infiltrado':
            player.palabra_secreta = palabra_infiltrado
            player.es_infiltrado = True
        else:  # impostor
            player.palabra_secreta = "Tú no tienes palabra, eres el impostor."
            player.es_impostor = True
        
        player.ronda_actual = partida.ronda_actual
        player.save()
    
    return True, "Roles asignados correctamente."

def calcular_puntos_ronda(partida):
    """Calcula y asigna puntos según el resultado de la ronda"""
    jugadores_activos = [p for p in partida.players.all() if not p.eliminado]
    jugadores_eliminados = [p for p in partida.players.all() if p.eliminado]
    
    # Contar roles de los jugadores activos
    buenos_activos = [p for p in jugadores_activos if p.es_bueno]
    infiltrados_activos = [p for p in jugadores_activos if p.es_infiltrado]
    impostores_activos = [p for p in jugadores_activos if p.es_impostor]
    
    # Contar roles de los eliminados
    buenos_eliminados = [p for p in jugadores_eliminados if p.es_bueno]
    infiltrados_eliminados = [p for p in jugadores_eliminados if p.es_infiltrado]
    impostores_eliminados = [p for p in jugadores_eliminados if p.es_impostor]
    
    # Verificar si hay impostores eliminados que ya intentaron adivinar y fallaron
    impostores_que_fallaron = [p for p in impostores_eliminados if p.ya_intento_adivinar]
    
    # Lógica de puntos según el resultado
    if len(jugadores_activos) == 2:  # Llegaron a 1 vs 1
        # Si hay impostores que fallaron en adivinar, el infiltrado gana 2 puntos
        if len(impostores_que_fallaron) > 0 and len(infiltrados_activos) > 0:
            # Infiltrado gana 2 puntos cuando el impostor falla
            for player in infiltrados_activos:
                player.puntos += 2
                player.save()
            return f"Puntos asignados. El impostor falló en adivinar, el infiltrado gana 2 puntos."
        elif len(impostores_activos) > 0:  # Hay impostor en el final
            # Impostor gana 3 puntos
            for player in impostores_activos:
                player.puntos += 3
                player.save()
        elif len(infiltrados_activos) > 0:  # Hay infiltrado en el final
            # Infiltrado gana 2 puntos
            for player in infiltrados_activos:
                player.puntos += 2
                player.save()
        elif len(buenos_activos) > 0:  # Hay buenos en el final
            # Buenos ganan 1 punto cada uno
            for player in buenos_activos:
                player.puntos += 1
                player.save()
    else:  # No llegaron a 1 vs 1
        # Los buenos ganan si eliminaron a todos los infiltrados e impostores
        if len(infiltrados_activos) == 0 and len(impostores_activos) == 0:
            # Buenos ganan 1 punto cada uno
            for player in buenos_activos:
                player.puntos += 1
                player.save()
    
    return f"Puntos asignados. Buenos activos: {len(buenos_activos)}, Infiltrados activos: {len(infiltrados_activos)}, Impostores activos: {len(impostores_activos)}"

@login_required
def partida(request, codigo):
    partida = get_object_or_404(GameSession, codigo=codigo)
    
    # No permitir unirse si la partida está en juego
    if partida.estado == 'en_juego' and not GamePlayer.objects.filter(session=partida, user=request.user).exists():
        messages.error(request, 'No puedes unirte a una partida que ya está en juego.')
        return redirect('home')
    
    # Añadir usuario a la partida si no está
    gameplayer, created = GamePlayer.objects.get_or_create(session=partida, user=request.user)
    
    # Si es nuevo jugador, resetear su estado
    if created:
        gameplayer.eliminado = False
        gameplayer.es_impostor = False
        gameplayer.es_infiltrado = False
        gameplayer.es_bueno = False
        gameplayer.puntos = 0
        gameplayer.ronda_actual = partida.ronda_actual
        gameplayer.save()
    
    jugadores = partida.players.select_related('user').all()
    es_host = partida.host == request.user
    puede_empezar = es_host and partida.players.count() >= 4 and partida.estado != 'en_juego'
    mensaje = None
    
    # Obtener palabras aleatorias de la base de datos
    try:
        par_palabras = PalabraPar.objects.order_by('?').first()
        palabra_buena = par_palabras.palabra_buena if par_palabras else "Gato"
        palabra_infiltrado = par_palabras.palabra_infiltrado if par_palabras else "Perro"
    except:
        palabra_buena = "Gato"
        palabra_infiltrado = "Perro"
    
    if request.method == 'POST':
        # Expulsar jugador de la sala (solo antes del juego)
        if 'expulsar' in request.POST and es_host and partida.estado != 'en_juego':
            user_id = request.POST.get('expulsar')
            if user_id and str(request.user.id) != user_id:
                GamePlayer.objects.filter(session=partida, user_id=user_id).delete()
                mensaje = 'Jugador expulsado de la sala.'
        
        # Eliminar jugador de la ronda (durante el juego)
        elif 'eliminar_ronda' in request.POST and es_host and partida.estado == 'en_juego' and not partida.ronda_terminada:
            user_id = request.POST.get('eliminar_ronda')
            if user_id:
                player_to_eliminate = GamePlayer.objects.get(session=partida, user_id=user_id)
                player_to_eliminate.eliminado = True
                player_to_eliminate.save()
                
                # Determinar el rol del jugador eliminado para el mensaje
                rol_eliminado = ""
                if player_to_eliminate.es_impostor:
                    rol_eliminado = "impostor"
                elif player_to_eliminate.es_infiltrado:
                    rol_eliminado = "infiltrado"
                elif player_to_eliminate.es_bueno:
                    rol_eliminado = "bueno"
                
                mensaje = f'{player_to_eliminate.user.username} eliminado de la ronda. Era {rol_eliminado}.'
                
                # Verificar si llegamos a 1 vs 1 o si se acabó la ronda
                jugadores_activos = [p for p in partida.players.all() if not p.eliminado]
                
                # Verificar si se eliminaron todos los malos (infiltrados e impostores)
                infiltrados_activos = [p for p in jugadores_activos if p.es_infiltrado]
                impostores_activos = [p for p in jugadores_activos if p.es_impostor]
                
                # Verificar si hay impostores eliminados que pueden adivinar
                impostores_eliminados = [p for p in partida.players.all() if p.eliminado and p.es_impostor and not p.ya_intento_adivinar]
                
                if len(infiltrados_activos) == 0 and len(impostores_activos) == 0:
                    if len(impostores_eliminados) > 0:
                        # Hay impostores eliminados que pueden adivinar, no terminar la ronda aún
                        mensaje += f' Todos los malos han sido eliminados, pero hay impostores que pueden intentar adivinar la palabra.'
                    else:
                        # No hay impostores que puedan adivinar, los buenos ganan
                        buenos_activos = [p for p in jugadores_activos if p.es_bueno]
                        for player in buenos_activos:
                            player.puntos += 1
                            player.save()
                        partida.ronda_terminada = True
                        partida.save()
                        mensaje += f' ¡Los buenos han ganado! Todos los malos han sido eliminados. Los buenos activos ganan 1 punto cada uno.'
                elif len(jugadores_activos) == 2:
                    # Verificar si hay impostores eliminados que pueden adivinar
                    impostores_eliminados = [p for p in partida.players.all() if p.eliminado and p.es_impostor and not p.ya_intento_adivinar]
                    
                    if len(impostores_eliminados) > 0:
                        # Hay impostores eliminados que pueden adivinar, no terminar la ronda aún
                        mensaje += f' ¡Llegamos a 1 vs 1! Hay impostores eliminados que pueden intentar adivinar la palabra antes de asignar puntos.'
                    else:
                        # No hay impostores que puedan adivinar, calcular puntos y terminar ronda
                        puntos_msg = calcular_puntos_ronda(partida)
                        partida.ronda_terminada = True
                        partida.save()
                        mensaje += f' ¡Llegamos a 1 vs 1! {puntos_msg}'
                elif len(jugadores_activos) == 1:
                    # Solo queda uno, calcular puntos y terminar ronda
                    puntos_msg = calcular_puntos_ronda(partida)
                    partida.ronda_terminada = True
                    partida.save()
                    mensaje += f' ¡Solo queda un jugador! {puntos_msg}'
        
        # Terminar partida
        elif 'terminar' in request.POST and es_host:
            partida.delete()
            return redirect('home')
        
        # Empezar partida
        elif 'empezar_partida' in request.POST and puede_empezar:
            # Obtener nuevas palabras para la primera ronda
            try:
                par_palabras = PalabraPar.objects.order_by('?').first()
                palabra_buena = par_palabras.palabra_buena if par_palabras else "Gato"
                palabra_infiltrado = par_palabras.palabra_infiltrado if par_palabras else "Perro"
            except:
                palabra_buena = "Gato"
                palabra_infiltrado = "Perro"
            
            # Asignar roles y palabras
            success, msg = asignar_roles_y_palabras(partida, palabra_buena, palabra_infiltrado)
            if not success:
                mensaje = msg
                return render(request, 'blanco/partida.html', {
                    'partida': partida,
                    'jugadores': jugadores,
                    'es_host': es_host,
                    'puede_empezar': puede_empezar,
                    'mensaje': mensaje,
                })
            
            partida.estado = 'en_juego'
            partida.palabra_impostor = palabra_buena
            partida.palabra_buena_actual = palabra_buena
            partida.palabra_infiltrado_actual = palabra_infiltrado
            partida.ronda_terminada = False
            partida.ronda_actual = 1
            partida.save()
            mensaje = '¡La partida ha comenzado!'
        
        # Nueva ronda de palabras
        elif 'nueva_ronda' in request.POST and es_host and partida.ronda_terminada:
            # Obtener nuevas palabras
            try:
                par_palabras = PalabraPar.objects.order_by('?').first()
                palabra_buena = par_palabras.palabra_buena if par_palabras else "Gato"
                palabra_infiltrado = par_palabras.palabra_infiltrado if par_palabras else "Perro"
            except:
                palabra_buena = "Gato"
                palabra_infiltrado = "Perro"
            
            # Asignar roles y palabras
            success, msg = asignar_roles_y_palabras(partida, palabra_buena, palabra_infiltrado)
            if not success:
                mensaje = msg
                return render(request, 'blanco/partida.html', {
                    'partida': partida,
                    'jugadores': jugadores,
                    'es_host': es_host,
                    'puede_empezar': puede_empezar,
                    'mensaje': mensaje,
                })
            
            partida.palabra_impostor = palabra_buena
            partida.palabra_buena_actual = palabra_buena
            partida.palabra_infiltrado_actual = palabra_infiltrado
            partida.ronda_terminada = False
            partida.ronda_actual += 1
            partida.save()
            mensaje = f'¡Nueva ronda comenzada! (Ronda {partida.ronda_actual})'
        
        # Adivinar palabra (impostor eliminado)
        elif 'adivinar_palabra' in request.POST:
            mi_gameplayer = GamePlayer.objects.get(session=partida, user=request.user)
            
            # Verificar que sea impostor eliminado y que no haya intentado adivinar antes
            if not mi_gameplayer.es_impostor or not mi_gameplayer.eliminado or mi_gameplayer.ya_intento_adivinar:
                pass
            else:
                palabra_adivinada = request.POST.get('palabra_adivinada', '').strip()
                palabra_correcta = partida.palabra_impostor
                
                # Normalizar ambas palabras para comparación
                palabra_adivinada_norm = normalizar_texto(palabra_adivinada)
                palabra_correcta_norm = normalizar_texto(palabra_correcta)
                
                # Marcar que ya intentó adivinar
                mi_gameplayer.ya_intento_adivinar = True
                mi_gameplayer.save()
                
                if palabra_adivinada_norm == palabra_correcta_norm:
                    # Impostor gana 3 puntos
                    mi_gameplayer.puntos += 3
                    mi_gameplayer.save()
                    mensaje = '¡Correcto! El impostor ha ganado adivinando la palabra y se lleva 3 puntos.'
                    
                    # Verificar si hay otros impostores eliminados que puedan adivinar
                    otros_impostores_eliminados = [p for p in partida.players.all() if p.eliminado and p.es_impostor and not p.ya_intento_adivinar and p != mi_gameplayer]
                    
                    if len(otros_impostores_eliminados) == 0:
                        # No hay más impostores que puedan adivinar, terminar la ronda
                        partida.ronda_terminada = True
                        partida.save()
                        mensaje += ' La ronda ha terminado.'
                    else:
                        mensaje += ' Otros impostores eliminados aún pueden intentar adivinar.'
                else:
                    mensaje = f'Incorrecto. La palabra era "{partida.palabra_impostor}". El impostor ha perdido.'
                    
                    # Verificar si hay otros impostores eliminados que puedan adivinar
                    otros_impostores_eliminados = [p for p in partida.players.all() if p.eliminado and p.es_impostor and not p.ya_intento_adivinar and p != mi_gameplayer]
                    
                    if len(otros_impostores_eliminados) == 0:
                        # No hay más impostores que puedan adivinar, verificar si la ronda debe terminar
                        jugadores_activos = [p for p in partida.players.all() if not p.eliminado]
                        infiltrados_activos = [p for p in jugadores_activos if p.es_infiltrado]
                        impostores_activos = [p for p in jugadores_activos if p.es_impostor]
                        buenos_activos = [p for p in jugadores_activos if p.es_bueno]
                        
                        # La ronda solo termina si solo quedan buenos o si llegamos a 1 vs 1
                        if len(infiltrados_activos) == 0 and len(impostores_activos) == 0:
                            # Solo quedan buenos, ganan 1 punto cada uno
                            for player in buenos_activos:
                                player.puntos += 1
                                player.save()
                            partida.ronda_terminada = True
                            partida.save()
                            mensaje += ' ¡Los buenos han ganado! Todos los malos han sido eliminados. Los buenos activos ganan 1 punto cada uno. La ronda ha terminado.'
                        elif len(jugadores_activos) == 2:
                            # Llegamos a 1 vs 1, asignar puntos según quién esté en el final
                            if len(impostores_activos) > 0:
                                # Impostor en el 1 vs 1, gana 3 puntos
                                for player in impostores_activos:
                                    player.puntos += 3
                                    player.save()
                                mensaje += ' ¡Llegamos a 1 vs 1! El impostor gana 3 puntos.'
                            elif len(infiltrados_activos) > 0:
                                # Infiltrado en el 1 vs 1, gana 2 puntos
                                for player in infiltrados_activos:
                                    player.puntos += 2
                                    player.save()
                                mensaje += ' ¡Llegamos a 1 vs 1! El infiltrado gana 2 puntos.'
                            elif len(buenos_activos) == 2:
                                # Dos buenos en el 1 vs 1, cada uno gana 1 punto
                                for player in buenos_activos:
                                    player.puntos += 1
                                    player.save()
                                mensaje += ' ¡Llegamos a 1 vs 1! Dos buenos, cada uno gana 1 punto.'
                            
                            partida.ronda_terminada = True
                            partida.save()
                            mensaje += ' La ronda ha terminado.'
                        else:
                            # La ronda continúa normalmente
                            mensaje += ' La ronda continúa.'
    
    # Si no quedan jugadores, eliminar la partida
    if partida.players.count() == 0:
        partida.delete()
        return redirect('home')
    
    # Obtener información del jugador actual
    mi_gameplayer = GamePlayer.objects.get(session=partida, user=request.user)
    palabra = mi_gameplayer.palabra_secreta if partida.estado == 'en_juego' and not mi_gameplayer.eliminado else None
    
    # Contar jugadores activos en la ronda
    jugadores_activos = [gp for gp in jugadores if not gp.eliminado]
    jugadores_eliminados = [gp for gp in jugadores if gp.eliminado]
    
    # Contar roles para mostrar información (solo para el host o si la ronda terminó)
    buenos_activos = [p for p in jugadores_activos if p.es_bueno]
    infiltrados_activos = [p for p in jugadores_activos if p.es_infiltrado]
    impostores_activos = [p for p in jugadores_activos if p.es_impostor]
    
    return render(request, 'blanco/partida.html', {
        'partida': partida,
        'jugadores': jugadores,
        'jugadores_activos': jugadores_activos,
        'jugadores_eliminados': jugadores_eliminados,
        'buenos_activos': buenos_activos,
        'infiltrados_activos': infiltrados_activos,
        'impostores_activos': impostores_activos,
        'es_host': es_host,
        'puede_empezar': puede_empezar,
        'mensaje': mensaje,
        'palabra': palabra,
        'mi_gameplayer': mi_gameplayer,
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
