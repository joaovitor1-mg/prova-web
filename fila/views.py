from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .models import Paciente
from .serializers import (
    ChamarPacienteSerializer,
    PacienteSerializer,
    PainelChamadoSerializer,
)


class PainelPublicoAPIView(APIView):
    """
    Endpoint público (somente leitura) consumido pelo Painel da Sala de Espera.
    Retorna contagem da fila, último chamado e histórico recente.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        total_aguardando = Paciente.objects.filter(status='aguardando').count()

        chamados = Paciente.objects.filter(status='chamado').order_by('-chamado_em')
        ultimo_chamado = chamados.first()
        historico = chamados[1:5] if ultimo_chamado else []

        return Response({
            'total_aguardando': total_aguardando,
            'ultimo_chamado': PainelChamadoSerializer(ultimo_chamado).data if ultimo_chamado else None,
            'historico': PainelChamadoSerializer(historico, many=True).data,
            'timestamp': timezone.now().isoformat(),
        })


class FilaAdminViewSet(ModelViewSet):
    """
    Endpoints administrativos para gerenciamento da fila de atendimento.
    Exige autenticação para escrita/alteração conforme os requisitos de segurança.
    """
    queryset = Paciente.objects.all()
    serializer_class = PacienteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Por padrão retorna pacientes aguardando (prioridade primeiro, depois ordem de chegada)
        status_filtro = self.request.query_params.get('status', 'aguardando')
        if status_filtro == 'todos':
            return Paciente.objects.all().order_by('-criado_em')
        return Paciente.objects.filter(status=status_filtro).order_by(
            '-prioridade', 'criado_em'
        )

    @action(detail=True, methods=['post'])
    def chamar(self, request, pk=None):
        paciente = self.get_object()
        serializer = ChamarPacienteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        paciente.chamar(
            sala=serializer.validated_data['sala'],
            medico=serializer.validated_data['medico']
        )
        return Response(PacienteSerializer(paciente).data)

    @action(detail=False, methods=['post'], url_path='chamar-proximo')
    def chamar_proximo(self, request):
        serializer = ChamarPacienteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        proximo = Paciente.objects.filter(status='aguardando').order_by(
            '-prioridade', 'criado_em'
        ).first()

        if not proximo:
            return Response(
                {'detail': 'Não há nenhum paciente aguardando na fila.'},
                status=status.HTTP_404_NOT_FOUND
            )

        proximo.chamar(
            sala=serializer.validated_data['sala'],
            medico=serializer.validated_data['medico']
        )
        return Response(PacienteSerializer(proximo).data)

    @action(detail=True, methods=['post'])
    def finalizar(self, request, pk=None):
        paciente = self.get_object()
        paciente.finalizar()
        return Response(PacienteSerializer(paciente).data)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        paciente = self.get_object()
        paciente.cancelar()
        return Response(PacienteSerializer(paciente).data)


# -------------------------------------------------------------
# Views de Renderização de Templates
# -------------------------------------------------------------

def painel_view(request):
    """Renderiza a interface do Painel Público (Notebook 3 / Sala de espera)"""
    return render(request, 'painel_publico.html')


@login_required
def recepcao_view(request):
    """Renderiza a interface da Recepção (Notebook 1 / Administrador)"""
    return render(request, 'admin_painel.html')


def login_usuario_view(request):
    """View simples de autenticação para os operadores da recepção"""
    erro = None
    if request.method == 'POST':
        usuario = request.POST.get('username')
        senha = request.POST.get('password')
        user = authenticate(request, username=usuario, password=senha)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', '/recepcao/')
            return redirect(next_url)
        else:
            erro = "Usuário ou senha inválidos."
    return render(request, 'login.html', {'erro': erro})


def logout_usuario_view(request):
    logout(request)
    return redirect('login_view')
