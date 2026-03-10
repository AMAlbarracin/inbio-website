from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.contrib import messages
from .models import *
from .forms import ContactoForm, NoticiaForm, PublicacionForm, LaboratorioForm, ServicioForm, EventoForm, InvestigadorForm, ProyectoForm, ComentarioNoticiaForm, LaboratorioImagenForm, EquipamientoFormset
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from django.shortcuts import render
from django.db.models import Count
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from web_publica.utils import enviar_notificacion_reserva
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError

from django.utils import timezone
from datetime import datetime
from django.utils.text import slugify
from django.conf import settings
import re
import requests
import feedparser
from scholarly import scholarly

def home_view(request):
    """
    Vista de página principal con datos dinámicos y contadores reales
    """
    
    # ===== CONTADORES DINÁMICOS =====
    contadores = {
        'proyectos': Proyecto.objects.filter(activo=True).count(),
        'publicaciones': Publicacion.objects.count(),
        'investigadores': Investigador.objects.filter(activo=True).count(),
        # Años de antigüedad: calcula automáticamente desde 2010
        'anios_trayectoria': datetime.now().year - 2010,
    }
    
    # ===== MOMENTOS CLAVE =====
    # Últimos 5 momentos destacados (ordenados por fecha más reciente)
    fechas_destacadas = FechaImportante.objects.filter(destacado=True).order_by('-fecha')[:5]
    
    # ===== AUTORIDADES =====
    # Director y Subdirector (máximo 2 personas)
    miembros_directiva = Investigador.objects.filter(
        categoria__in=['DIRECTOR', 'SUBDIRECTOR'],
        activo=True
    ).order_by('orden')[:2]  # "orden" permite poner primero al Director
    
    # ===== ÚLTIMAS NOTICIAS =====
    # Las 5 noticias más recientes (destacadas o no, pero activas)
    # Usamos order_by('-fecha_noticia') para asegurar el orden cronológico
    noticias_ultimas = Noticia.objects.filter(
        activa=True,        
    ).order_by('-fecha_noticia')[:5]
    
    # Para el contador de noticias activas (opcional)
    contadores['noticias_activas'] = Noticia.objects.filter(activa=True).count()
    
    context = {
        'fechas_destacadas': fechas_destacadas,
        'miembros_directiva': miembros_directiva,
        'noticias_ultimas': noticias_ultimas,
        'contadores': contadores,
    }
    
    return render(request, 'web_publica/home.html', context)


def historia_view(request):
    """Timeline interactivo de historia"""
    context = {
        'fechas': FechaImportante.objects.all(),
        'titulo_seccion': 'Nuestra Historia'
    }
    return render(request, 'web_publica/instituto/historia.html', context)

def mision_vision_view(request):
    """Misión, Visión, Valores y Objetivos"""
    context = {
        'mision': ValorInstitucional.objects.filter(tipo='MISION').first(),
        'vision': ValorInstitucional.objects.filter(tipo='VISION').first(),
        'valores': ValorInstitucional.objects.filter(tipo='VALOR'),
        'objetivos': ValorInstitucional.objects.filter(tipo='OBJETIVO'),
    }
    return render(request, 'web_publica/instituto/mision_vision.html', context)

from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.http import JsonResponse

def equipo_lista_view(request):
    categoria = request.GET.get('categoria')
    busqueda = request.GET.get('busqueda', "").strip()

    # Consulta base
    miembros = Investigador.objects.filter(activo=True)

    # Campo concatenado para búsquedas
    miembros = miembros.annotate(
        nombre_completo_busqueda=Concat('nombre', Value(' '), 'apellido')
    )

    # Filtro por categoría
    if categoria:
        miembros = miembros.filter(categoria=categoria)

    # Filtro general (nombre, apellido, nombre completo, título, línea)
    if busqueda:
        miembros = miembros.filter(
            Q(nombre__icontains=busqueda) |
            Q(apellido__icontains=busqueda) |
            Q(nombre_completo_busqueda__icontains=busqueda) |
            Q(titulo_Academico__icontains=busqueda) |
            Q(linea_investigacion__icontains=busqueda)
        )

    context = {
        'miembros': miembros,
        'categorias': Investigador.CATEGORIA_CHOICES,
        'categoria_actual': categoria,
        'busqueda': busqueda,
        'es_admin': request.user.is_authenticated and (
            request.user.is_staff or 
            request.user.groups.filter(name='Coordinadores').exists()
        )
    }

    return render(request, 'web_publica/equipo/lista_investigadores.html', context)



def investigador_detalle_view(request, id):
    investigador = get_object_or_404(Investigador, id=id)
    
    # --- Laboratorios asociados ---
    laboratorios_a_cargo = investigador.laboratorios_a_cargo.all()
    laboratorios_integrantes = investigador.laboratorios_participantes.all()

    # --- 1) PUBLICACIONES LOCALES ---
    publicaciones_locales = []
    for p in investigador.publicaciones.all():
        publicaciones_locales.append({
            "titulo": p.titulo,
            "autores": p.autores_completos(),
            "revista": p.revista,
            "año": str(p.año) if p.año else None,
            "link": p.link or p.doi or "",
            "fuente": p.fuente,
        })

    # --- 2) IMPORTAR ORCID ---
    if investigador.orcid_id:
        sincronizar_publicaciones(investigador)

    # --- 3) IMPORTAR GOOGLE SCHOLAR ---
    if investigador.google_scholar:
        sincronizar_publicaciones_scholar(investigador)

    # --- 4) RECARGAR desde BD ---
    # Después de sincronizar, recargamos las publicaciones vinculadas
    publicaciones_db = investigador.publicaciones.all()

    publicaciones_finales = []
    titulos_vistos = set()

    for p in publicaciones_db:
        tnorm = p.titulo.strip().lower()
        if tnorm in titulos_vistos:
            continue
        titulos_vistos.add(tnorm)

        publicaciones_finales.append({
            "titulo": p.titulo,
            "autores": p.autores_completos(),
            "revista": p.revista,
            "año": p.año,
            "link": p.link or (f"https://doi.org/{p.doi}" if p.doi else ""),
            "fuente": p.fuente,
        })

    # Orden descendente por año
    publicaciones_finales = sorted(
        publicaciones_finales,
        key=lambda x: x.get("año") or 0,
        reverse=True
    )

    context = {
        'laboratorios_a_cargo': laboratorios_a_cargo,
        'laboratorios_integrantes': laboratorios_integrantes,
        "investigador": investigador,
        "publicaciones": publicaciones_finales,
    }
    return render(request, "web_publica/equipo/detalle_investigador.html", context)


    
