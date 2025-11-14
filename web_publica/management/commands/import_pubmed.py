# web_publica/management/commands/import_pubmed.py
from django.core.management.base import BaseCommand
from web_publica.models import Publicacion
import requests
from datetime import datetime

class Command(BaseCommand):
    help = 'Importa publicaciones desde PubMed usando ORCID'
    
    def add_arguments(self, parser):
        parser.add_argument('orcid', type=str, help='ORCID del investigador')
    
    def handle(self, *args, **options):
        orcid = options['orcid']
        self.stdout.write(f"Buscando publicaciones para ORCID: {orcid}")
        
        # API de ORCID para obtener obras
        url = f"https://pub.orcid.org/v3.0/{orcid}/works"
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'INBIO-Instituto/1.0'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            works = data.get('group', [])
            
            creadas = 0
            for work in works:
                # Extraer información básica
                work_summary = work.get('work-summary', [{}])[0]
                title = work_summary.get('title', {}).get('title', {}).get('value', 'Sin título')
                
                # Verificar si ya existe
                if not Publicacion.objects.filter(titulo=title).exists():
                    publicacion = Publicacion(
                        titulo=title[:500],  # Truncar si es muy largo
                        autores="Autores extraídos automáticamente",
                        año=datetime.now().year,
                        tipo='ARTICULO',
                        revista="Revista extraída de ORCID",
                        link=f"https://orcid.org/{orcid}"
                    )
                    publicacion.save()
                    creadas += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'Se importaron {creadas} publicaciones nuevas')
            )
            
        except requests.exceptions.RequestException as e:
            self.stderr.write(
                self.style.ERROR(f'Error al conectar con ORCID: {str(e)}')
            )
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'Error inesperado: {str(e)}')
            )