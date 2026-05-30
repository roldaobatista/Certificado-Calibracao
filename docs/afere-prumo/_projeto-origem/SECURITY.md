---
owner: roldao
revisado-em: 2026-05-28
status: draft
idioma: pt-BR
limite-linhas: 250
proposito: canal externo de divulgação de vulnerabilidades — SLA, severidade, safe-harbor, MFA, rotação de segredos
---

<!--
template: SECURITY.md
uso: copiar para a raiz do repositório.
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §C0
-->

# SECURITY — Aferê Prumo

## Canal de divulgação

Reportar vulnerabilidade por e-mail para **<security@exemplo.com>**.

NÃO abrir issue pública para falhas exploráveis. NÃO discutir em chat público antes da correção.

Inclua no relato:
- Descrição do problema e impacto observado.
- Passo-a-passo de reprodução.
- Versão / commit afetado.
- Se houver, prova de conceito mínima.

## Classificação de severidade

Tabela inspirada no CVSS (sistema padrão da indústria), simplificada para uso diário.

| Severidade | Critério | Prazo de correção (SLA — prazo máximo de atendimento) |
|---|---|---|
| **CRÍTICO** | Explorável remotamente sem autenticação **ou** ganho de privilégio máximo (administrador/root) **ou** vazamento de dados sensíveis (LGPD Art. 5, II) | 24 horas |
| **ALTO** | Ganho parcial de privilégio (escalada limitada) **ou** indisponibilidade do serviço (DoS) **ou** vazamento de dado não-sensível em volume | 7 dias corridos |
| **MÉDIO** | Vazamento de informação técnica não-sensível (versão de biblioteca, caminhos internos, mensagens de erro detalhadas) | 30 dias corridos |
| **BAIXO** | Hardening / melhoria de defesa em profundidade, sem caminho de exploração concreto | 90 dias corridos |

> **SLA** significa "prazo máximo de atendimento" — o tempo entre triagem e correção em produção.

## SLA de resposta inicial

| Etapa | Prazo |
|---|---|
| Acusar recebimento | 72 horas |
| Triagem (severidade + plano) | 7 dias corridos |
| Correção | conforme tabela de severidade acima |

## Chave PGP (opcional)

Fingerprint: `<XXXX XXXX XXXX XXXX XXXX  XXXX XXXX XXXX XXXX XXXX>`
Chave pública: `<URL ou arquivo .asc no repositório>`

<!-- Remover esta seção se o projeto não publica chave PGP. -->

## Versões com suporte ativo

| Linha | Status | Recebe correção de segurança? |
|---|---|---|
| <linha-atual> | em produção | sim |
| <linha-anterior> | manutenção | sim, até 2026-05-28 |
| <linha-antiga> | end-of-life | não |

## Rotação de segredos

Segredos = senhas, tokens de API, chaves privadas, credenciais de banco, chaves de assinatura.

| Tipo de segredo | Frequência mínima de rotação | Responsável | Processo |
|---|---|---|---|
| Token de API de provedor externo | a cada 90 dias | owner do serviço | gerar novo no painel → atualizar cofre → revogar antigo após 24h |
| Senha de banco de dados de produção | a cada 180 dias | owner de infraestrutura | rotação coordenada com janela de manutenção |
| Chave de assinatura de release | anual | mantenedor principal | gerar nova chave → publicar fingerprint → revogar antiga |
| Credencial pessoal de mantenedor | sob suspeita de comprometimento | o próprio mantenedor | revogar imediatamente, recriar, comunicar equipe |

Segredos são armazenados em cofre (`<vault/1password/aws-secrets-manager>`), nunca em código, nunca em `.env` commitado.

## Gestão de dependências

- **Dependabot/Renovate**: configurado no repositório para abrir PR automaticamente quando dependência tem atualização de segurança.
- **SBOM** (Software Bill of Materials — lista de tudo que o projeto importa): **OBRIGATÓRIO** a cada release em `dist/sbom.json` (formato CycloneDX, gerado por `syft`). Pipeline de CI deve falhar se SBOM ausente ou vazio em release.
- **Revisão de CVE** (vulnerabilidade pública catalogada): revisão semanal de novas CVEs nas dependências diretas; mensal para transitivas.
- Dependências sem manutenção há > 12 meses são marcadas como débito técnico e substituídas no próximo ciclo.

## MFA dos mantenedores

**Obrigatório** para qualquer pessoa com permissão de push direto, merge em branch protegida ou publicação de pacote:

- Autenticação multi-fator (MFA) ativa na conta da plataforma de código (GitHub/GitLab/Bitbucket).
- MFA ativa em qualquer conta com acesso ao cofre de segredos.
- Chave SSH protegida por passphrase OU armazenada em hardware (YubiKey, Secure Enclave).

Mantenedor sem MFA tem acesso de push **revogado** até regularizar.

## Secrets scanning no CI

O pipeline de integração contínua roda escaneamento automático de segredos em **todo commit**:

- Ferramenta canônica: **`gitleaks`** (multiplataforma, instalação simples, ativa em pre-commit + CI). Trufflehog é alternativa aceita apenas se documentada em ADR.
- Falha o build se detectar padrão de credencial (token, chave privada, senha).
- Checklist de configuração inicial (marcar antes de tornar o repositório público):
  - [ ] Histórico do repositório varrido com `gitleaks detect --no-banner --redact --log-opts="--all"` antes de tornar público.
  - [ ] Vazamentos antigos tratados (rotação do segredo + reescrita de histórico via `git filter-repo` OU aceite documentado em ADR).
  - [ ] Pipeline de CI configurado para falhar build em commit novo com padrão de credencial.

Em caso de vazamento detectado: rotação **imediata** do segredo, mesmo antes de remover do histórico.

## Modelo de ameaças

Threat model formal vive em [`docs/seguranca/threat-model.md`](./docs/seguranca/threat-model.md) (template em `templates/threat-model.template.md`). Cobre STRIDE por componente, atacantes, trust boundaries, attack surface, mitigações vinculadas a INVs e auditores. Revisão obrigatória anual.

## Política de dependências

Critérios de aceitação de pacote novo, pinning, max-age, SBOM e scanning de CVE vivem em [`docs/seguranca/dependency-policy.md`](./docs/seguranca/dependency-policy.md) (template em `templates/dependency-policy.template.md`).

## Política de criptografia e de chaves

Algoritmos obrigatórios em repouso e em trânsito, cifras proibidas e hash de senha vivem em [`docs/seguranca/criptografia-policy.md`](./docs/seguranca/criptografia-policy.md) (template em `templates/criptografia-policy.template.md`). O ciclo de vida das chaves (geração, rotação, revogação, custódia em KMS/HSM) vive em [`docs/seguranca/key-management-policy.md`](./docs/seguranca/key-management-policy.md) (template em `templates/key-management-policy.template.md`). A rotação de segredos descrita acima é o resumo operacional dessas duas políticas.

## Vinculação com REGRAS-INEGOCIAVEIS

Este SECURITY.md é o canal externo (público) de segurança. As regras **internas** que sustentam essa política vivem em [`REGRAS-INEGOCIAVEIS.md`](./REGRAS-INEGOCIAVEIS.md):

- **INV-AGENT-008** — PII nunca em logs nem em código fonte (sustentado por `hook-secrets-scanner`).
- **INV-AGENT-009** — credenciais nunca commitadas (sustentado por `hook-secrets-scanner` + CI gitleaks).
- **SEC-001..NNN** — requisitos de segurança específicos do projeto (ver `docs/seguranca/requisitos-sec.md`).

## Política de divulgação coordenada

- **Embargo padrão**: 90 dias entre o aceite do report e a publicação pública da falha **ou** acordo direto com o reporter (o que for mais curto, exceto em caso de exploração ativa no mundo real, quando publicamos imediatamente com correção pronta).
- **Safe-harbor**: não tomamos medida legal contra pesquisador de segurança que reporte de boa-fé, respeite o embargo e não acesse dados além do necessário para demonstrar o problema.
- **CVE**: solicitamos identificador CVE quando a falha afeta versão pública e tem impacto material.
- **Crédito**: o reporter é creditado no aviso público, exceto se preferir anonimato.

## O que NÃO é considerado vulnerabilidade

- Falhas em dependência já com CVE público sem caminho de exploração no nosso uso.
- Falta de header de segurança em endpoint puramente interno / sem dado sensível.
  - **endpoint** = porta de entrada do sistema (uma URL que aceita requisição).
- Ataques que exigem acesso físico ao dispositivo do usuário.
- Engenharia social fora do nosso domínio.
- Ausência de **rate-limiting** (limite de quantas requisições por minuto) em endpoint público de leitura sem dado pessoal.
- Bug de UX que não leva a vazamento, escalada de privilégio ou perda de dado.

Em dúvida, reportar mesmo assim — triagem decide.