from .utils import fetch_scholar_pubs


def contacto_view(request):
    """Formulario de contacto funcional"""
    if request.method == 'POST':
        form = ContactoForm(request.POST)
        if form.is_valid():
            # Guardar en BD
            contacto = form.save()
            # Enviar email (configurar SMTP)
            send_mail(
                subject=f"Contacto Web: {contacto.asunto}",
                message=contacto.mensaje,
                from_email=contacto.email,
                recipient_list=['contacto@instituto.edu'],  # Cambiar
                fail_silently=False,
            )
            messages.success(request, 'Mensaje enviado correctamente')
            return redirect('web_publica:contacto')
    else:
        form = ContactoForm()
    
    context = {'form': form}
    return render(request, 'web_publica/contacto.html', context)

#def publicaciones_lista_view(request):
    """Listado de publicaciones con filtros"""
    tipo = request.GET.get('tipo')
    año = request.GET.get('año')
    
    publicaciones = Publicacion.objects.all()
    
    if tipo:
        publicaciones = publicaciones.filter(tipo=tipo)
    if año:
        publicaciones = publicaciones.filter(año=año)
    
    # Obtener años disponibles para el filtro
    años = Publicacion.objects.values_list('año', flat=True).distinct().order_by('-año')
    
    context = {
        'publicaciones': publicaciones,
        'tipos': Publicacion.TIPO_CHOICES,
        'años': años,
        'tipo_actual': tipo,
        'año_actual': año,
    }
    return render(request, 'web_publica/publicaciones/lista.html', context)

from django.shortcuts import render
from django.db.models import Count, Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from .models import Publicacion

def publicaciones_lista_view(request):
    """
    Vista completa para listado de publicaciones con filtros por autor
    """
    # 1. CAPTURAR PARÁMETROS DE LA URL
    tipo = request.GET.get('tipo', '').strip()
    año = request.GET.get('año', '').strip()
    query = request.GET.get('q', '').strip()
    orden = request.GET.get('orden', 'año_desc')
    page = request.GET.get('page', 1)
    
    # ⭐ NUEVO: Capturar múltiples autores seleccionados
    autores_seleccionados_ids = request.GET.getlist('autores')  # Lista de IDs

    # 2. EMPEZAR CON TODAS LAS PUBLICACIONES
    publicaciones = Publicacion.objects.all()

    # 3. APLICAR FILTROS
    if tipo and tipo in [t[0] for t in Publicacion.TIPO_CHOICES]:
        publicaciones = publicaciones.filter(tipo=tipo)
    
    if año and año.isdigit():
        publicaciones = publicaciones.filter(año=int(año))
    
    # ⭐ NUEVO: Filtrar por autores seleccionados
    if autores_seleccionados_ids:
        publicaciones = publicaciones.filter(
            autores_investigadores__id__in=autores_seleccionados_ids
        ).distinct()  # Importante: evita duplicados cuando hay múltiples autores
    
    if query:
        publicaciones = publicaciones.filter(
            Q(titulo__icontains=query) |
            Q(autores_externos__icontains=query) |
            Q(revista__icontains=query) |
            Q(doi__icontains=query)
        )

    # 4. ORDENAR
    orden_opciones = {
        'año_desc': '-año',
        'año_asc': 'año',
        'tipo': 'tipo',
        'destacadas': '-destacada',
    }
    publicaciones = publicaciones.order_by(orden_opciones.get(orden, '-año'))

    # 5. PAGINACIÓN
    paginator = Paginator(publicaciones, 20)
    try:
        page_obj = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    # 6. ESTADÍSTICAS PARA GRÁFICOS
    current_year = timezone.now().year
    años_rango = range(current_year - 7, current_year + 1)
    
    por_año = []
    for a in años_rango:
        count = Publicacion.objects.filter(año=a).count()
        if count > 0:
            por_año.append({'año': a, 'count': count})
    
    por_tipo = Publicacion.objects.values('tipo').annotate(count=Count('id')).order_by('-count')

    # ⭐ NUEVO: Obtener todos los investigadores activos para los checkboxes
    # Con número de publicaciones para mostrar contexto
    investigadores = Investigador.objects.filter(
        activo=True,
        publicaciones__isnull=False  # Solo investigadores con publicaciones
    ).annotate(
        num_publicaciones=Count('publicaciones')
    ).order_by('apellido', 'nombre')
    
    # 7. PREPARAR DATOS PARA EL TEMPLATE
    datos_graficos = {
        'por_año': {
            'labels': [item['año'] for item in por_año],
            'data': [item['count'] for item in por_año]
        },
        'por_tipo': {
            'labels': [Publicacion.TIPO_CHOICES_DICT[item['tipo']] for item in por_tipo],
            'data': [item['count'] for item in por_tipo]
        }
    }

    # 8. CONTEXT
    context = {
        'publicaciones': page_obj,
        'tipos': Publicacion.TIPO_CHOICES,
        'años_disponibles': Publicacion.objects.values_list('año', flat=True).distinct().order_by('-año'),
        'tipo_actual': tipo,
        'año_actual': año,
        'orden_actual': orden,
        'query': query,
        'total_publicaciones': paginator.count,
        'datos_graficos': datos_graficos,
        'page_obj': page_obj,
        'is_paginated': paginator.num_pages > 1,
        # ⭐ NUEVOS PARÁMETROS
        'investigadores': investigadores,
        'autores_seleccionados_ids': [int(id) for id in autores_seleccionados_ids],  # Lista de IDs numéricos
    }
    
    return render(request, 'web_publica/publicaciones/lista.html', context)


