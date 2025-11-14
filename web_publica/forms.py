from django import forms
from .models import Contacto, Noticia, Laboratorio, Evento, Publicacion,Servicio, Investigador, Proyecto


class ContactoForm(forms.ModelForm):
    class Meta:
        model = Contacto
        fields = ['nombre', 'email', 'asunto', 'mensaje']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu nombre completo'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'tucorreo@ejemplo.com'}),
            'asunto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Asunto del mensaje'}),
            'mensaje': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Tu mensaje...'}),
        }
        


class NoticiaForm(forms.ModelForm):
    class Meta:
        model = Noticia
        fields = ['titulo', 'resumen', 'contenido', 'imagen', 'categoria', 'destacada']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título de la noticia'}),
            'resumen': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Resumen corto'}),
            'contenido': forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Contenido completo'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'destacada': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
from django import forms
from .models import Publicacion

class PublicacionForm(forms.ModelForm):
    class Meta:
        model = Publicacion
        fields = ['titulo', 'autores', 'año', 'tipo', 'revista', 'doi', 'link', 'resumen']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título completo de la publicación'}),
            'autores': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Apellido, Nombre; Apellido, Nombre'}),
            'año': forms.NumberInput(attrs={'class': 'form-control', 'min': 1900, 'max': 2030}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'revista': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la revista/libro'}),
            'doi': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://doi.org/...'}),
            'link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Link alternativo (opcional)'}),
            'resumen': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Abstract o resumen del artículo'}),
        }
        
class LaboratorioForm(forms.ModelForm):
    class Meta:
        model = Laboratorio
        fields = ['nombre', 'descripcion', 'capacidad', 'equipamiento', 'imagen']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del laboratorio'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción breve'}),
            'capacidad': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'equipamiento': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Listado de equipamiento (uno por línea)'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
        }
        
class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = ['titulo', 'descripcion', 'fecha_evento', 'lugar', 'imagen', 'link_inscripcion']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del evento'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fecha_evento': forms.DateTimeInput(attrs={'class': 'form-control', 'placeholder': 'YYYY-MM-DD HH:MM'}),
            'lugar': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lugar del evento'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
            'link_inscripcion': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
        }
        
class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = ['nombre', 'descripcion', 'imagen', 'precio_desde']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del servicio'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Descripción completa del servicio'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
            'precio_desde': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': 0.01}),
        }
        


class InvestigadorForm(forms.ModelForm):
    class Meta:
        model = Investigador
        fields = ['nombre', 'apellido', 'categoria', 'foto', 'cargo', 'email', 
                  'telefono', 'biografia', 'linea_investigacion', 'orcid_id', 
                  'google_scholar', 'linkedin', 'publicaciones_destacadas', 
                  'activo', 'orden']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'biografia': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'linea_investigacion': forms.TextInput(attrs={'class': 'form-control'}),
            'orcid_id': forms.TextInput(attrs={'class': 'form-control'}),
            'google_scholar': forms.URLInput(attrs={'class': 'form-control'}),
            'linkedin': forms.URLInput(attrs={'class': 'form-control'}),
            'publicaciones_destacadas': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        
        
        
class ProyectoForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = ['titulo', 'descripcion', 'tipo', 'fecha_inicio', 'fecha_fin', 
                  'estado', 'responsable', 'activo']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'responsable': forms.Select(attrs={'class': 'form-select'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
        
