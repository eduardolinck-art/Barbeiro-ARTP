-- Perfil público vinculado ao auth.users do Supabase (mentorados)
create table perfis (
  id uuid primary key references auth.users(id) on delete cascade,
  nome text not null,
  celular text not null,
  email text not null,
  criado_em timestamptz default now()
);

create table mentores (
  id text primary key,               -- slug do mentor
  nome text not null,
  google_calendar_id text,
  google_refresh_token text,
  google_access_token text,
  token_expiry timestamptz
);

create table cursos (
  id text primary key,               -- ex: 'lidero', 'risco', 'imersao', 'agropulse'
  nome text not null
);

create table agendamentos (
  id uuid primary key default gen_random_uuid(),
  mentorado_id uuid references perfis(id) not null,
  mentor_id text references mentores(id) not null,
  curso_id text references cursos(id) not null,
  data date not null,
  hora time not null,
  status text not null default 'agendado', -- agendado | realizado | cancelado
  protocolo text not null,
  google_event_id text,
  criado_em timestamptz default now()
);

-- Garante, no nível do banco, que dois mentorados não consigam agendar o mesmo
-- horário do mesmo mentor (protege contra corrida de requisições concorrentes).
create unique index agendamentos_slot_unico on agendamentos (mentor_id, data, hora)
  where status = 'agendado';

create table avaliacoes (
  id uuid primary key default gen_random_uuid(),
  agendamento_id uuid references agendamentos(id) unique not null,
  nota int not null check (nota between 0 and 5),
  comentario text,
  criado_em timestamptz default now()
);

-- Seed dos mentores e cursos fixos do negócio
insert into mentores (id, nome) values
  ('cacia', 'Cacia Rosângela Portal'),
  ('carine', 'Carine'),
  ('carolina', 'Carolina da Silva Silveira'),
  ('caroline_bonora', 'Caroline Bonora'),
  ('caroline_dias', 'Caroline Silveira Dias'),
  ('denise', 'Denise Hailliot'),
  ('jane', 'Jane Biondo'),
  ('karem', 'Karem Zapana'),
  ('leonardo', 'Leonardo Bavaresco'),
  ('rosana', 'Rosana Agostini'),
  ('vitor_hugo', 'Vitor Hugo Magni D''Avila');

insert into cursos (id, nome) values
  ('lidero', 'Lidero'),
  ('risco', 'Descomplicando Risco e Crédito'),
  ('imersao', 'Imersão em Crédito'),
  ('agropulse', 'Agropulse');

-- RLS: cada mentorado só vê e edita seus próprios dados
alter table perfis enable row level security;
alter table agendamentos enable row level security;
alter table avaliacoes enable row level security;

-- `mentores` guarda tokens OAuth sensíveis (google_refresh_token, google_access_token).
-- RLS + grant por coluna: anon/authenticated só enxergam id/nome; tokens só via service_role
-- (que ignora RLS), usado apenas pelo backend em app/google_calendar.py.
alter table mentores enable row level security;

create policy "leitura pública de mentores" on mentores
  for select using (true);

revoke select on mentores from anon, authenticated;
grant select (id, nome) on mentores to anon, authenticated;

create policy "perfil próprio" on perfis
  for all using (auth.uid() = id);

create policy "agendamentos próprios" on agendamentos
  for all using (auth.uid() = mentorado_id);

create policy "avaliações dos próprios agendamentos" on avaliacoes
  for all using (
    exists (select 1 from agendamentos a where a.id = agendamento_id and a.mentorado_id = auth.uid())
  );