def publicacion_detalle_view(request, pk):
    """Detalle de una publicación específica"""
    publicacion = get_object_or_404(Publicacion, pk=pk)
    context = {'publicacion': publicacion}
    return render(request, 'web_publica/publicaciones/detalles.html', context)


def noticias_lista_view(request):
    """Listado de noticias y eventos"""
    categoria = request.GET.get('categoria')
    noticias = Noticia.objects.filter(activa=True)
    
    if categoria:
        noticias = noticias.filter(categoria=categoria)
    
    # Últimas 3 noticias destacadas para home
    destacadas = noticias.filter(destacada=True)[:3]
    
    context = {
        'noticias': noticias[:20],  # Últimas 20
        'destacadas': destacadas,
        'categorias': Noticia.CATEGORIA_CHOICES,
        'categoria_actual': categoria,
    }
    return render(request, 'web_publica/noticias/lista.html', context)

def noticia_detalle_view(request, pk):
    noticia = get_object_or_404(Noticia, pk=pk, activa=True)
    
    # ✅ DEBUGGING: Ver todos los comentarios
    print("=== DEBUG COMENTARIOS ===")
    print(f"Noticia ID: {noticia.pk}")
    print(f"Total comentarios: {noticia.comentarios.count()}")
    print(f"Comentarios aprobados: {noticia.comentarios.filter(aprobado=True).count()}")
    for c in noticia.comentarios.all():
        print(f"- {c.nombre}: {c.contenido[:50]}... (aprobado: {c.aprobado})")
    print("=========================")
    
    comentarios = noticia.comentarios.filter(aprobado=True)
    # 🔥 Cargar imágenes adicionales
    imagenes_extra = noticia.imagenes.all()

    # 🔥 Detectar si la noticia tiene galería
    videos_extra = noticia.videos_extra.all()
    
    if request.method == 'POST':
        form = ComentarioNoticiaForm(request.POST)
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.noticia = noticia
            
            comentario.aprobado = True  # Para pruebas, en producción debería ser False
            
            comentario.save()
            messages.success(request, 'Comentario enviado. Se publicará tras moderación.')
            return redirect('web_publica:noticia_detalle', pk=noticia.pk)
    else:
        form = ComentarioNoticiaForm()
    
    return render(request, 'web_publica/noticias/detalle.html', {
        'noticia': noticia,
        'form_comentario': form,
        'comentarios': comentarios,
        'imagenes_extra': imagenes_extra,
        'videos_extra': videos_extra,
        
    })

def laboratorios_lista_view(request):
    """Listado de laboratorios disponibles"""
    laboratorios = Laboratorio.objects.filter(activo=True).order_by('nombre')
    return render(request, 'web_publica/laboratorios/lista.html', {'laboratorios': laboratorios})

def laboratorio_detalle_view(request, pk):
    laboratorio = get_object_or_404(Laboratorio, pk=pk)

    # Galería de imágenes adicionales (si existen)
    imagenes = LaboratorioImagen.objects.filter(laboratorio=laboratorio).order_by('-id')

    # Reservas próximas (solo aprobadas)
    reservas = Reserva.objects.filter(
        laboratorio=laboratorio,
        estado="APROBADA",
        fecha__gte=timezone.now().date()
    ).order_by('fecha', 'hora_inicio')[:5]

    context = {
        "laboratorio": laboratorio,
        "imagenes": imagenes,
        "reservas": reservas
    }

    return render(request, "web_publica/laboratorios/detalle.html", context)


@login_required
def reserva_calendario_view(request):
    """Calendario interactivo de reservas"""
    # Nota: Requiere sistema de autenticación
    reservas = Reserva.objects.filter(estado='APROBADA')
    return render(request, 'web_publica/laboratorios/calendario.html', {'reservas': reservas})

def servicios_lista_view(request):
    """Catálogo de servicios para empresas"""
    servicios = Servicio.objects.all()
    return render(request, 'web_publica/empresas/servicios.html', {'servicios': servicios})

def solicitud_servicio_view(request):
    """Formulario de solicitud de servicio"""
    if request.method == 'POST':
        # Lógica del formulario
        pass
    return render(request, 'web_publica/empresas/solicitud.html')



@login_required
def dashboard_view(request):
    """Panel de control para investigadores"""
    reservas = Reserva.objects.filter(investigador__email=request.user.email).order_by('-fecha', '-hora_inicio')
    
    context = {
        'reservas_activas': reservas.filter(estado='APROBADA')[:5],
        'publicaciones_count': Publicacion.objects.count(),
        'reservas_count': reservas.count(),
    }
    return render(request, 'web_publica/auth/dashboard.html', context)



