from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


# ============================================================
# 1) HISTORIA Y VALORES INSTITUCIONALES
# ============================================================
class FechaImportante(models.Model):
    """Para la línea de tiempo de historia"""
    fecha = models.DateField()
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to='historia/', blank=True)
    destacado = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['fecha']
        verbose_name_plural = "Fechas Importantes"
    
    def __str__(self):
        return f"{self.fecha.year}: {self.titulo}"

class ValorInstitucional(models.Model):
    """Para Misión, Visión, Valores"""
    TIPO_CHOICES = [
        ('MISION', 'Misión'),
        ('VISION', 'Visión'),
        ('VALOR', 'Valor'),
        ('OBJETIVO', 'Objetivo'),
    ]
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField()
    icono = models.CharField(max_length=50, help_text="Ej: fa-dna, fa-microscope")  # FontAwesome
    orden = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['orden']
    
    def __str__(self):
        return self.titulo

# ============================================================
# 2) INVESTIGADORES / EQUIPO
# ============================================================

class Investigador(models.Model):
    CATEGORIA_CHOICES = [
        ('DIRECTOR', 'Director'),
        ('SUBDIRECTOR', 'Subdirector'),
        ('INVESTIGADOR', 'Investigador'),
        ('DOCENTE', 'Docente'),
        ('BECARIO', 'Becario'),
        ('ADMIN/TEC', 'Administrativo / Tecnico'),
    ]
    
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    categoria = models.CharField(max_length=30, choices=CATEGORIA_CHOICES)
    foto = models.ImageField(upload_to='equipo/', blank=True, default='default.jpg')
    titulo_Academico = models.CharField(max_length=200)
    email = models.EmailField()
    telefono = models.CharField(max_length=20, blank=True, validators=[
        RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Formato inválido")
    ])
    biografia = models.TextField(blank=True, null=True)
    linea_investigacion = models.CharField(max_length=200, blank=True, null=True)
    orcid_id = models.CharField(max_length=50, blank=True, null=True)
    google_scholar = models.URLField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    publicaciones_destacadas = models.TextField(help_text="Una por línea", blank=True, null=True)
    activo = models.BooleanField(default=True)
    orden = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['orden', 'apellido', 'nombre']
        verbose_name_plural = "Investigadores"
    
    def __str__(self):
        return f"{self.apellido}, {self.nombre}"
    
    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"
    
    def get_publicaciones_list(self):
        return self.publicaciones_destacadas.split('\n') if self.publicaciones_destacadas else []

# ============================================================
# 3) CONTACTO
# ============================================================
class Contacto(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.EmailField()
    asunto = models.CharField(max_length=200)
    mensaje = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha_envio']
    
    def __str__(self):
        return f"{self.nombre} - {self.asunto}"
    
# ============================================================
# 4) PUBLICACIONES CIENTÍFICAS
# ============================================================
    
class Publicacion(models.Model):
    TIPO_CHOICES = [
        ('ARTICULO', 'Artículo Científico'),
        ('CAPITULO', 'Capítulo de Libro'),
        ('CONFERENCIA', 'Conferencia'),
        ('PATENTE', 'Patente'),       
        ('LIBRO', 'Libro'),        
        ('REVIEW', 'Review'),
        ('TESIS', 'Tesis'),
        
    ]
    
    titulo = models.CharField(max_length=500)
    autores_investigadores = models.ManyToManyField(
        "Investigador",
        related_name="publicaciones",
        blank=True
    )
    # 🔹 Autores externos (texto libre opcional)
    autores_externos = models.TextField(
        blank=True,
        help_text="Autores externos, separados por coma"
    )
    
    año = models.IntegerField()
    # ⭐ NUEVO: Diccionario para acceso rápido
    TIPO_CHOICES_DICT = dict(TIPO_CHOICES)
    
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='ARTICULO')
    revista = models.CharField(max_length=200, blank=True)
    doi = models.URLField(blank=True)
    link = models.URLField(blank=True, null=True)
    resumen = models.TextField(blank=True)
    destacada = models.BooleanField(default=False)
    # Para saber de dónde viene esta publicación
    fuente = models.CharField(max_length=20, null=True, blank=True, choices=[
        ("orcid", "ORCID"),
        ("scholar", "Google Scholar"),
    ])
    
    class Meta:
        ordering = ['-año', '-id']
        verbose_name_plural = "Publicaciones"
    
    def __str__(self):
        return f"{self.titulo[:50]}... ({self.año}) ({self.fuente})"
    
    # 🔹 Combina internos + externos para mostrar en template
    def autores_completos(self):
        internos = ", ".join(i.nombre_completo for i in self.autores_investigadores.all())
        externos = self.autores_externos or ""
        if internos and externos:
            return internos + ", " + externos
        return internos or externos    
    
    @property
    def titulo_corto(self):
        return self.titulo[:40] + "..." if len(self.titulo) > 40 else self.titulo

