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
    