from rest_framework import serializers
from .models import Paciente


class PacienteSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    prioridade_display = serializers.CharField(source='get_prioridade_display', read_only=True)

    class Meta:
        model = Paciente
        fields = [
            'id',
            'nome',
            'prioridade',
            'prioridade_display',
            'status',
            'status_display',
            'sala',
            'medico',
            'criado_em',
            'chamado_em',
            'finalizado_em',
        ]
        read_only_fields = ['id', 'status', 'criado_em', 'chamado_em', 'finalizado_em']


class PainelChamadoSerializer(serializers.ModelSerializer):
    """
    Serializer para o Painel Público com foco em privacidade (LGPD).
    Exibe apenas as informações necessárias para a chamada do paciente.
    """
    chamado_em_formatado = serializers.SerializerMethodField()

    class Meta:
        model = Paciente
        fields = [
            'id',
            'nome',
            'sala',
            'medico',
            'prioridade',
            'chamado_em',
            'chamado_em_formatado',
        ]

    def get_chamado_em_formatado(self, obj):
        if obj.chamado_em:
            return obj.chamado_em.strftime('%H:%M:%S')
        return None


class ChamarPacienteSerializer(serializers.Serializer):
    sala = serializers.CharField(max_length=50, required=True)
    medico = serializers.CharField(max_length=120, required=True)