def reserva_calendario_view(request):
    """Página con calendario interactivo"""
    if request.user.is_authenticated:
        return render(request, 'web_publica/laboratorios/calendario.html')
    return redirect('web_publica:login')

@csrf_exempt  # Temporal, luego usaremos tokens
def reserva_api_view(request):
    """API para crear/eliminar reservas desde el calendario"""
    if request.method == 'GET':
        # Devolver eventos para FullCalendar
        reservas = Reserva.objects.filter(estado='APROBADA')
        events = []
        for reserva in reservas:
            events.append({
                'id': reserva.id,
                'title': f"Reservado: {reserva.laboratorio.nombre}",
                'start': f"{reserva.fecha}T{reserva.hora_inicio}",
                'end': f"{reserva.fecha}T{reserva.hora_fin}",
                'color': '#64ffda',
            })
        return JsonResponse(events, safe=False)
    
    elif request.method == 'POST' and request.user.is_authenticated:
        # Crear nueva reserva
        data = json.loads(request.body)
        try:
            laboratorio = Laboratorio.objects.get(id=data['laboratorio_id'])
            investigador = Investigador.objects.get(email=request.user.email)
            
            reserva = Reserva.objects.create(
                laboratorio=laboratorio,
                investigador=investigador,
                fecha=data['fecha'],
                hora_inicio=data['hora_inicio'],
                hora_fin=data['hora_fin'],
                descripcion=data.get('descripcion', ''),
                estado='PENDIENTE'  # Requiere aprobación admin
            )
            
            # Notificación por email (FASE 4)
            send_mail(
                'Nueva reserva pendiente',
                f'El investigador {investigador} solicitó reserva del {laboratorio}',
                'noreply@instituto.edu',
                ['admin@instituto.edu']
            )
            
            return JsonResponse({'status': 'ok', 'id': reserva.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        
@login_required
def estadisticas_view(request):
    """Dashboard con gráficos estadísticos"""
    # Datos para gráficos
    publicaciones_por_año = Publicacion.objects.values('año').annotate(total=Count('id')).order_by('año')
    reservas_por_mes = Reserva.objects.values('fecha__month').annotate(total=Count('id'))
    
    context = {
        'publicaciones_por_año': publicaciones_por_año,
        'reservas_por_mes': reservas_por_mes,
        'total_investigadores': Investigador.objects.filter(activo=True).count(),
        'total_publicaciones': Publicacion.objects.count(),
        'total_laboratorios': Laboratorio.objects.filter(activo=True).count(),
    }
    return render(request, 'web_publica/estadisticas/dashboard.html', context)



def es_administrador_o_coordinador(user):
    """Permiso para personal administrativo"""
    return user.is_authenticated and (user.is_staff or user.groups.filter(name='Coordinadores').exists())


@login_required
@user_passes_test(es_administrador_o_coordinador)
def cargar_noticia_view(request):
    if request.method == 'POST':
        form = NoticiaForm(request.POST, request.FILES)
        if form.is_valid():
            noticia = form.save()
            
            # Imágenes adicionales
            for img in request.FILES.getlist('imagenes_adicionales'):
                NoticiaImagen.objects.create(noticia=noticia, imagen=img)

            # Videos adicionales
            for video in request.FILES.getlist('videos_adicionales'):
                NoticiaVideo.objects.create(noticia=noticia, video=video)
            
            messages.success(request, 'Noticia publicada exitosamente')
            return redirect('web_publica:noticia_detalle', pk=noticia.pk)
    else:
        form = NoticiaForm()
    
    return render(request, 'web_publica/forms/cargar_noticia.html', {'form': form})

# Agregar al modelo Noticia (models.py)
class NoticiaQuerySet(models.QuerySet):
    def aprobadas(self):
        return self.filter(aprobado=True)  # Para los comentarios

ComentarioNoticia.add_to_class('objects', NoticiaQuerySet.as_manager())


@login_required
@user_passes_test(es_administrador_o_coordinador)
def cargar_publicacion_view(request):
    """Formulario frontend para cargar publicaciones manualmente"""
    if request.method == 'POST':
        form = PublicacionForm(request.POST)
        if form.is_valid():
            publicacion = form.save()
            messages.success(request, f'Publicación "{publicacion.titulo}" creada exitosamente')
            return redirect('web_publica:publicaciones')
    else:
        form = PublicacionForm()
    
    context = {
        'form': form,
        'titulo': 'Cargar Nueva Publicación'
    }
    return render(request, 'web_publica/forms/cargar_publicacion.html', context)

@login_required
@user_passes_test(es_administrador_o_coordinador)
@login_required
@user_passes_test(es_administrador_o_coordinador)
def cargar_laboratorio_view(request):

    if request.method == "POST":
        form = LaboratorioForm(request.POST, request.FILES)
        formset = EquipamientoFormset(request.POST, request.FILES)

        if form.is_valid() and formset.is_valid():
            laboratorio = form.save()

            # Guardar equipamientos
            equipamientos = formset.save(commit=False)
            for eq in equipamientos:
                eq.laboratorio = laboratorio
                eq.save()

            messages.success(request, f'Laboratorio "{laboratorio.nombre}" creado exitosamente')
            return redirect("web_publica:laboratorios")

    else:
        form = LaboratorioForm()
        formset = EquipamientoFormset()

    context = {
        "form": form,
        "formset": formset,
        "titulo": "Cargar Laboratorio"
    }
    return render(request, "web_publica/forms/cargar_laboratorio.html", context)

@login_required
@user_passes_test(es_administrador_o_coordinador)
def agregar_imagenes_laboratorio_view(request, pk):
    laboratorio = get_object_or_404(Laboratorio, pk=pk)

    if request.method == 'POST':
        print("FILES RECIBIDOS:", request.FILES)   # ← DEPURACIÓN
       
        form = LaboratorioImagenForm(request.POST, request.FILES)

        # Lista de imágenes enviadas
        imagenes = request.FILES.getlist('imagen')
        print("LISTA IMAGENES:", imagenes)  # ← DEPURACIÓN

        if form.is_valid():
            for img in imagenes:
                LaboratorioImagen.objects.create(
                    laboratorio=laboratorio,
                    imagen=img
                )
            messages.success(request, "Imágenes cargadas correctamente.")
            return redirect('web_publica:laboratorio_detalle', pk=laboratorio.pk)

    else:
        form = LaboratorioImagenForm()

    return render(request, 'web_publica/laboratorios/agregar_imagenes.html', {
        'form': form,
        'laboratorio': laboratorio,
    })


@login_required
@user_passes_test(es_administrador_o_coordinador)
def cargar_servicio_view(request):
    """Formulario frontend para cargar servicios empresariales"""
    if request.method == 'POST':
        form = ServicioForm(request.POST, request.FILES)
        if form.is_valid():
            servicio = form.save()
            messages.success(request, f'Servicio "{servicio.nombre}" creado exitosamente')
            return redirect('web_publica:servicios')
    else:
        form = ServicioForm()
    
    context = {'form': form, 'titulo': 'Cargar Servicio'}
    return render(request, 'web_publica/forms/cargar_servicio.html', context)



@login_required
@user_passes_test(es_administrador_o_coordinador)
def cargar_evento_view(request):
    """Formulario frontend para cargar eventos"""
    if request.method == 'POST':
        form = EventoForm(request.POST, request.FILES)
        if form.is_valid():
            evento = form.save()
            messages.success(request, f'Evento "{evento.titulo}" creado exitosamente')
            return redirect('web_publica:noticias')
    else:
        form = EventoForm()
    
    context = {'form': form, 'titulo': 'Cargar Evento'}
    return render(request, 'web_publica/forms/cargar_evento.html', context)



@login_required
@user_passes_test(es_administrador_o_coordinador)
def cargar_investigador_view(request):
    """Formulario frontend para cargar investigadores"""
    if request.method == 'POST':
        form = InvestigadorForm(request.POST, request.FILES)
        if form.is_valid():
            investigador = form.save()
            messages.success(request, f'Investigador {investigador.nombre_completo} creado exitosamente')
            return redirect('web_publica:equipo')
    else:
        form = InvestigadorForm()
    
    context = {
        'form': form,
        'titulo': 'Cargar Nuevo Investigador'
    }
    return render(request, 'web_publica/forms/cargar_investigador.html', context)

# Vista para cargar proyectos (internos y colaborativos)
@login_required
@user_passes_test(es_administrador_o_coordinador)
def cargar_proyecto_view(request):
    if request.method == 'POST':
        form = ProyectoForm(request.POST)
        if form.is_valid():
            proyecto = form.save()
            tipo = "Colaborativo" if proyecto.tipo == 'colaborativo' else "Investigación"
            messages.success(request, f'Proyecto {tipo} "{proyecto.titulo}" creado exitosamente')
            return redirect('web_publica:proyectos_investigacion')
    else:
        form = ProyectoForm()
    
    context = {
        'form': form,
        'titulo': 'Cargar Nuevo Proyecto'
    }
    return render(request, 'web_publica/forms/cargar_proyectos.html', context)

# Vista pública para mostrar proyectos de investigación
def proyectos_investigacion_view(request):
    proyectos = Proyecto.objects.filter(tipo='interno', activo=True).order_by('-fecha_inicio')
    return render(request, 'web_publica/proyectos/investigacion.html', {'proyectos': proyectos})

# Vista pública para mostrar proyectos colaborativos
def proyectos_colaborativos_view(request):
    proyectos = Proyecto.objects.filter(tipo='colaborativo', activo=True).order_by('-fecha_inicio')
    return render(request, 'web_publica/proyectos/colaborativos.html', {'proyectos': proyectos})


from django.db.models import Count, Q
from django.core.paginator import Paginator

@login_required
@user_passes_test(es_administrador_o_coordinador)
def cargas_web_view(request):
    """Panel de control centralizado para gestionar TODAS las entidades"""
    
    query = request.GET.get('q', '').strip()
    
    # ===== 2. DEBUG (temporal para verificar, puedes quitarlo después) =====
    if query:
        print(f"\n{'='*50}")
        print(f"🔍 BÚSQUEDA ACTIVA: '{query}'")
        print(f"URL: {request.get_full_path()}")
        print(f"{'='*50}\n")
    # =======================================================================
    
    
    # Dashboard de contadores
    contadores = {
        'noticias': Noticia.objects.count(),
        'noticias_activas': Noticia.objects.filter(activa=True).count(),
        'publicaciones': Publicacion.objects.count(),
        'investigadores': Investigador.objects.filter(activo=True).count(),
        'laboratorios': Laboratorio.objects.filter(activo=True).count(),
        'servicios': Servicio.objects.count(),
        'eventos': Evento.objects.filter(activo=True).count(),
        'proyectos': Proyecto.objects.filter(activo=True).count(),
    }
    
    # Querysets con paginación
    page_number = request.GET.get('page', 1)
    
    noticias_qs = Noticia.objects.all().order_by('-fecha_publicacion')
    noticias = Paginator(noticias_qs, 5).get_page(page_number)
    
    publicaciones_qs = Publicacion.objects.all().order_by('-año', '-id')
    publicaciones = Paginator(publicaciones_qs, 5).get_page(page_number)
    
    investigadores_qs = Investigador.objects.filter(activo=True).order_by('orden', 'apellido')
    investigadores = Paginator(investigadores_qs, 5).get_page(page_number)
    
    laboratorios_qs = Laboratorio.objects.filter(activo=True).order_by('nombre')
    laboratorios = Paginator(laboratorios_qs, 5).get_page(page_number)
    
    servicios_qs = Servicio.objects.all().order_by('nombre')
    servicios = Paginator(servicios_qs, 5).get_page(page_number)
    
    eventos_qs = Evento.objects.filter(activo=True).order_by('-fecha_evento')
    eventos = Paginator(eventos_qs, 5).get_page(page_number)
    
    proyectos_qs = Proyecto.objects.filter(activo=True).order_by('-fecha_inicio')
    proyectos = Paginator(proyectos_qs, 5).get_page(page_number)
    
    # ===== 5. APLICAR FILTROS SOLO SI HAY BÚSQUEDA (NUEVO) =====
    if query:
        noticias_qs = noticias_qs.filter(Q(titulo__icontains=query) | Q(resumen__icontains=query))
        publicaciones_qs = publicaciones_qs.filter(Q(titulo__icontains=query) | Q(autores__icontains=query))
        investigadores_qs = investigadores_qs.filter(
            Q(nombre__icontains=query) | Q(apellido__icontains=query) | Q(titulo_Academico__icontains=query)
        )
        eventos_qs = eventos_qs.filter(Q(titulo__icontains=query) | Q(descripcion__icontains=query))
        servicios_qs = servicios_qs.filter(Q(nombre__icontains=query) | Q(descripcion__icontains=query))
        laboratorios_qs = laboratorios_qs.filter(Q(nombre__icontains=query) | Q(descripcion__icontains=query))
        proyectos_qs = proyectos_qs.filter(titulo__icontains=query)
        
        # Actualizar contadores para reflejar resultados filtrados
        contadores.update({
            'noticias': noticias_qs.count(),
            'publicaciones': publicaciones_qs.count(),
            'investigadores': investigadores_qs.count(),
            'eventos': eventos_qs.count(),
            'servicios': servicios_qs.count(),
            'laboratorios': laboratorios_qs.count(),
            'proyectos': proyectos_qs.count(),
        })
        
    context = {
        'contadores': contadores,
        'noticias': noticias,
        'publicaciones': publicaciones,
        'investigadores': investigadores,
        'laboratorios': laboratorios,
        'servicios': servicios,
        'eventos': eventos,
        'proyectos': proyectos,
    }
    
    return render(request, 'web_publica/admin/cargas_web.html', context)


# ==================== CRUD NOTICIAS ====================
@login_required
@user_passes_test(es_administrador_o_coordinador)
def editar_noticia_view(request, pk):
    noticia = get_object_or_404(Noticia, pk=pk)
    imagenes = noticia.imagenes.all()      # imágenes adicionales
    videos = noticia.videos_extra.all()    # videos adicionales
    
    if request.method == 'POST':
        form = NoticiaForm(request.POST, request.FILES, instance=noticia)

        if form.is_valid():
            noticia = form.save()

            # =====================
            # GUARDAR IMÁGENES NUEVAS
            # =====================
            nuevas_imgs = request.FILES.getlist('imagenes_adicionales')
            for img in nuevas_imgs:
                NoticiaImagen.objects.create(noticia=noticia, imagen=img)

            # =====================
            # GUARDAR VIDEOS NUEVOS
            # =====================
            nuevos_videos = request.FILES.getlist('videos_adicionales')
            for video in nuevos_videos:
                NoticiaVideo.objects.create(noticia=noticia, video=video)

            messages.success(request, f'Noticia "{noticia.titulo}" actualizada')
            return redirect('web_publica:cargas_web')

    else:
        form = NoticiaForm(instance=noticia)

    return render(request, 'web_publica/forms/editar_noticia.html', {
        'form': form,
        'titulo': f'Editar Noticia: {noticia.titulo}',
        'noticia': noticia,
        'imagenes': imagenes,
        'videos': videos,
    })
    
@login_required
@user_passes_test(es_administrador_o_coordinador)
@require_POST
def eliminar_imagen_noticia(request, imagen_id):
    imagen = get_object_or_404(NoticiaImagen, id=imagen_id)
    imagen.delete()
    return JsonResponse({'success': True})

@require_POST
def eliminar_video_noticia(request, video_id):
    video = get_object_or_404(NoticiaVideo, id=video_id)
    noticia_id = video.noticia.pk
    video.delete()
    return JsonResponse({'success': True})

@login_required
@user_passes_test(es_administrador_o_coordinador)
def eliminar_noticia_view(request, pk):
    noticia = get_object_or_404(Noticia, pk=pk)
    if request.method == 'POST':
        titulo = noticia.titulo
        noticia.delete()
        messages.success(request, f'🗑️ Noticia "{titulo}" eliminada')
        return redirect('web_publica:cargas_web')
    
    return render(request, 'web_publica/forms/eliminar_confirmar.html', {
        'objeto': noticia,
        'tipo': 'Noticia',
        'cancel_url': 'web_publica:cargas_web'
    })

# ==================== CRUD PUBLICACIONES ====================
@login_required
@user_passes_test(es_administrador_o_coordinador)
def editar_publicacion_view(request, pk):
    publicacion = get_object_or_404(Publicacion, pk=pk)
    if request.method == 'POST':
        form = PublicacionForm(request.POST, request.FILES, instance=publicacion)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ Publicación "{publicacion.titulo_corto}" actualizada')
            return redirect('web_publica:cargas_web')
    else:
        form = PublicacionForm(instance=publicacion)
    
    return render(request, 'web_publica/forms/editar_publicacion.html', {
        'form': form,
        'titulo': f'Editar Publicación: {publicacion.titulo_corto}'
    })

@login_required
@user_passes_test(es_administrador_o_coordinador)
def eliminar_publicacion_view(request, pk):
    publicacion = get_object_or_404(Publicacion, pk=pk)
    if request.method == 'POST':
        titulo = publicacion.titulo_corto
        publicacion.delete()
        messages.success(request, f'🗑️ Publicación "{titulo}" eliminada')
        return redirect('web_publica:cargas_web')
    
    return render(request, 'web_publica/forms/eliminar_confirmar.html', {
        'objeto': publicacion,
        'tipo': 'Publicación',
        'cancel_url': 'web_publica:cargas_web'
    })

# ==================== CRUD LABORATORIOS ====================
@login_required
@user_passes_test(es_administrador_o_coordinador)
def editar_laboratorio_view(request, pk):

    laboratorio = get_object_or_404(Laboratorio, pk=pk)

    if request.method == 'POST':
        form = LaboratorioForm(request.POST, request.FILES, instance=laboratorio)
        formset = EquipamientoFormset(request.POST, request.FILES, instance=laboratorio)

        if form.is_valid() and formset.is_valid():

            form.save()

            # Guardar cambios en equipamientos
            equipamientos = formset.save(commit=False)
            for eq in equipamientos:
                eq.laboratorio = laboratorio
                eq.save()

            # Eliminar equipamientos marcados para borrado
            for obj in formset.deleted_objects:
                obj.delete()

            messages.success(request, f'Laboratorio "{laboratorio.nombre}" actualizado correctamente.')
            return redirect('web_publica:laboratorios')

    else:
        form = LaboratorioForm(instance=laboratorio)
        formset = EquipamientoFormset(instance=laboratorio)

    context = {
        'form': form,
        'formset': formset,
        'laboratorio': laboratorio,
        'titulo': f'Editar Laboratorio: {laboratorio.nombre}',
    }

    return render(request, 'web_publica/forms/editar_laboratorio.html', context)


@login_required
@user_passes_test(es_administrador_o_coordinador)
def eliminar_laboratorio_view(request, pk):
    laboratorio = get_object_or_404(Laboratorio, pk=pk)
    if request.method == 'POST':
        nombre = laboratorio.nombre
        laboratorio.delete()
        messages.success(request, f'🗑️ Laboratorio "{nombre}" eliminado')
        return redirect('web_publica:cargas_web')
    
    return render(request, 'web_publica/forms/eliminar_confirmar.html', {
        'objeto': laboratorio,
        'tipo': 'Laboratorio',
        'cancel_url': 'web_publica:cargas_web'
    })

# ==================== CRUD SERVICIOS ====================
@login_required
@user_passes_test(es_administrador_o_coordinador)
def editar_servicio_view(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    if request.method == 'POST':
        form = ServicioForm(request.POST, request.FILES, instance=servicio)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ Servicio "{servicio.nombre}" actualizado')
            return redirect('web_publica:cargas_web')
    else:
        form = ServicioForm(instance=servicio)
    
    return render(request, 'web_publica/forms/editar_servicio.html', {
        'form': form,
        'titulo': f'Editar Servicio: {servicio.nombre}'
    })

@login_required
@user_passes_test(es_administrador_o_coordinador)
def eliminar_servicio_view(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    if request.method == 'POST':
        nombre = servicio.nombre
        servicio.delete()
        messages.success(request, f'🗑️ Servicio "{nombre}" eliminado')
        return redirect('web_publica:cargas_web')
    
    return render(request, 'web_publica/forms/eliminar_confirmar.html', {
        'objeto': servicio,
        'tipo': 'Servicio',
        'cancel_url': 'web_publica:cargas_web'
    })

# ==================== CRUD EVENTOS ====================
@login_required
@user_passes_test(es_administrador_o_coordinador)
def editar_evento_view(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    if request.method == 'POST':
        form = EventoForm(request.POST, request.FILES, instance=evento)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ Evento "{evento.titulo}" actualizado')
            return redirect('web_publica:cargas_web')
    else:
        form = EventoForm(instance=evento)
    
    return render(request, 'web_publica/forms/editar_evento.html', {
        'form': form,
        'titulo': f'Editar Evento: {evento.titulo}'
    })

@login_required
@user_passes_test(es_administrador_o_coordinador)
def eliminar_evento_view(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    if request.method == 'POST':
        titulo = evento.titulo
        evento.delete()
        messages.success(request, f'🗑️ Evento "{titulo}" eliminado')
        return redirect('web_publica:cargas_web')
    
    return render(request, 'web_publica/forms/eliminar_confirmar.html', {
        'objeto': evento,
        'tipo': 'Evento',
        'cancel_url': 'web_publica:cargas_web'
    })

# ==================== CRUD INVESTIGADORES (ya tienes, pero completo) ====================
@login_required
@user_passes_test(es_administrador_o_coordinador)
def editar_investigador_view(request, pk):
    investigador = get_object_or_404(Investigador, pk=pk)
    if request.method == 'POST':
        form = InvestigadorForm(request.POST, request.FILES, instance=investigador)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ Investigador {investigador.nombre_completo} actualizado')
            return redirect('web_publica:cargas_web')
    else:
        form = InvestigadorForm(instance=investigador)
    
    return render(request, 'web_publica/forms/editar_investigador.html', {
        'form': form,
        'titulo': f'Editar Investigador: {investigador.nombre_completo}',
        'investigador': investigador
    })

@login_required
@user_passes_test(es_administrador_o_coordinador)
def eliminar_investigador_view(request, pk):
    investigador = get_object_or_404(Investigador, pk=pk)
    if request.method == 'POST':
        nombre = investigador.nombre_completo
        investigador.delete()
        messages.success(request, f'🗑️ Investigador {nombre} eliminado')
        return redirect('web_publica:cargas_web')
    
    return render(request, 'web_publica/forms/eliminar_confirmar.html', {
        'objeto': investigador,
        'tipo': 'Investigador',
        'cancel_url': 'web_publica:cargas_web'
    })

# ==================== CRUD PROYECTOS ====================
@login_required
@user_passes_test(es_administrador_o_coordinador)
def editar_proyecto_view(request, pk):
    proyecto = get_object_or_404(Proyecto, pk=pk)
    if request.method == 'POST':
        form = ProyectoForm(request.POST, instance=proyecto)
        if form.is_valid():
            proyecto = form.save()
            messages.success(request, f'✅ Proyecto "{proyecto.titulo}" actualizado')
            return redirect('web_publica:cargas_web')
    else:
        form = ProyectoForm(instance=proyecto)
    
    return render(request, 'web_publica/forms/editar_proyecto.html', {
        'form': form,
        'titulo': f'Editar Proyecto: {proyecto.titulo}'
    })

@login_required
@user_passes_test(es_administrador_o_coordinador)
def eliminar_proyecto_view(request, pk):
    proyecto = get_object_or_404(Proyecto, pk=pk)
    if request.method == 'POST':
        titulo = proyecto.titulo
        proyecto.delete()
        messages.success(request, f'🗑️ Proyecto "{titulo}" eliminado')
        return redirect('web_publica:cargas_web')
    
    return render(request, 'web_publica/forms/eliminar_confirmar.html', {
        'objeto': proyecto,
        'tipo': 'Proyecto',
        'cancel_url': 'web_publica:cargas_web'
    })
    
@login_required
@user_passes_test(es_administrador_o_coordinador)
def eliminar_comentario(request, pk):
    comentario = get_object_or_404(ComentarioNoticia, pk=pk)
    noticia_id = comentario.noticia.pk
    comentario.delete()
    messages.success(request, 'Comentario eliminado exitosamente.')
    return redirect('web_publica:noticia_detalle', pk=noticia_id)


from .models import Publicacion
from .utils import obtener_publicaciones_orcid

def sincronizar_publicaciones(investigador):
    import requests

    if not investigador.orcid_id:
        return

    url = f"https://pub.orcid.org/v3.0/{investigador.orcid_id}/works"
    headers = {"Accept": "application/json"}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return

    data = response.json()
    works = data.get("group", [])

    for w in works:
        summary = w.get("work-summary", [{}])[0]

        # 🔹 Título seguro
        titulo = (
            summary.get("title", {})
                   .get("title", {})
                   .get("value", "Sin título")
        )

        # 🔹 Año seguro
        anio = (
            summary.get("publication-date", {})
                   .get("year", {})
                   .get("value", None)
        )

        # 🔹 Revista segura
        revista = (
            (summary.get("journal-title") or {})
                  .get("value", "")
        )

        # 🔹 DOI seguro
        doi = (
            summary.get("external-ids", {})
                   .get("external-id", [{}])[0]
                   .get("external-id-value", "")
        )

        # Crear o recuperar publicación
        pub_obj, created = Publicacion.objects.get_or_create(
            titulo=titulo,
            año=anio,
        )

        # Actualizar datos si están vacíos
        if not pub_obj.revista:
            pub_obj.revista = revista
        if not pub_obj.doi:
            pub_obj.doi = doi

        pub_obj.save()
        pub_obj.fuente = "orcid"
        pub_obj.save()

        # Relación MANY-TO-MANY: agregar investigador
        pub_obj.autores_investigadores.add(investigador)


def sincronizar_publicaciones_scholar(investigador):
    """
    Sincroniza publicaciones desde Google Scholar usando la librería scholarly.
    Mucho más estable que feedparser.
    """

    if not investigador.google_scholar:
        return

    url = investigador.google_scholar.strip()

    # Extraemos ID
    match = re.search(r"user=([\w-]+)", url)
    if match:
        scholar_id = match.group(1)
    else:
        scholar_id = url  # por si meten solo el ID

    try:
        # Obtener perfil
        author = scholarly.search_author_id(scholar_id)
        author = scholarly.fill(author, sections=["publications"])

        for pub in author.get("publications", []):
            titulo = pub.get("bib", {}).get("title", "Sin título")
            link = pub.get("pub_url", "") or ""
            autores = pub.get("bib", {}).get("author", "")
            year = pub.get("bib", {}).get("pub_year", None)

            try:
                año = int(year)
            except:
                año = None

            # Crear o recuperar publicación
            pub_obj, created = Publicacion.objects.get_or_create(
                titulo=titulo,
                año=año if año else 0,
                defaults={
                    "fuente": "scholar",
                    "autores_externos": autores,
                    "link": link,
                }
            )

            # Completar campos faltantes
            if not pub_obj.autores_externos:
                pub_obj.autores_externos = autores
            if not pub_obj.link:
                pub_obj.link = link

            pub_obj.fuente = "scholar"
            pub_obj.save()

            # Vincular M2M
            pub_obj.autores_investigadores.add(investigador)

    except Exception as e:
        print("ERROR SCHOLAR:", e)
        return