# ============================================================
# 5) NOTICIAS
# ============================================================
    
class Noticia(models.Model):    
    CATEGORIA_CHOICES = [
        ('NOTICIA', 'Noticia'),        
        ('PRENSA', 'Nota de Prensa'),
    ]
    
    titulo = models.CharField(max_length=200)
    fecha_noticia = models.DateField(null=True, blank=True)
    resumen = models.TextField()
    contenido = models.TextField()
    imagen = models.ImageField(upload_to='noticias/', blank=True)
    
    # Campo de video
    video = models.FileField(upload_to='noticias/videos/', blank=True, null=True, help_text="Video opcional (MP4, máx 100MB)")
    video_url_externa = models.URLField(blank=True, help_text="URL de YouTube/Vimeo (alternativa a subir video)")
    
    # Enlaces a publicaciones externas
    enlace_prensa = models.URLField(blank=True, help_text="Link a nota original en medio de prensa")
    enlace_redes = models.URLField(blank=True, help_text="Link a publicación en redes sociales")
    
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES)  # ✅ Usamos la constante
    destacada = models.BooleanField(default=False)
    activa = models.BooleanField(default=True)
    
    # Metadatos SEO
    keywords = models.CharField(max_length=255, blank=True, help_text="Palabras clave separadas por coma")
    lectura_estimada = models.PositiveIntegerField(default=5, help_text="Tiempo de lectura en minutos")
    
    class Meta:
        ordering = ['-fecha_noticia']
        verbose_name_plural = "Noticias"
    
    def __str__(self):
        return self.titulo
    
    def get_categoria_display(self):
        """Método para mostrar el nombre legible de la categoría"""
        return dict(self.CATEGORIA_CHOICES).get(self.categoria, '')
    
    def tiene_video(self):
        """Verifica si la noticia tiene video local o externo"""
        return bool(self.video or self.video_url_externa)
    
    def get_video_type(self):
        """Retorna el tipo de video: 'local', 'youtube', 'vimeo' o None"""
        if self.video:
            return 'local'
        elif 'youtube.com' in self.video_url_externa or 'youtu.be' in self.video_url_externa:
            return 'youtube'
        elif 'vimeo.com' in self.video_url_externa:
            return 'vimeo'
        return None

# Modelo para imágenes adicionales
class NoticiaImagen(models.Model):
    noticia = models.ForeignKey(Noticia, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to='noticias/')
    
    def __str__(self):
        return f"Imagen {self.id} de {self.noticia.titulo}"

# Modelo para videos adicionales
class NoticiaVideo(models.Model):
    noticia = models.ForeignKey(Noticia, on_delete=models.CASCADE, related_name='videos_extra')
    video = models.FileField(upload_to='noticias/videos/')
    titulo = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"Video {self.id} de {self.noticia.titulo}"

# Modelo para comentarios de noticias
class ComentarioNoticia(models.Model):
    noticia = models.ForeignKey(Noticia, on_delete=models.CASCADE, related_name='comentarios')
    nombre = models.CharField(max_length=100, help_text="Tu nombre completo")
    email = models.EmailField(help_text="No será publicado")
    contenido = models.TextField(max_length=500, help_text="Máximo 500 caracteres")
    
    # NUEVO: Campo para moderación
    aprobado = models.BooleanField(default=False)
    spam = models.BooleanField(default=False)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name_plural = "Comentarios de Noticias"
    
    # ✅ SOLUCIÓN: Definir el manager AQUÍ, no con add_to_class
    objects = models.Manager()  # Manager por defecto
    aprobados = models.Manager()  # Manager para TODOS (filtraremos en la vista)


