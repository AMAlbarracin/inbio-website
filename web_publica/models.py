from django.db import models
from django.core.validators import RegexValidator

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

class Investigador(models.Model):
    CATEGORIA_CHOICES = [
        ('DIRECTOR', 'Director'),
        ('SUBDIRECTOR', 'Subdirector'),
        ('INVESTIGADOR_S', 'Investigador Senior'),
        ('INVESTIGADOR_J', 'Investigador Junior'),
        ('BECARIO', 'Becario'),
        ('ADMIN', 'Personal Administrativo'),
    ]
    
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    categoria = models.CharField(max_length=30, choices=CATEGORIA_CHOICES)
    foto = models.ImageField(upload_to='equipo/', blank=True, default='default.jpg')
    cargo = models.CharField(max_length=200)
    email = models.EmailField()
    telefono = models.CharField(max_length=20, blank=True, validators=[
        RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Formato inválido")
    ])
    biografia = models.TextField()
    linea_investigacion = models.CharField(max_length=200)
    orcid_id = models.CharField(max_length=50, blank=True)
    google_scholar = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    publicaciones_destacadas = models.TextField(help_text="Una por línea", blank=True)
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
    
    
class Publicacion(models.Model):
    TIPO_CHOICES = [
        ('ARTICULO', 'Artículo Científico'),
        ('CAPITULO', 'Capítulo de Libro'),
        ('CONFERENCIA', 'Conferencia'),
        ('PATENTE', 'Patente'),
    ]
    
    titulo = models.CharField(max_length=500)
    autores = models.TextField(help_text="Separados por coma")
    año = models.IntegerField()
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='ARTICULO')
    revista = models.CharField(max_length=200, blank=True)
    doi = models.URLField(blank=True)
    link = models.URLField(blank=True)
    resumen = models.TextField(blank=True)
    destacada = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-año', '-id']
        verbose_name_plural = "Publicaciones"
    
    def __str__(self):
        return f"{self.titulo[:50]}... ({self.año})"
    
    
class Noticia(models.Model):
    # ✅ DEFINIMOS CATEGORIA_CHOICES como atributo de clase
    CATEGORIA_CHOICES = [
        ('NOTICIA', 'Noticia'),
        ('EVENTO', 'Evento'),
        ('PRENSA', 'Nota de Prensa'),
    ]
    
    titulo = models.CharField(max_length=200)
    resumen = models.TextField()
    contenido = models.TextField()
    imagen = models.ImageField(upload_to='noticias/', blank=True)
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES)  # ✅ Usamos la constante
    destacada = models.BooleanField(default=False)
    activa = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-fecha_publicacion']
        verbose_name_plural = "Noticias y Eventos"
    
    def __str__(self):
        return self.titulo
    
    def get_categoria_display(self):
        """Método para mostrar el nombre legible de la categoría"""
        return dict(self.CATEGORIA_CHOICES).get(self.categoria, '')
    


    
class Laboratorio(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    capacidad = models.IntegerField()
    equipamiento = models.TextField()
    imagen = models.ImageField(upload_to='laboratorios/', blank=True)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nombre

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
    
class Servicio(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to='servicios/', blank=True)
    precio_desde = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
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
    
# VERSIÓN NUEVA (USAR ESTA)
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
    
    