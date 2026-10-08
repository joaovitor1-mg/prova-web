# 📐 Documento de Arquitetura de Software (Bloco 1)
**Sistema Distribuído de Fila de Pronto-Socorro**  
**Disciplina:** Web II • Técnico em Informática  
**Professor:** João Carlos Silva de Souza  
**Equipe:** João Vitor Martinelli, Guilherme Augusto, Sophia / Arthur  

---

## 1. Visão Geral dos Componentes e Distribuição

O sistema adota o padrão **Cliente-Servidor Distribuído** em rede local (LAN), desacoplando totalmente as responsabilidades de entrada de dados, persistência/regras de negócio e exibição pública:

```
                      ┌────────────────────────────────────────┐
                      │              REDE LOCAL                │
                      │         (ex: 200.128.156.0/22)         │
                      └──────────────────┬─────────────────────┘
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        │                                │                                │
        ▼                                ▼                                ▼
┌─────────────────┐             ┌─────────────────┐             ┌─────────────────┐
│   NOTEBOOK 1    │             │   NOTEBOOK 2    │             │   NOTEBOOK 3    │
│ Recepção/Admin  │             │ Servidor Core   │             │ Painel Sala TV  │
├─────────────────┤             ├─────────────────┤             ├─────────────────┤
│ • Operador:     │  HTTP/REST  │ • Host Central  │  HTTP/Poll  │ • Display:      │
│   Sophia        │────────────>│ • João Vitor    │<────────────│   Guilherme     │
│ • Cadastro Fila │             │ • Django + DRF  │             │ • TV em Tela    │
│ • Chamar Próx.  │             │ • SQLite DB     │             │   Cheia (F11)   │
│ • Exclusão/Fim  │             │ • Auth/Sessão   │             │ • Alerta Sonoro │
└─────────────────┘             └─────────────────┘             └─────────────────┘
```

### Onde cada componente executa:
1. **Notebook 2 (Servidor Central - Backend & DB):**
   - Executa a API REST desenvolvida em **Django 6.1** com **Django REST Framework (DRF)**.
   - Escuta na interface `0.0.0.0:8000`, permitindo conexões diretas via IP local.
   - Centraliza o banco de dados **SQLite**, garantindo consistência transacional ACID.
2. **Notebook 1 (Cliente Administrativo / Recepção):**
   - Executa no navegador do operador de recepção.
   - Autenticado via `SessionAuthentication` / Cookies seguros (`csrf_token`).
   - Realiza operações de escrita (`POST`, `DELETE`) para gerenciar pacientes e chamadas.
3. **Notebook 3 (Cliente Público / Painel da TV):**
   - Executa no navegador do monitor voltado para os pacientes na sala de espera.
   - Acesso estritamente **somente leitura** (`GET /api/painel/`), sem credenciais administrativas.
   - Comunica-se por **Polling Inteligente** (a cada 2 segundos) e dispara síntese sonora local via **Web Audio API**.

---

## 2. Fluxo de uma Chamada de Paciente

O ciclo completo de uma chamada segue o seguinte fluxo temporal:

```
Recepção (Notebook 1)             Servidor Core (Notebook 2)           Painel TV (Notebook 3)
         │                                    │                                    │
         │  1. POST /api/fila/chamar-proximo/ │                                    │
         │ ──────────────────────────────────>│                                    │
         │                                    │                                    │
         │                                    │ 2. Consulta banco (SQLite)         │
         │                                    │    Prioridade > Ordem de chegada   │
         │                                    │ 3. Atualiza Paciente:              │
         │                                    │    status='chamado', sala, medico  │
         │                                    │    chamado_em = now()              │
         │                                    │                                    │
         │  4. Retorna HTTP 200 JSON          │                                    │
         │ <──────────────────────────────────│                                    │
         │                                    │                                    │
         │                                    │    5. GET /api/painel/ (polling)   │
         │                                    │ <──────────────────────────────────│
         │                                    │                                    │
         │                                    │    6. HTTP 200 com novo chamado    │
         │                                    │ ──────────────────────────────────>│
         │                                    │                                    │
         │                                    │                                    │ 7. Detecta novo ID
         │                                    │                                    │ 8. Toca Alerta Sonoro
         │                                    │                                    │    (Web Audio API)
         │                                    │                                    │ 9. Animação Visual
```

---

## 3. Modelo de Informações (Dados Manipulados)

