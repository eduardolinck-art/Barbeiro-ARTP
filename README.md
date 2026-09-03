# Mentoria App

Sistema de agendamento de mentorias individuais, com 3 abas (Agendamento, Histórico de encontros,
Perfil), autenticação via Supabase e integração real com o Google Agenda.

**Stack:** [Flet](https://flet.dev) (UI web em Python) · [Supabase](https://supabase.com) (Postgres + Auth) ·
Google Calendar API · deploy no [Render](https://render.com) a partir do GitHub.

## Estrutura

```
main.py                  # entrada do app Flet (rotas: /login, /app, /oauth2callback, /conectar-mentores)
app/
  config.py              # leitura das variáveis de ambiente
  supabase_client.py      # client Supabase (um por sessão de usuário + client admin)
  google_calendar.py      # freebusy, criação de evento, refresh de token, OAuth
  models.py                # dataclasses (Perfil, Mentor, Curso, Agendamento, Avaliacao)
  repositories/             # CRUD de cada tabela
  views/                     # as 4 telas (auth, agendamento, histórico, perfil)
  components/                 # modais reutilizáveis e o componente de estrelas
supabase/migrations/0001_init.sql   # schema completo do banco
```

## 1. Rodando localmente

Pré-requisitos: Python 3.11+.

```bash
python -m venv venv
venv\Scripts\activate            # Windows
pip install -r requirements.txt
```

Copie `.env.example` para `.env` e preencha as variáveis (veja as seções 2 e 3 abaixo para saber
onde conseguir cada uma).

```bash
python main.py
```

O app abre no navegador em `http://localhost:8550`.

## 2. Criar o projeto Supabase e rodar a migration

1. Crie um projeto em [supabase.com](https://supabase.com) (ou use um existente).
2. Vá em **Project Settings → API** e copie:
   - `Project URL` → variável `SUPABASE_URL`
   - `anon public` key → variável `SUPABASE_ANON_KEY`
   - `service_role` key → variável `SUPABASE_SERVICE_ROLE_KEY` (fique atento: essa chave ignora
     as regras de segurança do banco — nunca a exponha no frontend nem em repositório público)
3. Ative **Email confirmations** em **Authentication → Providers → Email** conforme sua preferência
   (com confirmação ativada, o cadastro só libera login após o usuário clicar no link do e-mail).
4. Rode a migration `supabase/migrations/0001_init.sql`:
   - Mais simples: abra **SQL Editor** no painel do Supabase, cole o conteúdo do arquivo e execute.
   - Alternativa: instale o [Supabase CLI](https://supabase.com/docs/guides/cli) e rode
     `supabase db push` apontando para o projeto.

A migration cria as tabelas `perfis`, `mentores`, `cursos`, `agendamentos`, `avaliacoes`, já com
Row Level Security e os mentores/cursos iniciais do negócio cadastrados.

## 3. Criar as credenciais OAuth no Google Cloud Console

1. Acesse [console.cloud.google.com](https://console.cloud.google.com) e crie um projeto (ou
   reutilize um existente).
2. Em **APIs e serviços → Biblioteca**, ative a **Google Calendar API**.
3. Em **APIs e serviços → Tela de consentimento OAuth**:
   - Tipo de usuário: Externo (ou Interno, se usar Google Workspace).
   - Preencha nome do app, e-mail de suporte, domínios autorizados.
   - Em Escopos, adicione `https://www.googleapis.com/auth/calendar`.
   - Adicione os mentores como **usuários de teste** enquanto o app não estiver "publicado" no
     Google (senão o consentimento expira e precisa ser refeito com frequência).
4. Em **Credenciais → Criar credenciais → ID do cliente OAuth**:
   - Tipo de aplicativo: **Aplicativo da Web**.
   - Em **URIs de redirecionamento autorizados**, adicione:
     - `http://localhost:8550/oauth2callback` (para testar localmente)
     - `https://SEU-APP.onrender.com/oauth2callback` (produção, depois que o Render gerar o domínio)
   - Copie o **Client ID** e o **Client Secret** → variáveis `GOOGLE_CLIENT_ID` e
     `GOOGLE_CLIENT_SECRET`.
5. Defina `GOOGLE_REDIRECT_URI` igual à URI de redirecionamento que você quer usar no momento
   (local ou produção — precisa bater exatamente com uma das cadastradas no passo anterior).

### Conectando a agenda de cada mentor

Depois do app publicado (ou rodando localmente), acesse `/conectar-mentores`. Essa página lista
os mentores cadastrados com um botão "Conectar Google Agenda" — cada mentor deve clicar no
próprio botão, fazer login com a conta Google dele e autorizar o acesso. Isso grava o
`refresh_token` dele na tabela `mentores`, usado depois para consultar disponibilidade e criar
eventos.

## 4. Deploy: GitHub → Render

1. Suba o repositório para o GitHub (branch `main` = produção).
2. No [Render](https://dashboard.render.com), **New → Web Service**, conecte o repositório GitHub.
3. Render detecta o `render.yaml` automaticamente. Se pedir para confirmar manualmente:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main.py`
4. Em **Environment**, preencha as variáveis (`SUPABASE_URL`, `SUPABASE_ANON_KEY`,
   `SUPABASE_SERVICE_ROLE_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`,
   `GOOGLE_REDIRECT_URI` com a URL final do Render + `/oauth2callback`). O Render já injeta a
   variável `PORT` automaticamente.
5. Deploy automático: qualquer push na branch conectada (recomenda-se `main`) dispara um novo
   deploy.
6. Depois do primeiro deploy, volte no Google Cloud Console e confirme que a URI de redirecionamento
   de produção (`https://SEU-APP.onrender.com/oauth2callback`) está cadastrada.

## Fluxo de negócio implementado

- Mentorado se cadastra/faz login (Supabase Auth).
- Agenda uma mentoria escolhendo mentor (ou "sem preferência"), curso e um horário realmente
  livre na agenda do mentor no Google — dois mentorados nunca conseguem ocupar o mesmo horário do
  mesmo mentor (garantido por um índice único no banco).
- Ao confirmar, um evento é criado na agenda real do mentor e um protocolo é gerado.
- Depois que a data passa, o encontro aparece no Histórico, onde pode ser avaliado de 0 a 5
  estrelas.
- Perfil permite editar nome/celular/e-mail e sair da conta.
