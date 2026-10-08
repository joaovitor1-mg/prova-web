from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .models import Paciente


class FilaProntoSocorroTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='recepcionista', password='senha123')
        self.client.force_authenticate(user=self.user)

    def test_cadastrar_paciente(self):
        """Requisito 1: Administrador cadastra uma pessoa na fila"""
        payload = {'nome': 'Carlos Silva', 'prioridade': 'normal'}
        response = self.client.post('/api/fila/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Paciente.objects.count(), 1)
        self.assertEqual(Paciente.objects.first().status, 'aguardando')

    def test_chamar_proximo_paciente(self):
        """Requisito 3: Administrador chama o próximo paciente associando sala e médico"""
        paciente = Paciente.objects.create(nome='Maria Oliveira', status='aguardando')
        payload = {'sala': 'Sala 03', 'medico': 'Dra. Helena'}
        
        response = self.client.post(f'/api/fila/{paciente.id}/chamar/', payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        paciente.refresh_from_db()
        self.assertEqual(paciente.status, 'chamado')
        self.assertEqual(paciente.sala, 'Sala 03')
        self.assertEqual(paciente.medico, 'Dra. Helena')
        self.assertIsNotNone(paciente.chamado_em)

    def test_painel_publico_somente_leitura(self):
        """Requisitos 4, 5 e 7: Painel exibe dados e não permite escrita não autorizada"""
        # Criar pacientes
        p1 = Paciente.objects.create(nome='Paciente 1', status='aguardando')
        p2 = Paciente.objects.create(nome='Paciente 2', status='chamado', sala='Sala 01', medico='Dr. Pedro')

        # Cliente deslogado (Painel público)
        anon_client = APIClient()
        response = anon_client.get('/api/painel/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        dados = response.json()

        # Valida contagem
        self.assertEqual(dados['total_aguardando'], 1)
        # Valida último chamado
        self.assertIsNotNone(dados['ultimo_chamado'])
        self.assertEqual(dados['ultimo_chamado']['nome'], 'Paciente 2')
        self.assertEqual(dados['ultimo_chamado']['sala'], 'Sala 01')

        # Tentar alterar dados sem autenticação deve retornar 401/403
        post_response = anon_client.post('/api/fila/', {'nome': 'Hacker'})
        self.assertIn(post_response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_remover_paciente_fila(self):
        """Requisito 2: Administrador remove uma pessoa da fila"""
        paciente = Paciente.objects.create(nome='Desistente', status='aguardando')
        response = self.client.post(f'/api/fila/{paciente.id}/cancelar/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        paciente.refresh_from_db()
        self.assertEqual(paciente.status, 'cancelado')
