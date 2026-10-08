# 🏥 Fila de Pronto-Socorro — Sistema Distribuído (Web II)

Sistema distribuído de gerenciamento de fila de atendimento hospitalar com atualização em tempo real e aviso sonoro, desenvolvido com **Django** e **Django REST Framework (DRF)**.

---

## 📐 1. Arquitetura do Sistema (3 Máquinas)

O sistema opera de forma desacoplada em três nós conectados na mesma **Rede Local (LAN)**:

```
                      ┌────────────────────────────────────────┐
                      │              REDE LOCAL                │
                      │         (ex: 192.168.1.0/24)           │
                      └──────────────────┬─────────────────────┘
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        │                                │                                │
        ▼                                ▼                                ▼
┌─────────────────┐             ┌─────────────────┐             ┌─────────────────┐
│   NOTEBOOK 1    │             │   NOTEBOOK 2    │             │   NOTEBOOK 3    │
│  User / Admin   │             │   Servidor Core │             │  Painel Público │
├─────────────────┤             ├─────────────────┤             ├─────────────────┤
│ • Recepção      │  HTTP REST  │ • Django + DRF  │  HTTP / Polling│ • Sala Espera   │
│ • Cadastra Pac. │────────────>│ • SQLite DB     │<────────────│ • Contagem Fila │
│ • Chama Paciente│             │ • Auth & Regras │             │ • Nome + Sala   │
│ • Remove / Fim  │             │ • Central de API│             │ • Alerta Sonoro │
└─────────────────┘             └─────────────────┘             └─────────────────┘
```

### Papéis e Responsabilidades:
1. **Notebook 2 (Servidor Backend & Banco):**
   - Roda a API Django REST Framework vinculada ao IP da rede (`0.0.0.0:8000`).
   - Centraliza o banco SQLite, persistência dos dados e validação de permissões.
   - Fornece endpoints autenticados para a Recepção e endpoints de leitura pública para o Painel.
2. **Notebook 1 (Recepção / Admin):**
   - Interface de controle da recepcionista.
   - Autenticado via Session ou Token.
   - Operações: Adicionar paciente à fila, chamar próximo (selecionando sala e médico) e remover da fila.
3. **Notebook 3 (Painel Público / Sala de Espera):**
   - Interface pública somente leitura (LGPD: exibe nome sem expor dados sensíveis).
   - Consulta contínua ao backend (Polling inteligente / SSE a cada 2 segundos).
   - Dispara aviso sonoro via Web Audio API / áudio HTML5 a cada nova chamada detectada.
   - Indicador visual de conectividade (resiliente a perdas de conexão).

---

## 🛠️ 2. Especificação Rápida dos Endpoints (DRF)

| Método | Endpoint | Acesso | Descrição |
|---|---|---|---|
| `GET` | `/api/painel/` | **Público** | Retorna contagem de espera, última chamada (nome, sala, médico) e histórico recente. |
| `POST` | `/api/fila/` | **Admin** | Cadastra novo paciente na fila de espera. |
| `GET` | `/api/fila/` | **Admin** | Lista todos os pacientes que ainda aguardam atendimento. |
| `POST` | `/api/fila/<id>/chamar/` | **Admin** | Marca paciente como chamado, vinculando `sala` e `medico`. |
| `POST` | `/api/fila/<id>/finalizar/` | **Admin** | Remove paciente da fila (atendimento concluído ou desistência). |

---

## 🚀 3. Instruções de Execução por Máquina

### 🖥️ MÁQUINA 2: Servidor (Django + DRF)

1. **Clonar o repositório:**
   ```bash
   git clone <URL_DO_REPOSITORIO>
   cd pronto_socorro
   ```

2. **Criar e ativar ambiente virtual:**
   ```bash
   python -m venv venv
   # No Linux:
   source venv/bin/activate
   # No Windows:
   .\venv\Scripts\activate
   ```

3. **Instalar dependências:**
   ```bash
   pip install django djangorestframework django-cors-headers
   ```

4. **Aplicar migrações e criar usuário admin:**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. **Identificar o IP da máquina na rede local:**
   - **Linux:** `ip -4 addr show | grep inet`
   - **Windows:** `ipconfig`
   *(Exemplo encontrado: `192.168.1.100`)*

6. **Iniciar o servidor aberto na rede:**
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

---

### 💻 MÁQUINA 1: Recepção (Admin)

1. Certifique-se de estar na **mesma rede Wi-Fi / cabo** que a Máquina 2.
2. Abra o navegador e acesse:
   ```
   http://192.168.1.100:8000/admin-painel/
   ```
   *(Substitua `192.168.1.100` pelo IP real da Máquina 2).*
3. Faça login com as credenciais administrativas criadas.
4. **Fluxo:** Cadastre novos pacientes, visualize a fila em tempo real e utilize o botão **"Chamar Próximo"** informando o médico e o consultório.

---

### 📺 MÁQUINA 3: Painel Público (Sala de Espera)

1. Certifique-se de estar na **mesma rede** que a Máquina 2.
2. Abra o navegador em tela cheia (`F11`) e acesse:
   ```
   http://192.168.1.100:8000/painel/
   ```
3. **⚠️ Passo Essencial para o Som:**
   - Por restrição de segurança dos navegadores contra reprodução automática, clique no botão **"🔔 Habilitar Alerta Sonoro / Iniciar Painel"** que aparece na tela.
4. A partir desse momento, a tela atualizará a contagem automaticamente e tocará o aviso sonoro a cada nova chamada realizada pelo Notebook 1.

---

## 🧪 4. Roteiro de Demonstração e Testes (Bloco 3)

1. **Cenário Normal:**
   - Notebook 1 cadastra 3 pacientes (ex: Carlos Silva, Maria Santos, João Oliveira).
   - Observar no Notebook 3 o contador mudar instantaneamente para `3 pessoas aguardando`.
   - Notebook 1 clica em chamar Carlos Silva (Sala 02, Dra. Beatriz).
   - Notebook 3 toca o alerta sonoro, destaca Carlos Silva em tela cheia e decrementa a fila de espera para `2`.
2. **Cenário de Desistência/Remoção:**
   - Notebook 1 remove Maria Santos da fila.
   - Notebook 3 atualiza para `1 pessoa aguardando`.
3. **Teste de Falha e Robustez:**
   - Desconectar temporariamente a rede do Notebook 3: o painel deve exibir um badge amarelo/vermelho `Reconectando...` sem quebrar a aplicação.
   - Reconectar o cabo/Wi-Fi: o painel se recupera sozinho sem necessidade de F5.
4. **Teste de Segurança:**
   - Tentar acessar URLs de escrita no Notebook 3: requisições POST são bloqueadas (HTTP 401/403).

---

## 👥 5. Divisão de Tarefas da Equipe

* **Líder Bloco 1 (Arquitetura & Modelagem):** Desenho arquitetural, diagramas de rede, fluxo e especificação técnica.
* **Líder Bloco 2 (Desenvolvimento & Integração):** Configuração do Django, DRF, endpoints, interface do painel e integração do áudio.
* **Líder Bloco 3 (Testes, Demonstração & Resiliência):** Testes unitários do Django, roteiro de testes de rede/falhas e apresentação ao vivo.
