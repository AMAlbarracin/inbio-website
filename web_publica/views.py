from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.contrib import messages
from .models import *
from .forms import ContactoForm, NoticiaForm, PublicacionForm, LaboratorioForm, ServicioForm, EventoForm, InvestigadorForm, ProyectoForm
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from web_publica.utils import enviar_notificacion_reserva
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError

# web_publica/views.py
def home_view(request):
    """Vista de página principal con datos dinámicos"""
    context = {
        'fechas_destacadas': FechaImportante.objects.filter(destacado=True)[:5],
        'miembros_directiva': Investigador.objects.filter(categoria__in=['DIRECTOR', 'CODIRECTOR']),
        'destacadas': Noticia.objects.filter(destacada=True, activa=True)[:3],  # Noticias
        'contadores': {
            'proyectos': 127,
            'publicaciones': Publicacion.objects.count(),
            'investigadores': Investigador.objects.filter(activo=True).count(),
        }
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

def equipo_lista_view(request):
    categoria = request.GET.get('categoria')
    if categoria:
        miembros = Investigador.objects.filter(categoria=categoria, activo=True)
    else:
        miembros = Investigador.objects.filter(activo=True)
    
    context = {
        'miembros': miembros,
        'categorias': Investigador.CATEGORIA_CHOICES,
        'categoria_actual': categoria,
        'es_admin': request.user.is_authenticated and (request.user.is_staff or request.user.groups.filter(name='Coordinadores').exists())
    }
    return render(request, 'web_publica/equipo/lista_investigadores.html', context)

def investigador_detalle_view(request, slug):
    """Perfil individual de investigador"""
    # Crearemos slug automáticamente
    from django.utils.text import slugify
    investigador = Investigador.objects.get(id=slug)  # Temporal
    context = {'investigador': investigador}
    return render(request, 'web_publica/equipo/detalle_investigador.html', context)

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

def publicaciones_lista_view(request):
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

def publicacion_detalle_view(request, pk):
    """Detalle de una publicación específica"""
    publicacion = get_object_or_404(Publicacion, pk=pk)
    context = {'publicacion': publicacion}
    return render(request, 'web_publica/publicaciones/detalle.html', context)

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
    context = {'noticia': noticia}
    return render(request, 'web_publica/noticias/detalle.html', context)

def laboratorios_lista_view(request):
    """Listado de laboratorios disponibles"""
    laboratorios = Laboratorio.objects.filter(activo=True)
    return render(request, 'web_publica/laboratorios/lista.html', {'laboratorios': laboratorios})

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
    """Formulario frontend para cargar noticias"""
    if request.method == 'POST':
        form = NoticiaForm(request.POST, request.FILES)
        if form.is_valid():
            noticia = form.save()
            
            # Guardar múltiples imágenes
            imagenes = request.FILES.getlist('imagenes_adicionales')
            for img in imagenes:
                NoticiaImagen.objects.create(noticia=noticia, imagen=img)
                
            messages.success(request, f'Noticia "{noticia.titulo}" creada exitosamente')
            return redirect('web_publica:noticias')
    else:
        form = NoticiaForm()
    
    context = {
        'form': form,
        'titulo': 'Cargar Nueva Noticia'
    }
    return render(request, 'web_publica/forms/cargar_noticia.html', context)


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
def cargar_laboratorio_view(request):
    """Formulario frontend para cargar laboratorios"""
    if request.method == 'POST':
        form = LaboratorioForm(request.POST, request.FILES)
        if form.is_valid():
            laboratorio = form.save()
            messages.success(request, f'Laboratorio "{laboratorio.nombre}" creado exitosamente')
            return redirect('web_publica:laboratorios')
    else:
        form = LaboratorioForm()
    
    context = {'form': form, 'titulo': 'Cargar Laboratorio'}
    return render(request, 'web_publica/forms/cargar_laboratorio.html', context)


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
    return render(request, 'web_publica/forms/cargar_proyecto.html', context)

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
    if request.method == 'POST':
        form = NoticiaForm(request.POST, request.FILES, instance=noticia)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ Noticia "{noticia.titulo}" actualizada')
            return redirect('web_publica:cargas_web')
    else:
        form = NoticiaForm(instance=noticia)
    
    return render(request, 'web_publica/forms/editar_noticia.html', {
        'form': form,
        'titulo': f'Editar Noticia: {noticia.titulo}'
    })

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
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ Laboratorio "{laboratorio.nombre}" actualizado')
            return redirect('web_publica:cargas_web')
    else:
        form = LaboratorioForm(instance=laboratorio)
    
    return render(request, 'web_publica/forms/editar_laboratorio.html', {
        'form': form,
        'titulo': f'Editar Laboratorio: {laboratorio.nombre}'
    })

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