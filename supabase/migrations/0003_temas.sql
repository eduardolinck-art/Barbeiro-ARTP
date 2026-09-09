-- Fluxo em cascata: Curso -> Tema -> Mentor. Cada tema pertence a um curso,
-- e cada mentor cobre um ou mais temas (não necessariamente do mesmo curso).
create table temas (
  id text primary key,
  curso_id text references cursos(id) not null,
  nome text not null
);

create table mentor_temas (
  mentor_id text references mentores(id) not null,
  tema_id text references temas(id) not null,
  primary key (mentor_id, tema_id)
);

-- Temas fictícios de exemplo, distribuídos entre os 4 cursos.
insert into temas (id, curso_id, nome) values
  ('lidero_gestao_equipes', 'lidero', 'Gestão de Equipes'),
  ('lidero_comunicacao', 'lidero', 'Comunicação Assertiva'),
  ('lidero_estrategia', 'lidero', 'Liderança Estratégica'),
  ('risco_analise', 'risco', 'Análise de Crédito'),
  ('risco_gestao', 'risco', 'Gestão de Risco'),
  ('risco_recuperacao', 'risco', 'Recuperação de Crédito'),
  ('imersao_fundamentos', 'imersao', 'Fundamentos de Crédito'),
  ('imersao_pj', 'imersao', 'Crédito para PJ'),
  ('imersao_pf', 'imersao', 'Crédito para PF'),
  ('agro_rural', 'agropulse', 'Crédito Rural'),
  ('agro_gestao', 'agropulse', 'Gestão do Agronegócio'),
  ('agro_sustentabilidade', 'agropulse', 'Sustentabilidade no Campo');

-- Atribuição fictícia e aleatória de mentores a temas (dado de exemplo, ajustar depois
-- com a atribuição real do negócio). Todo mentor cobre pelo menos um tema.
insert into mentor_temas (mentor_id, tema_id) values
  ('karem', 'lidero_gestao_equipes'),
  ('caroline_bonora', 'lidero_comunicacao'),
  ('carine', 'lidero_comunicacao'),
  ('carolina', 'lidero_estrategia'),
  ('leonardo', 'lidero_estrategia'),
  ('leonardo', 'risco_analise'),
  ('denise', 'risco_gestao'),
  ('jane', 'risco_recuperacao'),
  ('rosana', 'imersao_fundamentos'),
  ('caroline_dias', 'imersao_pj'),
  ('karem', 'imersao_pj'),
  ('cacia', 'imersao_pf'),
  ('carine', 'agro_rural'),
  ('vitor_hugo', 'agro_gestao'),
  ('carolina', 'agro_gestao'),
  ('rosana', 'agro_sustentabilidade');

-- Agendamento passa a registrar também o tema escolhido (o curso continua
-- guardado, derivável do tema, mas mantido para facilitar consultas diretas).
alter table agendamentos add column tema_id text references temas(id);
