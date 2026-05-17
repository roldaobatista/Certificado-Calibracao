---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/comum/glossario.md
  - docs/arquitetura/cross-cutting/auth-rbac.md
  - docs/conformidade/comum/lgpd-rat.md
---

# Glossário — Módulo Acesso, Segurança e Controle de Usuários (ACS)

> Termos **específicos** deste módulo. Termos transversais (tenant, filial, RLS, KMS) ficam em `docs/comum/glossario.md`.
>
> **Regra anti-duplicação:** hook valida que termo aqui NÃO duplica termo do glossário comum com sentido diferente.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| Usuário | Conta humana com login no sistema, vinculada a 1 tenant e ≥1 filial. | "operador", "conta" (gera confusão com conta financeira) | Quem opera o sistema. | `auth-rbac.md` |
| Perfil de acesso | Conjunto nomeado de permissões (ex: "Atendente"). | "role", "papel", "função" (usar só "Perfil"). | Pacote de acessos que define o que esse usuário pode fazer. | `auth-rbac.md`, `INV-009` |
| Permissão | Direito atômico de executar 1 ação em 1 tela/módulo (ex: "editar cliente"). | "privilégio". | Liberação de UMA ação específica. | `auth-rbac.md` |
| Matriz de permissões | Tabela módulo × tela × ação CRUD configurável por perfil. | "ACL", "policy" (jargão). | Tabela onde admin marca/desmarca o que cada perfil pode. | `auth-rbac.md` |
| Sessão | Janela ativa de login (token + dispositivo + IP + expiração). | "login ativo". | Cada vez que alguém está logado em um dispositivo. | `auth-rbac.md` |
| MFA / 2FA | Segundo fator de autenticação. No Aferê = TOTP. | "verificação em duas etapas" (ok pro Roldão). | Código de 6 dígitos do app autenticador. | `INV-003`, NIST 800-63B |
| TOTP | Time-based One-Time Password (RFC 6238). Código de 6 dígitos que muda a cada 30s. | "Google Authenticator" (é só um app que faz TOTP). | Padrão técnico que o app usa pra gerar o código. | RFC 6238 |
| SMS-OTP | Código por SMS — **proibido** no Aferê (vulnerável a SIM-swap). | — | NÃO existe no Aferê. | `SEC-001`, NIST SP 800-63B |
| Recuperação de senha | Fluxo de redefinir senha via link de uso único por email. | "reset de senha", "esqueci minha senha" (ok pro usuário). | Email com link pra trocar senha. | `auth-rbac.md` |
| Trilha de auditoria | Log imutável (WORM) de toda ação de escrita do sistema. | "log de eventos" (genérico demais), "audit log" (EN). | Histórico de tudo que aconteceu, gravado em pedra. | `INV-001`, ISO 17025 8.4 |
| Histórico de alterações | Versionamento campo-a-campo de um registro crítico (cliente, certificado, NF, lançamento). | "versionamento", "diff". | Foto de antes/depois de cada mudança em um registro. | `INV-001` |
| WORM | Write-Once Read-Many — gravação irretocável. | "imutável" (ok). | Registro que ninguém apaga nem edita, nunca. | `INV-001`, Backblaze B2 |
| Tenant | Empresa cliente do Aferê (isolamento de dados total). | "cliente Aferê" (confunde com cliente final). | Uma empresa que paga assinatura do Aferê. | `docs/comum/glossario.md` (canônico) |
| Filial | Subdivisão operacional dentro de 1 tenant (matriz + filiais). | "unidade", "branch". | Um endereço/operação dentro da mesma empresa. | `docs/comum/glossario.md` (canônico) |
| Admin do Tenant | Perfil máximo dentro de 1 tenant — não atravessa para outros tenants. | "super admin" (confunde com admin global). | Dono/gerente da empresa cliente. | `INV-TENANT-004` |
| Admin Global | Perfil interno do Aferê (Roldão/operação) — acessa metadados de qualquer tenant, **nunca** dados de negócio. | "root", "superuser". | Equipe Aferê — vê só dados de plataforma, nunca o conteúdo do cliente. | `INV-TENANT-004` |
| Titular de Dados Pessoais | Pessoa física cujo dado pessoal (CPF, nome, telefone) está cadastrado em algum tenant. | "data subject", "dono do dado". | A pessoa física que tem direitos LGPD sobre os dados dela. | LGPD Art. 5 V |
| Consentimento LGPD | Manifestação livre e informada do titular para tratamento de dado pessoal por finalidade. | "aceite", "opt-in". | "Eu concordo que vocês usem meu telefone para X". | LGPD Art. 7 I, Art. 8 |
| Base legal LGPD | Fundamento que permite tratar dado pessoal (consentimento, execução contrato, obrigação legal, etc.). | — | Por que estamos autorizados a guardar/usar esse dado. | LGPD Art. 7 |
| Exportação LGPD | Direito do titular receber cópia estruturada dos próprios dados. | "portabilidade". | Pacote ZIP que titular baixa com tudo que tem dele. | LGPD Art. 18 II, V |
| Anonimização | Transformação irreversível que impede identificar o titular preservando integridade contábil. | "pseudonimização" (NÃO é a mesma coisa — pseudonimização é reversível). | Apagar nome/CPF mas manter "houve uma venda" pra contabilidade fechar. | LGPD Art. 5 XI |
| Exclusão LGPD | Apagamento de dado pessoal respeitando retenção legal (Receita 5a, ISO 17025 ~25a). | "deletar conta". | Apagar o dado, mas só depois do prazo legal vencer. | LGPD Art. 18 VI |
| Princípio do menor privilégio | Conceder só a permissão estritamente necessária. | "least privilege". | Ninguém recebe acesso a mais do que precisa pra trabalhar. | `INV-009`, ISO 27001 |
| Anti-enumeração | Mensagens de erro genéricas que não revelam se um email/usuário existe. | — | "Email ou senha incorretos" (sem dizer qual). | `SEC-001`, OWASP ASVS |
| Rate-limit | Limite de quantas tentativas por janela de tempo. | "throttling". | Bloqueio temporário após muitas tentativas erradas. | `SEC-002`, OWASP ASVS |
| 4-eyes (dupla checagem) | Ação destrutiva exige 2 admins confirmando. | "dual approval". | Duas pessoas precisam concordar antes de fazer algo grave. | `INV-001`, prática de governança |

---

## Como esta lista evolui

- Termo novo → adicionar + verificar não conflito com glossário comum.
- Termo migrar para `docs/comum/glossario.md` quando aparecer em ≥2 módulos.
- Mudança de definição → bump CHANGELOG seção "Modificado".

## Convenções

- Termos em PT-BR. Termo técnico-original em inglês inevitável (tenant, TOTP, WORM) inclui tradução de campo.
- Definição em 1 linha. Se precisar mais, criar entrada em `docs/explicacoes/<termo>.md`.
- Origem obrigatória para termos regulados (LGPD, ISO 17025, RFC, NIST, OWASP).
