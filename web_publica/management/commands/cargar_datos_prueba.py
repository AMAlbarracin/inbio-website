# web_publica/management/commands/cargar_datos_prueba.py
from django.core.management.base import BaseCommand
from web_publica.models import *
from django.core.files import File
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Carga datos de prueba realistas para el IBIO'
    
    def handle(self, *args, **options):
        self.stdout.write("🚀 Cargando datos de prueba...")
        
        # 1. CREAR INVESTIGADORES
        investigadores_data = [
            {
                'nombre': 'Juan',
                'apellido': 'García López',
                'categoria': 'DIRECTOR',
                'titulo_Academico': 'Director del Instituto',
                'email': 'j.garcia@instituto.edu',
                'linea_investigacion': 'Biomateriales y Regeneración Tisular',
                'orcid_id': '0000-0002-1825-0097',
                'google_scholar': 'https://scholar.google.com/citations?user=example',
                'biografia': 'Dr. García es especialista en ingeniería de tejidos con 15 años de experiencia...',
                'publicaciones_destacadas': 'Nature Biotechnology 2024; Journal of Biomedical Materials Research 2023'
            },
            # Puedes añadir más investigadores aquí...
        ]
        
        for data in investigadores_data:
            if not Investigador.objects.filter(email=data['email']).exists():
                inv = Investigador.objects.create(**data)
                self.stdout.write(f"✅ Investigador: {inv.nombre_completo}")
        
        # 2. CREAR PUBLICACIONES
        publicaciones_data = [
            {
                'titulo': 'Advances in Neural Biomaterials: A 2024 Review',
                'autores': 'García, J.; López, M.; Rodríguez, A.',
                'año': 2024,
                'tipo': 'ARTICULO',
                'revista': 'Nature Biotechnology',
                'doi': 'https://doi.org/10.1038/s41587-024-02145-8',
                'resumen': 'This review covers the latest advances in neural biomaterials...'
            },
            # Puedes añadir más...
        ]
        
        for data in publicaciones_data:
            if not Publicacion.objects.filter(titulo=data['titulo']).exists():
                pub = Publicacion.objects.create(**data)
                self.stdout.write(f"✅ Publicación: {pub.titulo[:50]}...")
        
        # 3. CREAR NOTICIAS DESTACADAS
        noticias_data = [
            {
                'titulo': 'Nueva Publicación en Nature Biotechnology',
                'resumen': 'Nuestro equipo liderado por el Dr. García publica un artículo revolucionario...',
                'contenido': 'El IBIO se enorgullece de anunciar la publicación más reciente en Nature Biotechnology...',
                'categoria': 'NOTICIA',
                'destacada': True
            },
            {
                'titulo': 'Seminario Internacional: Inteligencia Artificial en Medicina',
                'resumen': 'El próximo 15 de diciembre tendremos al Dr. Smith de MIT...',
                'contenido': 'No te pierdas este evento exclusivo con uno de los líderes mundiales...',
                'categoria': 'EVENTO',
                'destacada': True
            }
        ]
        
        for data in noticias_data:
            if not Noticia.objects.filter(titulo=data['titulo']).exists():
                noticia = Noticia.objects.create(**data)
                self.stdout.write(f"✅ Noticia: {noticia.titulo}")
        
        # 4. CREAR LABORATORIOS
        laboratorios_data = [
            {
                'nombre': 'Laboratorio de Biomecánica Avanzada',
                'descripcion': 'Equipado con tecnología de última generación para análisis de movimiento humano',
                'capacidad': 12,
                'equipamiento': 'Cámara de alta velocidad Vicon, Plataforma de fuerza, Software MATLAB'
            },
            {
                'nombre': 'Laboratorio de Biomateriales',
                'descripcion': 'Síntesis y caracterización de materiales biocompatibles',
                'capacidad': 8,
                'equipamiento': 'Microscopio SEM, Espectrofotómetro, Liofilizador'
            }
        ]
        
        for data in laboratorios_data:
            if not Laboratorio.objects.filter(nombre=data['nombre']).exists():
                lab = Laboratorio.objects.create(**data)
                self.stdout.write(f"✅ Laboratorio: {lab.nombre}")
        
        # 5. CREAR SERVICIOS PARA EMPRESAS
        servicios_data = [
            {
                'nombre': 'Desarrollo de Biomateriales',
                'descripcion': 'Diseño y validación de materiales biocompatibles para aplicaciones médicas',
                'precio_desde': 75000.00
            },
            {
                'nombre': 'Análisis Biomecánico',
                'descripcion': 'Estudios de movimiento y carga mecánica en sistemas biológicos',
                'precio_desde': 50000.00
            }
        ]
        
        for data in servicios_data:
            if not Servicio.objects.filter(nombre=data['nombre']).exists():
                serv = Servicio.objects.create(**data)
                self.stdout.write(f"✅ Servicio: {serv.nombre}")
        
        # 6. CREAR FECHAS IMPORTANTES (HISTORIA)
        fechas_data = [
            {
                'fecha': '2020-03-15',
                'titulo': 'Fundación del Instituto de Bioingeniería',
                'descripcion': 'Se crea el IBIO con el objetivo de liderar la investigación en tecnologías de salud',
                'destacado': True
            },
            {
                'fecha': '2021-08-01',
                'titulo': 'Primer Convenio con Hospital Universitario',
                'descripcion': 'Colaboración para desarrollar prótesis personalizadas'
            }
        ]
        
        for data in fechas_data:
            if not FechaImportante.objects.filter(titulo=data['titulo']).exists():
                fecha = FechaImportante.objects.create(**data)
                self.stdout.write(f"✅ Fecha Importante: {fecha.titulo}")
        
        self.stdout.write(self.style.SUCCESS("\n🎉 Datos de prueba cargados exitosamente!"))
        self.stdout.write("\nPrueba estas URLs:")
        self.stdout.write("  - http://127.0.0.1:8000/")
        self.stdout.write("  - http://127.0.0.1:8000/publicaciones/")
        self.stdout.write("  - http://127.0.0.1:8000/noticias/")
        self.stdout.write("  - http://127.0.0.1:8000/equipo/")
        
        