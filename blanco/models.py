from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class GameSession(models.Model):
    codigo = models.CharField(max_length=8, unique=True)
    creado = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, default='esperando')  # esperando, en_juego, terminada
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_sessions', null=True, blank=True)
    palabra_impostor = models.CharField(max_length=100, blank=True, null=True)  # Palabra que debe adivinar el impostor
    ronda_terminada = models.BooleanField(default=False)  # Si la ronda actual ha terminado
    ronda_actual = models.IntegerField(default=1)  # Número de ronda actual (1, 2, 3...)
    palabra_buena_actual = models.CharField(max_length=100, blank=True, null=True)
    palabra_infiltrado_actual = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Partida {self.codigo}"

class GamePlayer(models.Model):
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='players')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    joined = models.DateTimeField(auto_now_add=True)
    palabra_secreta = models.CharField(max_length=100, blank=True, null=True)
    eliminado = models.BooleanField(default=False)  # Si está eliminado de la ronda actual
    es_impostor = models.BooleanField(default=False)  # Si es el impostor en esta ronda
    es_infiltrado = models.BooleanField(default=False)  # Si es infiltrado en esta ronda
    es_bueno = models.BooleanField(default=False)  # Si es bueno en esta ronda
    puntos = models.IntegerField(default=0)  # Puntos totales del jugador
    ronda_actual = models.IntegerField(default=1)  # Ronda en la que está el jugador
    ya_intento_adivinar = models.BooleanField(default=False)  # Si el impostor ya intentó adivinar en esta ronda

    class Meta:
        unique_together = ('session', 'user')

    def __str__(self):
        return f"{self.user.username} en {self.session.codigo}"

class PalabraPar(models.Model):
    palabra_buena = models.CharField(max_length=100)
    palabra_infiltrado = models.CharField(max_length=100)
    categoria = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return f"{self.palabra_buena} - {self.palabra_infiltrado}"
