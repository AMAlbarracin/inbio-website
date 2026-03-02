from django import forms
from .models import Contacto, Noticia, Laboratorio, Evento, Publicacion,Servicio, Investigador, Proyecto, ComentarioNoticia, LaboratorioImagen, Equipamiento
from django.core.validators import FileExtensionValidator
from django.forms import inlineformset_factory

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
    imagenes_adicionales = forms.FileField(
        required=False,
        widget=forms.FileInput(),  
        label="Imágenes adicionales"
    )
    
    videos_adicionales = forms.FileField(
        required=False,
        widget=forms.FileInput(),
        label="Videos adicionales (máx 3, 50MB c/u)"
    )
    class Meta:
        model = Noticia
        fields = ['titulo', 'fecha_noticia', 'resumen', 'contenido', 
            'imagen', 'video', 'video_url_externa', 'enlace_prensa', 
            'enlace_redes', 'categoria', 'destacada', 'keywords']        
        
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título de la noticia'}),
            'fecha_noticia': forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'YYYY-MM-DD'}),
            'resumen': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Resumen corto'}),
            'contenido': forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Contenido completo'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
            
            'video': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'video/mp4,video/mov,video/avi'
            }),
            'video_url_externa': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.youtube.com/watch?v=...'
            }),
            'enlace_prensa': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://diario.com/noticia/...'
            }),
            'enlace_redes': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://twitter.com/...'
            }),
            
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'destacada': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'keywords': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'bioingenieria, investigacion, salud, ...'
            }),
        }
        help_texts = {
            'video': "Máximo 100MB. Formatos: MP4, MOV, AVI",
            'video_url_externa': "Alternativa a subir video. Pega URL de YouTube o Vimeo",
        }
        
    def clean(self):
        cleaned_data = super().clean()
        video = cleaned_data.get('video')
        video_url = cleaned_data.get('video_url_externa')
        
        # Validar que no se suba ambos tipos de video
        if video and video_url:
            raise forms.ValidationError("Elige subir un video o poner URL externa, no ambos.")
        
        return cleaned_data
    
    def clean_imagenes_adicionales(self):
        files = self.files.getlist('imagenes_adicionales')
        if len(files) > 5:
            raise forms.ValidationError("Máximo 5 imágenes adicionales.")
        return files
    
    def clean_videos_adicionales(self):
        files = self.files.getlist('videos_adicionales')
        if len(files) > 3:
            raise forms.ValidationError("Máximo 3 videos adicionales.")
        
        for video in files:
            if video.size > 50 * 1024 * 1024:  # 50MB
                raise forms.ValidationError(f"El video {video.name} excede los 50MB.")
        
        return files

# NUEVO: Formulario para comentarios
class ComentarioNoticiaForm(forms.ModelForm):
    
    class Meta:
        model = ComentarioNoticia
        fields = ['nombre', 'email', 'contenido']
        
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu nombre completo',
                'maxlength': 100
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'tu@email.com'
            }),
            'contenido': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Comparte tu opinión (máx 500 caracteres)',
                'maxlength': 500
            }),
        }
        
from django import forms
from .models import Publicacion

class PublicacionForm(forms.ModelForm):
    class Meta:
        model = Publicacion
        fields = ['titulo', 'autores_investigadores', 'autores_externos', 'año', 'tipo', 'revista', 'doi', 'link', 'resumen']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título completo de la publicación'}),
            'autores_investigadores': forms.SelectMultiple(
                attrs={'class': 'form-select'}
            ),
            'autores_externos': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 2,
                       'placeholder': 'Autores externos separados por coma'}
            ),
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
        fields = ['nombre', 'descripcion', 'encargado', 'integrantes', 'capacidad', 'imagen_principal']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del laboratorio'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción breve'}),
            'encargado': forms.Select(attrs={'class': 'form-control'}),
            'integrantes': forms.SelectMultiple(attrs={'class': 'form-control'}),            
            'capacidad': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'imagen_principal': forms.FileInput(attrs={'class': 'form-control'}),
        }
        
class LaboratorioImagenForm(forms.ModelForm):
    class Meta:
        model = LaboratorioImagen
        fields = ['imagen']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['imagen'].widget.attrs.update({
            'multiple': True,
            'accept': 'image/*'
        })
        
class EquipamientoForm(forms.ModelForm):
    class Meta:
        model = Equipamiento
        fields = ['nombre', 'descripcion', 'imagen']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del equipamiento'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'imagen': forms.FileInput(attrs={'class': 'form-control'})
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
        fields = ['nombre', 'descripcion', 'imagen', 'activo', 'laboratorio']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del servicio'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Descripción completa del servicio'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'laboratorio': forms.Select(attrs={'class': 'form-control'}),
            
        }
        


class InvestigadorForm(forms.ModelForm):
    class Meta:
        model = Investigador
        fields = ['nombre', 'apellido', 'categoria', 'foto', 'titulo_Academico', 'email', 
                  'telefono', 'biografia', 'linea_investigacion', 'orcid_id', 
                  'google_scholar', 'linkedin', 'publicaciones_destacadas', 
                  'activo', 'orden']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
            'titulo_Academico': forms.TextInput(attrs={'class': 'form-control'}),
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
        
    # 🔽 Hace NO obligatorios los campos indicados
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        opcionales = [
            'biografia', 'linea_investigacion', 'orcid_id', 'google_scholar',
            'linkedin', 'publicaciones_destacadas'
        ]
        for campo in opcionales:
            self.fields[campo].required = False
        
        
        
class ProyectoForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = ['titulo', 'descripcion', 'tipo', 'fecha_inicio', 'fecha_fin', 
                  'estado', 'responsable', 'integrantes', 'laboratorios','activo']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'responsable': forms.Select(attrs={'class': 'form-select'}),
            'integrantes': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'laboratorios': forms.SelectMultiple(attrs={'class': 'form-select'}),               
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
# ---------------------------------------------------
# INLINE FORMSET → Equipamientos dentro del laboratorio
# ---------------------------------------------------

EquipamientoFormset = inlineformset_factory(
    Laboratorio,
    Equipamiento,
    form=EquipamientoForm,
    extra=1,           # cuántos formularios vacíos mostrar
    can_delete=True,   # permitir borrar equipamientos
)
      