A entidade central do domínio hospitalar é o **`Paciente`**, modelada para atender a todo o ciclo de vida na unidade:

### Dicionário de Dados (`Paciente`):
| Campo | Tipo | Descrição | Regra / Choices |
|---|---|---|---|
| `id` | Integer (PK) | Identificador único incremental | Gerado automaticamente |
| `nome` | Varchar(150) | Nome completo do paciente | Obrigatório |
| `prioridade` | Varchar(20) | Grau de prioridade médica | `'normal'`, `'preferencial'` |
| `status` | Varchar(20) | Estado atual na unidade | `'aguardando'`, `'chamado'`, `'finalizado'`, `'cancelado'` |
| `sala` | Varchar(50) | Consultório ou sala de destino | Preenchido no momento da chamada |
| `medico` | Varchar(120) | Nome do médico responsável | Preenchido no momento da chamada |
| `criado_em` | DateTime | Timestamp de chegada | `auto_now_add=True` |
| `chamado_em` | DateTime | Timestamp do chamado para atendimento | Atualizado quando o médico chama |
| `finalizado_em`| DateTime | Timestamp da conclusão do atendimento | Atualizado na liberação/desistência |

---

## 4. Tecnologias Escolhidas e Justificativas

| Tecnologia | Função no Projeto | Justificativa | Alternativas Descartadas |
|---|---|---|---|
| **Django + DRF** | Backend REST & Servidor Web | Requisito da prova. Oferece ORM robusto, autenticação nativa, serializadores e painel administrativo prontos e seguros. | Flask / FastAPI (não atendiam à base exigida de Django). |
| **SQLite** | Banco de Dados Relacional | Embutido no Python, zero configuração de servidor externo, ideal para demonstração local estável e com suporte total a transações ACID. | PostgreSQL / MySQL (adicionariam complexidade desnecessária de setup de rede e credenciais). |
| **Polling HTTP Inteligente (2s)** | Comunicação em Tempo Real | Extremamente resiliente a falhas de rede, sem necessidade de servidores ASGI complexos ou Redis, com reconexão automática e nativa pelo `fetch()`. | WebSockets / Django Channels + Redis (descartados por risco de falha de conexão e dependências adicionais no ambiente de apresentação). |
| **Web Audio API** | Alerta Sonoro | Sintetiza frequências sonoras hospitalares (duas notas: 659Hz e 523Hz) diretamente no browser. Independente de carregamento de arquivos MP3 ou falhas de codec. | Arquivo `.mp3` externo (descartado pelo risco de erro de download de arquivo estático na rede). |
| **Tailwind CSS (CDN)** | Interface dos Frontends | Agilidade de estilização com layout responsivo, escuro (Dark Mode) de alto contraste e legibilidade à distância para telas de TV. | CSS puro do zero ou Bootstrap pesado. |

---

## 5. Padrões de Projeto e Arquiteturais Adotados

1. **Cliente-Servidor (Client-Server):** Desacoplamento explícito de nós: servidor provê endpoints e dados; clientes provêm interfaces de usuário.
2. **REST (Representational State Transfer):** Uso semântico de verbos HTTP (`GET`, `POST`, `DELETE`) e códigos de status (`200 OK`, `201 Created`, `401 Unauthorized`, `404 Not Found`).
3. **MVT (Model-View-Template):** Estrutura canônica do Django para organização de código e renderização das páginas.
4. **Data Transfer Object (DTO) / Serializer:** Utilização de Serializers do DRF para validar payloads de entrada e filtrar campos de saída em conformidade com a LGPD (Princípio da Necessidade).

---

## 6. Divisão de Responsabilidades da Equipe

* **Líder Bloco 1 (Arquitetura e Modelagem):** **João Vitor Martinelli**
  * Desenho da arquitetura distribuída, fluxo temporal de chamada, modelo relacional e especificações de rede.
* **Líder Bloco 2 (Desenvolvimento dos Artefatos):** **Guilherme Augusto & Sophia / Arthur**
  * Implementação dos endpoints do backend, criação da interface pública da TV (`painel_publico.html`), tela de recepção (`admin_painel.html`) e integração com áudio.
* **Líder Bloco 3 (Testes e Demonstração):** **Toda a Equipe**
  * Execução dos testes automatizados (`python manage.py test`), demonstração do roteiro ao vivo em 3 máquinas e simulação de teste de desconexão de rede.
