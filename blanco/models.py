from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class GameSession(models.Model):
    codigo = models.CharField(max_length=8, unique=True)
    creado = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, default='esperando')
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_sessions', null=True, blank=True)

    def __str__(self):
        return f"Partida {self.codigo}"

class GamePlayer(models.Model):
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='players')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    joined = models.DateTimeField(auto_now_add=True)
    palabra_secreta = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ('session', 'user')

    def __str__(self):
        return f"{self.user.username} en {self.session.codigo}"
