from django.contrib import admin
from .models import GameSession, GamePlayer, PalabraPar

# Register your models here.

@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'estado', 'host', 'creado', 'ronda_actual', 'ronda_terminada')
    list_filter = ('estado', 'ronda_actual', 'ronda_terminada', 'creado')
    search_fields = ('codigo', 'host__username')
    readonly_fields = ('codigo', 'creado')
    ordering = ('-creado',)
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'estado', 'host', 'creado')
        }),
        ('Estado del Juego', {
            'fields': ('ronda_actual', 'ronda_terminada')
        }),
        ('Palabras de la Ronda', {
            'fields': ('palabra_impostor', 'palabra_buena_actual', 'palabra_infiltrado_actual'),
            'classes': ('collapse',)
        }),
    )

@admin.register(GamePlayer)
class GamePlayerAdmin(admin.ModelAdmin):
    list_display = ('user', 'session', 'puntos', 'ronda_actual', 'eliminado', 'es_impostor', 'es_infiltrado', 'es_bueno')
    list_filter = ('eliminado', 'es_impostor', 'es_infiltrado', 'es_bueno', 'ronda_actual', 'session__estado')
    search_fields = ('user__username', 'session__codigo')
    readonly_fields = ('joined',)
    ordering = ('-joined',)
    
    fieldsets = (
        ('Información del Jugador', {
            'fields': ('user', 'session', 'joined', 'puntos')
        }),
        ('Estado en la Ronda', {
            'fields': ('ronda_actual', 'eliminado', 'ya_intento_adivinar')
        }),
        ('Roles', {
            'fields': ('es_impostor', 'es_infiltrado', 'es_bueno'),
            'classes': ('collapse',)
        }),
        ('Palabra Secreta', {
            'fields': ('palabra_secreta',),
            'classes': ('collapse',)
        }),
    )

@admin.register(PalabraPar)
class PalabraParAdmin(admin.ModelAdmin):
    list_display = ('palabra_buena', 'palabra_infiltrado', 'categoria')
    list_filter = ('categoria',)
    search_fields = ('palabra_buena', 'palabra_infiltrado', 'categoria')
    ordering = ('categoria', 'palabra_buena')
    
    fieldsets = (
        ('Palabras', {
            'fields': ('palabra_buena', 'palabra_infiltrado')
        }),
        ('Categorización', {
            'fields': ('categoria',)
        }),
    )
