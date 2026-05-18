---
owner: Roldão
revisado-em: 2026-05-18
status: stable
modulo: equipamentos
dominio: suporte-plataforma
versao: 2
---

# Glossário — Equipamentos do cliente

> Termos específicos deste módulo. Transversais ficam em `docs/comum/glossario.md`.
> **v2 (2026-05-18):** acréscimos de termos da auditoria 4 subagentes (RecebimentoEquipamento, dual-mode, perfil_tenant_no_cadastro, motivos versionamento).

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| Equipamento do cliente | Instrumento físico que o tenant calibra para um cliente final | "produto", "item" | Ativo do cliente cadastrado no Aferê | OP17, INV-025 |
| TAG do equipamento | Identificador interno + único por tenant (humano-legível) | "código", "ID externo" | Etiqueta colada no instrumento | OP17, INV-049 |
| QR Code do equipamento | Código 2D impresso na etiqueta apontando para a ficha do equipamento | "código de barras" | Acesso rápido via leitor mobile | OP17, INV-051 |
| Hash assinado do QR | Token opaco HMAC-SHA256 com `tenant_id` no payload + KMS_qr_secret | "código", "id curto" | Identificador da URL `/v1/qr/{hash}` — não previsível, não enumerável | INV-051 |
| Número de série (NS) | Identificador do fabricante, gravado no equipamento | "serial number" cru | Identificação original do fabricante | Fabricante |
| Ficha 360° do equipamento | Visão consolidada: dados + histórico de calibração + OS abertas + recebimentos + eventos | "ficha técnica" só | Tela 3 do módulo | OP17 |
| Dual-mode (resolução QR) | Endpoint `/v1/qr/{hash}` decide entre Escopo A (mesmo tenant), B (outro tenant), C (anônimo) e retorna payload diferente | "público autenticado" (impreciso) | INV-051; allowlist em `qr-publico-allowlist.md` | tech-lead B2 |
| Histórico imutável | Linha do tempo de eventos do equipamento gravados em `audit_trail.eventos` (WORM + hash chain) | "log" | Eventos não-editáveis | INV-001, INV-025 |
| Versionamento de equipamento | Registro de mudança de atributo descritivo após emissão (cria nova versão, preserva antiga) | "edição direta" | Snapshot antigo permanece no certificado anterior | INV-025 |
| Motivo de mudança (enum) | Categoria controlada da mudança em `EquipamentoVersao`: correcao_cadastro_inicial / reparo_reclassificou / recalibracao_revelou_drift_permanente / troca_componente_principal / reidentificacao_fabricante / outros | "razão", "comentário livre" | Enum forçado pra evitar fraude metrológica | RBC B7 |
| Perfil do tenant no cadastro | Snapshot imutável de `perfil_tenant_no_momento_cadastro` (A/B/C/D) gravado quando equipamento é cadastrado — anti-downgrade | — | Equipamento criado em A continua regido por A mesmo se tenant rebaixar | RBC B4 |
| Vínculo cliente-equipamento | Relação entre equipamento e cliente final; `cliente_atual_id` (mutável via transferência) vs `cliente_id_original_hash` (imutável, salgado por tenant) | "dono", "owner" | Quem é o titular do equipamento agora vs quem cadastrou originalmente | OP17, advogado B1 |
| Hash do cliente original | `SHA-256` salgado por tenant aplicado ao `cliente_id` original — preserva rastreabilidade ISO 17025 cl. 8.4 mesmo se cliente original for crypto-shredded por LGPD art. 18 VI | — | Forma de manter histórico sem PII reidentificável | advogado B1, US-CLI-005 |
| Status do equipamento | Estado operacional: ativo / inativo_temporario / aposentado / em_calibracao_lab / sucata / orfao_pendente_decisao / extraviado | "situação" | Filtro de listagem Tela 1 | OP17, RBC C5 |
| Equipamento órfão | Equipamento cujo `cliente_atual_id` aponta pra cliente inativo > 12 meses | "abandonado" | Status `orfao_pendente_decisao` — exige decisão do suporte tenant | RBC C4 |
| EquipamentoRecebimento | Entidade que registra cada entrada física do equipamento no laboratório com condição visual + foto + decisão sobre anomalias (ISO 17025 cl. 7.4) | "ordem de entrada" | Entrada física pra calibração | RBC B1 |
| status_fluxo_lab | Máquina de estados ≥6 fases do equipamento dentro do laboratório: aguardando_recebimento → recebido_pendente_inspecao → em_inspecao_visual → aguardando_calibracao → em_calibracao → aguardando_aprovacao_tecnica → aguardando_devolucao → devolvido. Alternativos: nao_conformidade_recebimento, nao_conformidade_calibracao | "em calibração" (genérico demais) | Onde o equipamento está fisicamente | RBC B3 |
| Condição visual de chegada | Enum: integro / amassado / lacre_violado / contaminado / sem_acessorios / outros — exige foto em perfil A | — | Defesa do lab contra "veio quebrado" | RBC B2, ISO 17025 cl. 7.4.4 |
| Termo de transferência | Documento aceito pelo cedente e cessionário antes de mudar `cliente_atual_id` — Lei 14.063/2020 art. 4º I (assinatura simples MVP-1) ou art. 4º II/III (avançada/qualificada V2) | "autorização", "permissão" | Aceite duplo obrigatório (US-EQP-004) | advogado B2 |
| Notificação de sucatamento | E-mail automático ao cliente final quando equipamento é sucateado tendo cert vigente — evento `equipamento.sucateado_com_certificado_vigente` | — | RBC B5 — cliente sabe que cert continua histórico mas equip não está em uso | RBC B5 |
| Porta CertificadoQueryService | Interface domain que o módulo equipamentos usa pra perguntar ao módulo certificados se há cert emitido/vigente — Marco 2 usa adapter `EmptyCertificadoQueryService` (stub) | — | Anti-acoplamento entre módulos antes do módulo `certificados` existir | tech-lead B5, ADR-0007 |
| Porta OSQueryService | Análoga — pergunta ao módulo `os` se há OS aberta — stub `EmptyOSQueryService` Marco 2 | — | — | tech-lead B5 |
| port-binding-validator | Hook pre-release que bloqueia ir pra produção se alguma porta estiver bindada em `EmptyXxx` em `settings.production` | — | Anti "esqueci de plugar" | tech-lead B5 |

---

## Como esta lista evolui

- Termo novo → adicionar + verificar conflito com glossário comum.
- Termo descontinuado → marcar `@deprecated` + janela 3 meses.
- Nova versão de modelo → bump nesta tabela + revisão dos 4 subagentes.
