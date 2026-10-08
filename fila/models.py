from django.db import models
from django.utils import timezone


class Paciente(models.Model):
    STATUS_CHOICES = [
        ('aguardando', 'Aguardando Atendimento'),
        ('chamado', 'Chamado para Atendimento'),
        ('finalizado', 'Atendimento Finalizado'),
        ('cancelado', 'Cancelado / Desistência'),
    ]

    PRIORIDADE_CHOICES = [
        ('normal', 'Normal'),
        ('preferencial', 'Preferencial'),
    ]

    nome = models.CharField(max_length=150, verbose_name="Nome do Paciente")
    prioridade = models.CharField(
        max_length=20,
        choices=PRIORIDADE_CHOICES,
        default='normal',
        verbose_name="Prioridade"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='aguardando',
        verbose_name="Status"
    )

    sala = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Sala / Consultório"
    )
    medico = models.CharField(
        max_length=120,
        blank=True,
        null=True,
        verbose_name="Médico Responsável"
    )

    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Horário de Chegada")
    chamado_em = models.DateTimeField(null=True, blank=True, verbose_name="Momento da Chamada")
    finalizado_em = models.DateTimeField(null=True, blank=True, verbose_name="Momento de Finalização")

    class Meta:
        ordering = ['criado_em']
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'

    def __str__(self):
        return f"{self.nome} ({self.get_status_display()})"

    def chamar(self, sala, medico):
        self.status = 'chamado'
        self.sala = sala
        self.medico = medico
        self.chamado_em = timezone.now()
        self.save()

    def finalizar(self):
        self.status = 'finalizado'
        self.finalizado_em = timezone.now()
        self.save()

    def cancelar(self):
        self.status = 'cancelado'
        self.finalizado_em = timezone.now()
        self.save()
