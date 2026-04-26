-- Migration: MFA credentials, recovery codes, session auth level
-- Owner: backend-api + db-schema
-- Data: 2026-04-27

-- Nível de autenticação na sessão (full | partial)
ALTER TABLE public.app_sessions
  ADD COLUMN IF NOT EXISTS auth_level VARCHAR(16) NOT NULL DEFAULT 'full';

-- Tabela de credenciais MFA (TOTP)
CREATE TABLE IF NOT EXISTS public.mfa_credentials (
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  type VARCHAR(16) NOT NULL,
  secret VARCHAR(64) NOT NULL,
  verified BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ(6) NOT NULL,
  CONSTRAINT mfa_credentials_pkey PRIMARY KEY (id),
  CONSTRAINT mfa_credentials_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.app_users(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS mfa_credentials_user_id_idx ON public.mfa_credentials(user_id);

-- Tabela de códigos de recuperação MFA
CREATE TABLE IF NOT EXISTS public.mfa_recovery_codes (
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  code_hash TEXT NOT NULL,
  used_at TIMESTAMPTZ(6),
  created_at TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT mfa_recovery_codes_pkey PRIMARY KEY (id),
  CONSTRAINT mfa_recovery_codes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.app_users(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX IF NOT EXISTS mfa_recovery_codes_user_id_idx ON public.mfa_recovery_codes(user_id);
