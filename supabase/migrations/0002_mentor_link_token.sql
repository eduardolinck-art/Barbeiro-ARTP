-- Link secreto e individual por mentor para /conectar/<mentor_id>/<token>.
-- Evita que qualquer pessoa com o link genérico conecte a agenda errada.
-- NULL = link ainda não gerado para esse mentor (ele não consegue conectar até termos um token).
alter table mentores add column link_token text unique;
