-- Init script para docker-compose dev
-- Cria a role afere_app com LOGIN para que o serviço API possa conectar via DATABASE_APP_URL.
-- Em produção, esta role deve ser criada pelo DBA/IaC com senha gerenciada por secrets manager.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'afere_app') THEN
    CREATE ROLE afere_app LOGIN PASSWORD 'afere_app' NOINHERIT;
  ELSE
    ALTER ROLE afere_app WITH LOGIN PASSWORD 'afere_app';
  END IF;
END
$$;

-- Permite que o owner 'afere' assuma a role afere_app se necessário para grants/debug
GRANT afere_app TO afere;
