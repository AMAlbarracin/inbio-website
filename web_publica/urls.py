from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'web_publica'

urlpatterns = [
    #Pagina Principal 
    path('', views.home_view, name='home'),
    
    #Seccion Instituto
    path('instituto/historia/', views.historia_view, name='historia'),
    path('instituto/mision-vision/', views.mision_vision_view, name='mision_vision'),
    
    #Seccion Equipo
    path('equipo/', views.equipo_lista_view, name='equipo'),
    path('equipo/<int:pk>/', views.investigador_detalle_view, name='investigador_detalle'),
   
    #Seccion Publicaciones
    path('publicaciones/', views.publicaciones_lista_view, name='publicaciones'),
    path('publicaciones/<int:pk>/', views.publicacion_detalle_view, name='publicacion_detalle'),
    
    #Seccion contacto
    path('contacto/', views.contacto_view, name='contacto'),
    
    #Seccion Noticias / Eventos 
    path('noticias/', views.noticias_lista_view, name='noticias'),
    path('noticias/<int:pk>/', views.noticia_detalle_view, name='noticia_detalle'),

    #Seccion Laboratorios
    path('laboratorios/', views.laboratorios_lista_view, name='laboratorios'),
    path('laboratorios/calendario/', views.reserva_calendario_view, name='reserva_calendario'),
    path('reserva-api/', views.reserva_api_view, name='reserva_api'),
    path('reserva-api/<int:pk>/', views.reserva_api_view, name='reserva_api_detail'),

    # SECCIÓN SERVICIOS PARA EMPRESAS
    path('servicios/', views.servicios_lista_view, name='servicios'),
    path('servicios/solicitud/', views.solicitud_servicio_view, name='solicitud_servicio'),
    
    #Seccion Proyectos 
    path('proyectos-investigacion/', views.proyectos_investigacion_view, name='proyectos_investigacion'),
    path('proyectos-colaborativos/', views.proyectos_colaborativos_view, name='proyectos_colaborativos'),

    # Seccion Login / Logout 
    path('login/', auth_views.LoginView.as_view(
        template_name='web_publica/auth/login.html',
        success_url='/dashboard/'
    ), name='login'),
    
    path('logout/', auth_views.LogoutView.as_view(
        next_page='/'
    ), name='logout'),
    
    # Dashboard para usuarios autenticados
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('estadisticas/', views.estadisticas_view, name='estadisticas'),
      
    #Seccion de Formularios para cargar datos
    path('noticias/cargar/', views.cargar_noticia_view, name='cargar_noticia'),
    path('publicaciones/cargar/', views.cargar_publicacion_view, name='cargar_publicacion'),
    path('laboratorios/cargar/', views.cargar_laboratorio_view, name='cargar_laboratorio'),
    path('servicios/cargar/', views.cargar_servicio_view, name='cargar_servicio'),
    path('eventos/cargar/', views.cargar_evento_view, name='cargar_evento'),
    path('cargar-investigador/', views.cargar_investigador_view, name='cargar_investigador'),
    path('cargar-proyecto/', views.cargar_proyecto_view, name='cargar_proyecto'),
    
    #CRUD de la seccion Privada 
    path('cargas-web/', views.cargas_web_view, name='cargas_web'),
    # FORMULARIOS DE EDICIÓN
    path('editar-noticia/<int:pk>/', views.editar_noticia_view, name='editar_noticia'),
    path('editar-publicacion/<int:pk>/', views.editar_publicacion_view, name='editar_publicacion'),
    path('editar-laboratorio/<int:pk>/', views.editar_laboratorio_view, name='editar_laboratorio'),
    path('editar-servicio/<int:pk>/', views.editar_servicio_view, name='editar_servicio'),
    path('editar-evento/<int:pk>/', views.editar_evento_view, name='editar_evento'),
    path('editar-investigador/<int:pk>/', views.editar_investigador_view, name='editar_investigador'),
    path('editar-proyecto/<int:pk>/', views.editar_proyecto_view, name='editar_proyecto'),
    
    # ELIMINACIÓN
    path('eliminar-noticia/<int:pk>/', views.eliminar_noticia_view, name='eliminar_noticia'),
    path('eliminar-publicacion/<int:pk>/', views.eliminar_publicacion_view, name='eliminar_publicacion'),
    path('eliminar-laboratorio/<int:pk>/', views.eliminar_laboratorio_view, name='eliminar_laboratorio'),
    path('eliminar-servicio/<int:pk>/', views.eliminar_servicio_view, name='eliminar_servicio'),
    path('eliminar-evento/<int:pk>/', views.eliminar_evento_view, name='eliminar_evento'),
    path('eliminar-investigador/<int:pk>/', views.eliminar_investigador_view, name='eliminar_investigador'),
    path('eliminar-proyecto/<int:pk>/', views.eliminar_proyecto_view, name='eliminar_proyecto'),
    
    
]

from rest_framework.routers import DefaultRouter
from .api_views import *

router = DefaultRouter()
router.register(r'api/publicaciones', PublicacionViewSet, basename='api-publicaciones')
router.register(r'api/investigadores', InvestigadorViewSet, basename='api-investigadores')
router.register(r'api/reservas', ReservaViewSet, basename='api-reservas')

# Añadir al final de urlpatterns
urlpatterns += router.urls