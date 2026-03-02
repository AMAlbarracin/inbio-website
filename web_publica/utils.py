from django.core.mail import send_mail
from django.conf import settings

def enviar_notificacion_reserva(reserva):
    """Envía email cuando se crea o actualiza una reserva"""
    asunto = f'[IBIO] Reserva {reserva.get_estado_display()} - {reserva.laboratorio.nombre}'
    
    mensaje = f'''
    Estimado/a {reserva.investigador.nombre_completo},
    
    Su reserva ha sido {reserva.get_estado_display().lower()}:
    
    Laboratorio: {reserva.laboratorio.nombre}
    Fecha: {reserva.fecha}
    Hora: {reserva.hora_inicio} - {reserva.hora_fin}
    Descripción: {reserva.descripcion}
    
    Atentamente,
    Instituto de Bioingeniería
    '''
    
    send_mail(
        asunto,
        mensaje,
        settings.EMAIL_HOST_USER,
        [reserva.investigador.email, 'admin@instituto.edu'],
        fail_silently=False,
    )
    
import requests

def obtener_publicaciones_orcid(orcid_id):
    url = f"https://pub.orcid.org/v3.0/{orcid_id}/works"
    
    headers = {
        "Accept": "application/json"
    }
    
    r = requests.get(url, headers=headers)
    
    if r.status_code != 200:
        return []
    
    data = r.json()
    publicaciones = []

    for item in data.get("group", []):
        work = item["work-summary"][0]  # resumen principal

        pub = {
            "titulo": work.get("title", {}).get("title", {}).get("value"),
            "anio": work.get("publication-date", {}).get("year", {}).get("value"),
            "tipo": work.get("type"),
            "doi": None,
        }

        # Buscar DOI si existe
        for ext_id in work.get("external-ids", {}).get("external-id", []):
            if ext_id.get("external-id-type") == "doi":
                pub["doi"] = ext_id.get("external-id-value")

        publicaciones.append(pub)

    return publicaciones

# yourapp/utils_scholar.py
import requests
import feedparser
import re
from django.core.cache import cache
from datetime import timedelta

# Tiempo de cache en segundos (por defecto 6 horas)
SCHOLAR_CACHE_TIMEOUT = 60 * 60 * 6

def build_scholar_rss_url(scholar_id, pagesize=50):
    """
    Construye la URL RSS pública de Google Scholar para un usuario.
    scholar_id: la parte 'user' de https://scholar.google.com/citations?user=XXXXXXXX
    pagesize: cantidad aproximada de items a pedir (Google Scholar no documenta oficialmente).
    """
    # La URL con output=rss devuelve un feed
    # Nota: a veces funciona con "user" y "hl=es"
    return f"https://scholar.google.com/citations?hl=en&user={scholar_id}&view_op=list_works&sortby=pubdate&cstart=0&pagesize={pagesize}&output=rss"

def parse_entry_to_pub(entry):
    """
    Convierte un item de feedparser a dict con campos que usamos.
    entry es un objeto de feedparser.
    """
    title = entry.get("title", "").strip()
    link = entry.get("link", "")
    summary = entry.get("summary", "")  # suele contener autores/journal
    # Intento extraer año con regex simple
    year = None
    m = re.search(r'\b(19|20)\d{2}\b', summary)
    if m:
        year = m.group(0)
    # Extraer autores/journal aproximado del summary (no siempre limpio)
    # summary puede tener: "Author1, Author2 - Journal, YEAR"
    authors = ""
    journal = ""
    if summary:
        # separo por " - " o por punto
        parts = [p.strip() for p in re.split(r' - |\.\s+', summary) if p.strip()]
        if len(parts) >= 1:
            authors = parts[0]
        if len(parts) >= 2:
            journal = parts[1]
    return {
        "titulo": title,
        "autores": authors,
        "revista": journal,
        "año": year,
        "link": link,
        "fuente": "scholar",
    }

def fetch_scholar_pubs(scholar_id, pagesize=50, use_cache=True):
    """
    Devuelve lista de dicts: [{'titulo','autores','revista','año','link','fuente'}, ...]
    Usa cache por SCHOLAR_CACHE_TIMEOUT segundos para no golpear Google Scholar en cada carga.
    """
    if not scholar_id:
        return []

    cache_key = f"scholar_pubs_{scholar_id}"
    if use_cache:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

    url = build_scholar_rss_url(scholar_id, pagesize=pagesize)
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            return []
        feed = feedparser.parse(resp.content)
        pubs = []
        for entry in feed.entries:
            pub = parse_entry_to_pub(entry)
            pubs.append(pub)
        # Guardar en cache
        cache.set(cache_key, pubs, SCHOLAR_CACHE_TIMEOUT)
        return pubs
    except Exception:
        # no propagamos el error al usuario, devolvemos vacío
        return []
    

