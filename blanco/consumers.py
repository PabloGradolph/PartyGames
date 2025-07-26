import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.shortcuts import get_object_or_404


class PartidaConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.codigo = self.scope['url_route']['kwargs']['codigo']
        self.room_group_name = f'partida_{self.codigo}'
        
        # Verificar que la partida existe
        partida = await self.get_partida()
        if not partida:
            await self.close()
            return
        
        # Verificar que el usuario está autenticado
        if not self.scope['user'].is_authenticated:
            await self.close()
            return
        
        # Unirse al grupo de la partida
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Enviar datos actualizados de la partida a todos
        await self.send_partida_data()
        
        # Solo enviar mensaje de conexión si es un jugador nuevo
        # y no es una reconexión por recarga de página
        if await self.is_new_player() and await self.is_really_new_connection():
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'partida_message',
                    'message': {
                        'type': 'user_connected',
                        'username': self.scope['user'].username,
                    }
                }
            )

    async def disconnect(self, close_code):
        # Salir del grupo de la partida
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Solo enviar mensaje de desconexión si el usuario realmente se va de la partida
        # (no solo recarga la página o navega a otra página)
        if close_code != 1000 and close_code != 1001:  # 1000 = cierre normal, 1001 = navegación
            # Verificar si el usuario realmente se fue de la partida
            if await self.user_left_partida():
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'partida_message',
                        'message': {
                            'type': 'user_disconnected',
                            'username': self.scope['user'].username,
                        }
                    }
                )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        
        if message_type == 'refresh_request':
            await self.send_partida_data()
        elif message_type == 'eliminar_jugador':
            await self.handle_eliminar_jugador(text_data_json)
        elif message_type == 'nueva_ronda':
            await self.handle_nueva_ronda(text_data_json)
        elif message_type == 'iniciar_partida':
            await self.handle_iniciar_partida(text_data_json)
        elif message_type == 'terminar_partida':
            await self.handle_terminar_partida(text_data_json)
        elif message_type == 'expulsar_jugador':
            await self.handle_expulsar_jugador(text_data_json)
        elif message_type == 'adivinar_palabra':
            await self.handle_adivinar_palabra(text_data_json)

    async def partida_message(self, event):
        await self.send(text_data=json.dumps(event['message']))

    @database_sync_to_async
    def get_partida(self):
        from .models import GameSession
        try:
            return GameSession.objects.get(codigo=self.codigo)
        except GameSession.DoesNotExist:
            return None

    @database_sync_to_async
    def is_new_player(self):
        """Verifica si el usuario es un jugador nuevo en la partida"""
        from .models import GameSession, GamePlayer
        try:
            partida = GameSession.objects.get(codigo=self.codigo)
            # Verificar si el usuario ya está en la partida
            return not GamePlayer.objects.filter(
                session=partida, 
                user=self.scope['user']
            ).exists()
        except:
            return False

    @database_sync_to_async
    def is_host(self):
        """Verifica si el usuario es el host de la partida"""
        from .models import GameSession
        try:
            partida = GameSession.objects.get(codigo=self.codigo)
            return partida.host == self.scope['user']
        except:
            return False

    @database_sync_to_async
    def user_left_partida(self):
        """Verifica si el usuario realmente se fue de la partida (no solo recargó)"""
        from .models import GameSession, GamePlayer
        try:
            partida = GameSession.objects.get(codigo=self.codigo)
            # Si el usuario sigue siendo parte de la partida, no se fue realmente
            return not GamePlayer.objects.filter(
                session=partida,
                user=self.scope['user']
            ).exists()
        except GameSession.DoesNotExist:
            return True  # Si la partida no existe, asumir que se fue

    @database_sync_to_async
    def is_really_new_connection(self):
        """Verifica si es una conexión realmente nueva (no una reconexión por recarga)"""
        from .models import GameSession, GamePlayer
        try:
            partida = GameSession.objects.get(codigo=self.codigo)
            # Verificar si el usuario ya estaba en la partida antes
            existing_player = GamePlayer.objects.filter(
                session=partida,
                user=self.scope['user']
            ).first()
            
            # Si ya existe un jugador, es una reconexión (recarga de página)
            # Solo es nueva conexión si no existía antes
            return existing_player is None
        except GameSession.DoesNotExist:
            return False

    @database_sync_to_async
    def get_partida_data(self):
        """Obtiene todos los datos actualizados de la partida"""
        from .models import GameSession
        partida = get_object_or_404(GameSession, codigo=self.codigo)
        jugadores = partida.players.select_related('user').all()
        
        jugadores_data = []
        for jugador in jugadores:
            jugadores_data.append({
                'id': jugador.id,
                'user_id': jugador.user.id,
                'username': jugador.user.username,
                'puntos': jugador.puntos,
                'ronda_actual': jugador.ronda_actual,
                'eliminado': jugador.eliminado,
                'es_host': partida.host == jugador.user,
                'es_impostor': jugador.es_impostor,
                'es_infiltrado': jugador.es_infiltrado,
                'es_bueno': jugador.es_bueno,
                'palabra_secreta': jugador.palabra_secreta,
            })
        
        return {
            'estado': partida.estado,
            'ronda_actual': partida.ronda_actual,
            'ronda_terminada': partida.ronda_terminada,
            'jugadores': jugadores_data,
            'jugadores_activos': len([j for j in jugadores if not j.eliminado]),
            'jugadores_eliminados': len([j for j in jugadores if j.eliminado]),
            'palabra_buena_actual': partida.palabra_buena_actual,
            'palabra_infiltrado_actual': partida.palabra_infiltrado_actual,
        }

    async def send_partida_data(self):
        """Envía los datos actualizados de la partida a todos los clientes"""
        partida_data = await self.get_partida_data()
        user_id = self.scope['user'].id
        # Buscar la palabra secreta del usuario actual
        palabra_secreta = ''
        for jugador in partida_data['jugadores']:
            if jugador['user_id'] == user_id:
                palabra_secreta = jugador.get('palabra_secreta', '')
            # Eliminar la palabra secreta de todos los jugadores
            if 'palabra_secreta' in jugador:
                del jugador['palabra_secreta']
        partida_data['palabra_secreta'] = palabra_secreta

        # Enviar datos actualizados a todos los clientes del grupo
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'partida_message',
                'message': {
                    'type': 'partida_updated',
                    'data': partida_data,
                }
            }
        )

    @database_sync_to_async
    def eliminar_jugador_ronda(self, jugador_id):
        """Elimina un jugador de la ronda actual"""
        from .models import GamePlayer
        try:
            jugador = GamePlayer.objects.get(id=jugador_id)
            jugador.eliminado = True
            jugador.save()
            return True
        except GamePlayer.DoesNotExist:
            return False
        except Exception as e:
            return False

    @database_sync_to_async
    def verificar_fin_ronda(self):
        """Verifica si la ronda debe terminar y asigna puntos según corresponda"""
        from .models import GameSession, GamePlayer
        
        partida = get_object_or_404(GameSession, codigo=self.codigo)
        jugadores_activos = [p for p in partida.players.all() if not p.eliminado]
        
        # Contar roles de los jugadores activos
        buenos_activos = [p for p in jugadores_activos if p.es_bueno]
        infiltrados_activos = [p for p in jugadores_activos if p.es_infiltrado]
        impostores_activos = [p for p in jugadores_activos if p.es_impostor]
        
        # Verificar si hay impostores eliminados que pueden adivinar
        impostores_eliminados = [p for p in partida.players.all() if p.eliminado and p.es_impostor and not p.ya_intento_adivinar]
        
        # Caso 1: Todos los malos eliminados (infiltrados + impostores)
        if len(infiltrados_activos) == 0 and len(impostores_activos) == 0:
            if len(impostores_eliminados) > 0:
                # Hay impostores eliminados que pueden adivinar, no terminar la ronda aún
                return False
            else:
                # No hay impostores que puedan adivinar, los buenos ganan
                for player in buenos_activos:
                    player.puntos += 1
                    player.save()
                partida.ronda_terminada = True
                partida.save()
                return True
        
        # Caso 2: Llegamos a 1 vs 1
        elif len(jugadores_activos) == 2:
            if len(impostores_eliminados) > 0:
                # Hay impostores eliminados que pueden adivinar, no terminar la ronda aún
                return False
            else:
                # No hay impostores que puedan adivinar, calcular puntos y terminar ronda
                self.calcular_puntos_1vs1(partida, jugadores_activos)
                partida.ronda_terminada = True
                partida.save()
                return True
        
        # Caso 3: Solo queda 1 jugador (esto no debería pasar, pero por seguridad)
        elif len(jugadores_activos) == 1:
            if len(impostores_eliminados) > 0:
                # Hay impostores eliminados que pueden adivinar, no terminar la ronda aún
                return False
            else:
                # No hay impostores que puedan adivinar, terminar la ronda
                partida.ronda_terminada = True
                partida.save()
                return True
        
        # La ronda continúa
        return False

    def calcular_puntos_1vs1(self, partida, jugadores_activos):
        """Calcula puntos para el caso 1 vs 1"""
        buenos_activos = [p for p in jugadores_activos if p.es_bueno]
        infiltrados_activos = [p for p in jugadores_activos if p.es_infiltrado]
        impostores_activos = [p for p in jugadores_activos if p.es_impostor]
        
        # 2 buenos: 1 punto cada uno
        if len(buenos_activos) == 2:
            for player in buenos_activos:
                player.puntos += 1
                player.save()
        
        # 1 bueno y 1 infiltrado: 2 puntos infiltrado
        elif len(buenos_activos) == 1 and len(infiltrados_activos) == 1:
            for player in infiltrados_activos:
                player.puntos += 2
                player.save()
        
        # 1 bueno y 1 impostor: 3 puntos impostor
        elif len(buenos_activos) == 1 and len(impostores_activos) == 1:
            for player in impostores_activos:
                player.puntos += 3
                player.save()
        
        # 1 infiltrado y 1 impostor: 3 puntos impostor, 2 puntos infiltrado
        elif len(infiltrados_activos) == 1 and len(impostores_activos) == 1:
            for player in impostores_activos:
                player.puntos += 3
                player.save()
            for player in infiltrados_activos:
                player.puntos += 2
                player.save()
        
        # 2 impostores: 3 puntos cada uno
        elif len(impostores_activos) == 2:
            for player in impostores_activos:
                player.puntos += 3
                player.save()
        
        # 2 infiltrados: 2 puntos cada uno
        elif len(infiltrados_activos) == 2:
            for player in infiltrados_activos:
                player.puntos += 2
                player.save()

    async def handle_eliminar_jugador(self, data):
        """Maneja la eliminación de un jugador"""
        jugador_id = data.get('jugador_id')
        
        if jugador_id and await self.is_host():
            success = await self.eliminar_jugador_ronda(jugador_id)
            
            if success:
                # Enviar datos actualizados a todos los clientes inmediatamente
                await self.send_partida_data()
                
                # Verificar si la ronda debe terminar (después de enviar los datos actualizados)
                ronda_terminada = await self.verificar_fin_ronda()
                
                # Si la ronda terminó, enviar notificación especial
                if ronda_terminada:
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'partida_message',
                            'message': {
                                'type': 'ronda_terminada',
                                'message': 'La ronda ha terminado. El host puede iniciar una nueva ronda.',
                            }
                        }
                    )


    @database_sync_to_async
    def iniciar_nueva_ronda(self):
        """Inicia una nueva ronda"""
        from .models import GameSession, PalabraPar
        import random
        
        partida = get_object_or_404(GameSession, codigo=self.codigo)
        
        # Obtener nuevas palabras aleatorias, evitando las últimas usadas
        ultimas_palabras = []
        if partida.palabra_buena_actual:
            ultimas_palabras.append(partida.palabra_buena_actual)
        if partida.palabra_infiltrado_actual:
            ultimas_palabras.append(partida.palabra_infiltrado_actual)
        
        if ultimas_palabras:
            par_palabras = PalabraPar.objects.exclude(
                palabra_buena__in=ultimas_palabras
            ).exclude(
                palabra_infiltrado__in=ultimas_palabras
            ).order_by('?').first()
        else:
            par_palabras = PalabraPar.objects.order_by('?').first()
        
        if par_palabras:
            palabra_buena = par_palabras.palabra_buena
            palabra_infiltrado = par_palabras.palabra_infiltrado
        else:
            palabra_buena = "CASA"
            palabra_infiltrado = "HOGAR"
        
        # Actualizar palabras de la partida
        partida.palabra_buena_actual = palabra_buena
        partida.palabra_infiltrado_actual = palabra_infiltrado
        partida.palabra_impostor = palabra_buena
        partida.ronda_actual += 1
        partida.ronda_terminada = False
        partida.save()
        
        # Asignar roles y palabras a los jugadores
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
            return False
        
        random.shuffle(roles)
        
        for player, rol in zip(players, roles):
            player.eliminado = False
            player.es_impostor = False
            player.es_infiltrado = False
            player.es_bueno = False
            player.ya_intento_adivinar = False
            
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
        
        return True

    async def handle_nueva_ronda(self, data):
        """Maneja el inicio de una nueva ronda"""
        success = await self.iniciar_nueva_ronda()
        if success:
            # Enviar notificación de nueva ronda a todos
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'partida_message',
                    'message': {
                        'type': 'nueva_ronda_iniciada',
                        'message': '¡Nueva ronda iniciada! Los roles han sido reasignados.',
                    }
                }
            )

    @database_sync_to_async
    def iniciar_partida(self):
        """Inicia la partida"""
        from .models import GameSession, PalabraPar
        import random
        
        partida = get_object_or_404(GameSession, codigo=self.codigo)
        
        # Verificar que hay suficientes jugadores
        jugadores = list(partida.players.all())
        if len(jugadores) < 4:
            return False
        
        # Obtener una palabra aleatoria, evitando las últimas usadas
        ultimas_palabras = []
        if partida.palabra_buena_actual:
            ultimas_palabras.append(partida.palabra_buena_actual)
        if partida.palabra_infiltrado_actual:
            ultimas_palabras.append(partida.palabra_infiltrado_actual)
        
        if ultimas_palabras:
            palabras_disponibles = list(PalabraPar.objects.exclude(
                palabra_buena__in=ultimas_palabras
            ).exclude(
                palabra_infiltrado__in=ultimas_palabras
            ))
        else:
            palabras_disponibles = list(PalabraPar.objects.all())
            
        if not palabras_disponibles:
            # Si no hay palabras en la base de datos, usar palabras por defecto
            palabra_buena = "CASA"
            palabra_infiltrado = "HOGAR"
        else:
            palabra_par = random.choice(palabras_disponibles)
            palabra_buena = palabra_par.palabra_buena
            palabra_infiltrado = palabra_par.palabra_infiltrado
        
        # Asignar palabras a la partida
        partida.palabra_buena_actual = palabra_buena
        partida.palabra_infiltrado_actual = palabra_infiltrado
        partida.palabra_impostor = palabra_buena  # El impostor debe adivinar la palabra buena
        
        # Cambiar estado de la partida
        partida.estado = 'en_juego'
        partida.ronda_actual = 1
        partida.ronda_terminada = False
        partida.save()
        
        # Asignar roles y palabras aleatorios
        random.shuffle(jugadores)
        
        if len(jugadores) == 4:
            # 3 buenos, 1 infiltrado
            for i, jugador in enumerate(jugadores):
                if i < 3:
                    jugador.es_bueno = True
                    jugador.es_infiltrado = False
                    jugador.es_impostor = False
                    jugador.palabra_secreta = palabra_buena
                else:
                    jugador.es_bueno = False
                    jugador.es_infiltrado = True
                    jugador.es_impostor = False
                    jugador.palabra_secreta = palabra_infiltrado
                jugador.save()
        
        elif len(jugadores) == 5:
            # 3 buenos, 1 infiltrado, 1 impostor
            for i, jugador in enumerate(jugadores):
                if i < 3:
                    jugador.es_bueno = True
                    jugador.es_infiltrado = False
                    jugador.es_impostor = False
                    jugador.palabra_secreta = palabra_buena
                elif i == 3:
                    jugador.es_bueno = False
                    jugador.es_infiltrado = True
                    jugador.es_impostor = False
                    jugador.palabra_secreta = palabra_infiltrado
                else:
                    jugador.es_bueno = False
                    jugador.es_infiltrado = False
                    jugador.es_impostor = True
                    jugador.palabra_secreta = "¡Impostor! No tienes palabra en esta ronda."
                jugador.save()
        
        elif len(jugadores) >= 6:
            # Para 6+: 4+ buenos, 1+ infiltrados, 1+ impostores
            num_buenos = max(4, len(jugadores) - 3)
            num_infiltrados = max(1, (len(jugadores) - num_buenos) // 2)
            num_impostores = len(jugadores) - num_buenos - num_infiltrados
            
            for i, jugador in enumerate(jugadores):
                if i < num_buenos:
                    jugador.es_bueno = True
                    jugador.es_infiltrado = False
                    jugador.es_impostor = False
                    jugador.palabra_secreta = palabra_buena
                elif i < num_buenos + num_infiltrados:
                    jugador.es_bueno = False
                    jugador.es_infiltrado = True
                    jugador.es_impostor = False
                    jugador.palabra_secreta = palabra_infiltrado
                else:
                    jugador.es_bueno = False
                    jugador.es_infiltrado = False
                    jugador.es_impostor = True
                    jugador.palabra_secreta = "¡Impostor! No tienes palabra en esta ronda."
                jugador.save()
        
        return True

    async def handle_iniciar_partida(self, data):
        """Maneja el inicio de la partida"""
        success = await self.iniciar_partida()
        if success:
            # Enviar notificación de inicio de partida a todos
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'partida_message',
                    'message': {
                        'type': 'partida_iniciada',
                        'message': '¡La partida ha comenzado! Los roles han sido asignados.',
                    }
                }
            )
        else:
            # Enviar error si no se puede iniciar
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'No se puede iniciar la partida. Se necesitan al menos 4 jugadores.'
            }))

    @database_sync_to_async
    def terminar_partida(self):
        """Termina la partida"""
        from .models import GameSession
        partida = get_object_or_404(GameSession, codigo=self.codigo)
        partida.estado = 'terminada'
        partida.save()
        return True

    async def handle_terminar_partida(self, data):
        """Maneja la terminación de la partida"""
        if await self.is_host():
            success = await self.terminar_partida()
            if success:
                # Enviar notificación de partida terminada a todos
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'partida_message',
                        'message': {
                            'type': 'partida_terminada',
                            'message': 'La partida ha sido terminada por el host.',
                        }
                    }
                )

    @database_sync_to_async
    def expulsar_jugador(self, user_id):
        """Expulsa un jugador de la partida"""
        from .models import GamePlayer
        try:
            jugador = GamePlayer.objects.get(
                session__codigo=self.codigo,
                user_id=user_id
            )
            jugador.delete()
            return True
        except GamePlayer.DoesNotExist:
            return False

    async def handle_expulsar_jugador(self, data):
        """Maneja la expulsión de un jugador"""
        user_id = data.get('user_id')
        if user_id and await self.is_host():
            success = await self.expulsar_jugador(user_id)
            if success:
                await self.send_partida_data()
                # Enviar notificación de expulsión
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'partida_message',
                        'message': {
                            'type': 'jugador_expulsado',
                            'user_id': user_id,
                        }
                    }
                )

    async def handle_adivinar_palabra(self, data):
        """Maneja la adivinación de palabra por un impostor eliminado"""
        palabra_adivinada = data.get('palabra_adivinada', '').strip()
        
        if palabra_adivinada:
            resultado = await self.procesar_adivinacion(palabra_adivinada)
            
            # Enviar resultado de la adivinación
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'partida_message',
                    'message': {
                        'type': 'adivinacion_resultado',
                        'resultado': resultado,
                    }
                }
            )
            
            # Enviar datos actualizados inmediatamente después de la adivinación
            await self.send_partida_data()
            
            # Si la ronda terminó, enviar notificación
            if resultado.get('ronda_terminada'):
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'partida_message',
                        'message': {
                            'type': 'ronda_terminada',
                            'message': 'La ronda ha terminado. El host puede iniciar una nueva ronda.',
                        }
                    }
                )

    @database_sync_to_async
    def procesar_adivinacion(self, palabra_adivinada):
        """Procesa la adivinación de palabra por un impostor eliminado"""
        from .models import GameSession, GamePlayer
        
        partida = get_object_or_404(GameSession, codigo=self.codigo)
        mi_gameplayer = GamePlayer.objects.get(session=partida, user=self.scope['user'])
        
        # Verificar que sea impostor eliminado y que no haya intentado adivinar antes
        if not mi_gameplayer.es_impostor or not mi_gameplayer.eliminado or mi_gameplayer.ya_intento_adivinar:
            return {'error': 'No puedes adivinar la palabra'}
        
        palabra_correcta = partida.palabra_impostor
        
        # Normalizar ambas palabras para comparación
        palabra_adivinada_norm = palabra_adivinada.lower().strip()
        palabra_correcta_norm = palabra_correcta.lower().strip()
        
        # Marcar que ya intentó adivinar
        mi_gameplayer.ya_intento_adivinar = True
        mi_gameplayer.save()
        
        if palabra_adivinada_norm == palabra_correcta_norm:
            # Impostor gana 3 puntos
            mi_gameplayer.puntos += 3
            mi_gameplayer.save()
            
            # Verificar si hay otros impostores eliminados que puedan adivinar
            otros_impostores_eliminados = [p for p in partida.players.all() if p.eliminado and p.es_impostor and not p.ya_intento_adivinar and p != mi_gameplayer]
            
            if len(otros_impostores_eliminados) == 0:
                # No hay más impostores que puedan adivinar, terminar la ronda
                partida.ronda_terminada = True
                partida.save()
                return {
                    'correcto': True,
                    'mensaje': '¡Correcto! El impostor ha ganado adivinando la palabra y se lleva 3 puntos. La ronda ha terminado.',
                    'ronda_terminada': True
                }
            else:
                return {
                    'correcto': True,
                    'mensaje': '¡Correcto! El impostor ha ganado adivinando la palabra y se lleva 3 puntos. Otros impostores eliminados aún pueden intentar adivinar.',
                    'ronda_terminada': False
                }
        else:
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
                    return {
                        'correcto': False,
                        'mensaje': f'Incorrecto. La palabra era "{partida.palabra_impostor}". ¡Los buenos han ganado! Todos los malos han sido eliminados. Los buenos activos ganan 1 punto cada uno. La ronda ha terminado.',
                        'ronda_terminada': True
                    }
                elif len(jugadores_activos) == 2:
                    # Llegamos a 1 vs 1, asignar puntos según la combinación
                    self.calcular_puntos_1vs1(partida, jugadores_activos)
                    partida.ronda_terminada = True
                    partida.save()
                    return {
                        'correcto': False,
                        'mensaje': f'Incorrecto. La palabra era "{partida.palabra_impostor}". ¡Llegamos a 1 vs 1! La ronda ha terminado.',
                        'ronda_terminada': True
                    }
                elif len(jugadores_activos) == 1:
                    # Solo queda 1 jugador (no debería pasar, pero por seguridad)
                    partida.ronda_terminada = True
                    partida.save()
                    return {
                        'correcto': False,
                        'mensaje': f'Incorrecto. La palabra era "{partida.palabra_impostor}". Solo queda 1 jugador. La ronda ha terminado.',
                        'ronda_terminada': True
                    }
                else:
                    # La ronda continúa normalmente
                    return {
                        'correcto': False,
                        'mensaje': f'Incorrecto. La palabra era "{partida.palabra_impostor}". La ronda continúa.',
                        'ronda_terminada': False
                    }
            else:
                # La ronda continúa normalmente
                return {
                    'correcto': False,
                    'mensaje': f'Incorrecto. La palabra era "{partida.palabra_impostor}". Otros impostores eliminados aún pueden intentar adivinar.',
                    'ronda_terminada': False
                }