from rest_framework import viewsets, permissions
from .models import *
from .serializers import *

class PublicacionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Publicacion.objects.all()
    serializer_class = PublicacionSerializer
    permission_classes = [permissions.AllowAny]

class InvestigadorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Investigador.objects.filter(activo=True)
    serializer_class = InvestigadorSerializer
    permission_classes = [permissions.AllowAny]

class ReservaViewSet(viewsets.ModelViewSet):
    queryset = Reserva.objects.all()
    serializer_class = ReservaSerializer
    permission_classes = [permissions.IsAuthenticated]
    