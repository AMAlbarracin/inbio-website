from django.contrib import admin
from .models import *
from django.utils.html import format_html

@admin.register(FechaImportante)
class FechaImportanteAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'titulo', 'destacado')
    list_filter = ('destacado',)
    search_fields = ('titulo', 'descripcion')
    date_hierarchy = 'fecha'

@admin.register(ValorInstitucional)
class ValorInstitucionalAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'titulo', 'icono', 'orden')
    list_filter = ('tipo',)
    list_editable = ('orden',)

@admin.register(Investigador)
class InvestigadorAdmin(admin.ModelAdmin):
    list_display = ('foto_thumbnail', 'nombre_completo', 'categoria', 'cargo', 'activo', 'orden')
    list_filter = ('categoria', 'activo', 'linea_investigacion')
    search_fields = ('nombre', 'apellido', 'email')
    list_editable = ('activo', 'orden')
    readonly_fields = ('nombre_completo',)
    
    def foto_thumbnail(self, obj):
        if obj.foto:
            return format_html('<img src="{}" width="40" style="border-radius:50%;"/>', obj.foto.url)
        return format_html('<i class="fas fa-user-circle fa-2x text-gray-400"></i>')
    foto_thumbnail.short_description = 'Foto'
    
@admin.register(Contacto)
class ContactoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'asunto', 'fecha_envio')
    search_fields = ('nombre', 'email', 'asunto')
    readonly_fields = ('fecha_envio',)
    
@admin.register(Publicacion)
class PublicacionAdmin(admin.ModelAdmin):
    list_display = ('titulo_corto', 'autores_corto', 'año', 'tipo', 'destacada')
    list_filter = ('año', 'tipo', 'destacada')
    search_fields = ('titulo', 'autores', 'revista')
    list_editable = ('destacada',)
    
    def titulo_corto(self, obj):
        return obj.titulo[:60] + "..."
    titulo_corto.short_description = 'Título'
    
    def autores_corto(self, obj):
        return obj.autores[:50] + "..."
    autores_corto.short_description = 'Autores'

# ✅ CORREGIDO: Eliminado EventoInline (ya no existe relación)

@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = ('titulo_corto', 'categoria', 'fecha_publicacion', 'destacada', 'activa')
    list_filter = ('categoria', 'activa', 'destacada')
    search_fields = ('titulo', 'resumen')
    list_editable = ('activa', 'destacada')
    # ✅ CORREGIDO: Eliminado inlines = [EventoInline]
    
    def titulo_corto(self, obj):
        return obj.titulo[:50] + "..."
    titulo_corto.short_description = 'Título'

# ✅ CORREGIDO: EventoAdmin con campos DEL MODELO INDEPENDIENTE
@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'fecha_evento', 'lugar', 'activo')  # ← 'titulo' en lugar de 'noticia'
    list_filter = ('fecha_evento', 'activo')  # ← 'activo' añadido
    search_fields = ('titulo', 'lugar')  # ← 'titulo' en lugar de 'noticia'
    list_editable = ('activo',)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(activo=True)

@admin.register(Laboratorio)
class LaboratorioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'capacidad', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'equipamiento')

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('laboratorio', 'investigador', 'fecha', 'hora_inicio', 'estado')
    list_filter = ('estado', 'fecha')
    search_fields = ('laboratorio__nombre', 'investigador__nombre')
    

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio_desde')
    search_fields = ('nombre', 'descripcion')

@admin.register(SolicitudServicio)
class SolicitudServicioAdmin(admin.ModelAdmin):
    list_display = ('empresa', 'servicio', 'estado', 'fecha_solicitud')
    list_filter = ('estado', 'servicio')
    search_fields = ('empresa', 'contacto', 'email')
    