# ============================================================
# 6) LABORATORIOS (con relaciones nuevas)
# ============================================================  
class Laboratorio(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    capacidad = models.IntegerField()
     # Nuevo modelo
    equipamiento = models.ManyToManyField(
        'Equipamiento',
        related_name='laboratorios',
        blank=True
    )
    
    encargado = models.ForeignKey(
        Investigador,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='laboratorios_a_cargo'
    )

    integrantes = models.ManyToManyField(
        Investigador,
        related_name='laboratorios_participantes',
        blank=True
    )
    
    imagen_principal = models.ImageField(upload_to='laboratorios/', blank=True)
    activo = models.BooleanField(default=True)
    
    proyectos = models.ManyToManyField(
        "Proyecto",
        related_name="laboratorios_colaboradores", 
        blank=True
    )
    
    servicios = models.ManyToManyField(
        "Servicio", 
        related_name="laboratorios", blank=True)
    
    def __str__(self):
        return self.nombre

# Galería de imágenes adicionales
class LaboratorioImagen(models.Model):
    laboratorio = models.ForeignKey(
        Laboratorio,
        on_delete=models.CASCADE,
        related_name='galeria'
    )
    imagen = models.ImageField(upload_to='laboratorios/galeria')

    def __str__(self):
        return f"Imagen de {self.laboratorio.nombre}"

class Equipamiento(models.Model):
    laboratorio = models.ForeignKey(
        Laboratorio, 
        on_delete=models.CASCADE, 
        related_name='equipos'
    )
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='equipamiento/', blank=True, null=True)
    estado = models.CharField(
        max_length=30,
        choices=[
            ('operativo', 'Operativo'),
            ('mantenimiento', 'En mantenimiento'),
            ('fuera_servicio', 'Fuera de servicio')
        ],
        default='operativo'
    )
    
    def __str__(self):
        return f"{self.nombre} ({self.laboratorio.nombre})"

    
# ============================================================
# 7) RESERVAS DE LABORATORIO
# ============================================================
class Reserva(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('APROBADA', 'Aprobada'),
        ('RECHAZADA', 'Rechazada'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    laboratorio = models.ForeignKey(Laboratorio, on_delete=models.CASCADE, related_name='reservas')
    investigador = models.ForeignKey(Investigador, on_delete=models.CASCADE)
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    descripcion = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha', '-hora_inicio']
    
    def __str__(self):
        return f"{self.laboratorio} - {self.investigador} ({self.fecha})"

# ============================================================
# 8) SERVICIOS
# ============================================================    
class Servicio(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to='servicios/', blank=True)
    activo = models.BooleanField(default=True)
    laboratorio = models.ForeignKey(
        Laboratorio, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='laboratorio_del_servicio'
    )

     
    def __str__(self):
        return self.nombre

class SolicitudServicio(models.Model):
    ESTADO_CHOICES = [
        ('NUEVA', 'Nueva'),
        ('PRESUPUESTO', 'En Presupuesto'),
        ('EJECUCION', 'En Ejecución'),
        ('FINALIZADA', 'Finalizada'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    empresa = models.CharField(max_length=200)
    contacto = models.CharField(max_length=100)
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE)
    descripcion = models.TextField()
    archivo_adjunto = models.FileField(upload_to='solicitudes/', blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='NUEVA')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.empresa} - {self.servicio} ({self.estado})"
    
# ============================================================
# 9) EVENTOS
# ============================================================
class Evento(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    fecha_evento = models.DateTimeField()
    lugar = models.CharField(max_length=200)
    imagen = models.ImageField(upload_to='eventos/', blank=True, null=True)
    link_inscripcion = models.URLField(blank=True)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.titulo

# ============================================================
# 10) PROYECTOS
# ============================================================    
class Proyecto(models.Model):
    TIPO_INVESTIGACION = 'interno'
    TIPO_COLABORATIVO = 'colaborativo'
    TIPO_CHOICES = [
        (TIPO_INVESTIGACION, 'Proyecto de Investigación'),
        (TIPO_COLABORATIVO, 'Proyecto Colaborativo'),
    ]
    
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default=TIPO_INVESTIGACION)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=[
        ('PLANIFICACION', 'En Planificación'),
        ('ACTIVO', 'Activo'),
        ('COMPLETADO', 'Completado'),
    ], default='PLANIFICACION')
    responsable = models.ForeignKey('Investigador', on_delete=models.CASCADE, related_name='proyectos')
    integrantes = models.ManyToManyField(
        Investigador,
        related_name='proyectos_participantes',
        blank=True
    )
    laboratorios = models.ManyToManyField(
        Laboratorio, 
        blank=True, 
        related_name='proyectos_asociados'
    )

    activo = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-fecha_inicio']
        verbose_name_plural = "Proyectos"
    
    def __str__(self):
        return self.titulo
    
    @property
    def duracion(self):
        """Calcula duración en meses"""
        if self.fecha_fin:
            return (self.fecha_fin.year - self.fecha_inicio.year) * 12 + (self.fecha_fin.month - self.fecha_inicio.month)
        return "En curso"
    
    