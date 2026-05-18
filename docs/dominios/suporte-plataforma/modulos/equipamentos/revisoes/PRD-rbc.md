---
owner: consultor-rbc-iso17025 (subagente)
revisado-em: 2026-05-18
status: stable
escopo: PRD draft equipamentos — review ISO 17025 + NIT-DICLA + CGCRE
---

# Revisão ISO/IEC 17025 + NIT-DICLA — PRD `equipamentos` (DRAFT v1)

> **Disclaimer:** subagente IA sem credencial CGCRE. Revisão consultiva baseada em ISO/IEC 17025:2017, NIT-DICLA-021, NIT-DICLA-030 rev. 15, NIT-DICLA-016, práticas de supervisão CGCRE. Antes da supervisão real, consultor humano credenciado revisa.

## (A) Conformidade ISO 17025 — gaps

A norma cobre o item objeto de calibração em **três cláusulas inter-relacionadas** que o PRD trata parcialmente:

1. **Cl. 7.4 (Manuseio de itens)** — exige registrar condição de chegada, anomalias visíveis, integridade do lacre/proteção, foto e responsabilidade pelo transporte. **PRD NÃO COBRE.** Não há `EquipamentoRecebimento`.
2. **Cl. 7.8 (Relatórios)** + 7.8.2.1.c — exige amarrar inequivocamente o item à sua identificação física. PRD cobre TAG + NS, mas falta padronização (NIT-DICLA-021 §5.2 espera procedimento documentado).
3. **Cl. 7.5 + 8.4** — alteração entre recebimento e emissão tem que ter rastro completo. Motivo não é enum controlado — gap.
4. **Cl. 7.4.4 + 7.4.5 (Anomalia no item)** — laboratório precisa decidir e registrar antes de prosseguir. Status `em_calibracao` é genérico demais.
5. **Cl. 7.10 (Trabalho não conforme)** — equip com NC durante calibração precisa fluxo de comunicação + bloqueio. PRD não trata.
6. **Cl. 4.1 (Imparcialidade) + 7.8.2.1.j** — equipamento muda de cliente compromete rastreabilidade da cadeia anterior; cert emitido para Cliente X não migra automaticamente para Cliente Y.

## (B) BLOQUEADORES

### B1 — Falta entidade `RecebimentoEquipamento` (ISO 17025 cl. 7.4.2 + 7.4.3)
Cada entrada física no laboratório é evento auditável: data/hora, recebedor, identificação física (lacres, embalagem), fotos, condição declarada vs. observada, identificação interna provisória (ID de bancada).

### B2 — Foto + condição visual de chegada OBRIGATÓRIOS (cl. 7.4.4)
Sem foto + checklist visual no recebimento, lab não se defende de "meu equipamento veio quebrado". Em A é pedido sistemático CGCRE.

Campos: `condicao_visual_chegada` (enum: integro/amassado/lacre_violado/contaminado/outros), `fotos_chegada[]` (≥1 obrigatória em perfil A; opcional B/C/D), `anomalias_observadas`, `decisao_apos_anomalia` (enum: prosseguir/contatar_cliente/recusar).

### B3 — Status `em_calibracao` não cobre o fluxo real (cl. 7.4 + 7.10)
Substituir por máquina de estados ≥6 fases:
- `aguardando_recebimento` → `recebido_pendente_inspecao` → `em_inspecao_visual` → `aguardando_calibracao` → `em_calibracao` → `aguardando_aprovacao_tecnica` → `aguardando_devolucao` → `devolvido`
- Caminhos alternativos: `nao_conformidade_recebimento`, `nao_conformidade_calibracao` — saem da máquina principal.

### B4 — INV-025 absoluta em A, configurável em B/C/D — falta controle anti-downgrade
- **Quem rebaixa perfil do tenant?** Apenas Suporte Aferê com A3 + justificativa ≥50 chars + audit em WORM.
- **Equipamento criado em perfil A NÃO pode ter sua história editada se tenant rebaixar pra B depois.** Imutabilidade pós-cert é por equipamento, não por perfil-corrente. **Modelo precisa congelar perfil-no-momento-da-emissão.**
- Adicionar campo: `perfil_tenant_no_momento_cadastro: enum {A,B,C,D}` — IMUTÁVEL (snapshot anti-downgrade).
- Hook: extensão `INV-checker` pra detectar UPDATE em equip com cert A emitido, ainda que tenant em B.

### B5 — Sucatar com cert ATIVO sem notificação ao cliente (cl. 7.10 + 4.2)
Se equip foi sucateado antes do vencimento, cliente precisa ser notificado formalmente.
- Pré-condição adicional: se `Certificado.status=emitido AND data_proxima_calibracao > now()` → exigir confirmação dupla + notificação automática (e-mail) ao cliente final + evento `Equipamento.sucateado_com_certificado_vigente` em WORM.

### B6 — Transferência entre clientes sem invalidar/segregar certs anteriores (cl. 4.2 + 7.8 + LGPD art. 6º)
ISO 17025 cl. 4.2 (confidencialidade): dados do Cliente A não podem vazar pro Cliente B só porque equipamento mudou de dono. **Cert emitido pra Cliente A continua sendo registro do Cliente A** — não "transfere" automaticamente.
- Regra: `cliente_id_original` permanece imutável (INV-025), mas **histórico de certs anteriores fica oculto na ficha 360° do Cliente B** (visível apenas se Cliente A consentir).
- Cliente B vê: "equipamento adquirido de terceiro em DD/MM/AAAA — histórico anterior preservado mas confidencial — solicitar ao vendedor".

### B7 — `classe_exatidao` e `faixa_medicao` versionáveis sem motivo controlado
Mudança desses dois em equip real é evento metrológico raríssimo. UI/API atual deixa qualquer metrologista editar com motivo livre.
- Exigir `motivo_mudanca` enum: `correcao_cadastro_inicial`/`reparo_reclassificou`/`recalibracao_revelou_drift_permanente`/`troca_de_componente_principal`/`outros_com_justificativa_obrigatoria_min_100_chars`.
- Cada motivo dispara fluxo diferente: `correcao_cadastro_inicial` exige aprovação gestor qualidade; `reparo_reclassificou` exige anexo do laudo.
- Em perfil A, mudança em `classe_exatidao` ou `faixa_medicao` sempre exige **assinatura A3 do RT**.

## (C) CONCERNS

### C1 — Padrão de TAG não documentado (NIT-DICLA-021 §5.2)
Sugestão default (configurável por tenant): `{PREFIXO_LAB}-{ANO_CADASTRO}-{SEQ_6_DIGITOS}` — ex: `BLS-2026-000123`. Em A, PREFIXO_LAB = sigla CGCRE.

### C2 — QR Code: durabilidade física + etiqueta de calibração separada
Na prática perfil A há **duas etiquetas distintas**:
- **Etiqueta de identificação** (TAG + QR) — permanente, poliéster + laminação, ≥5 anos.
- **Etiqueta de calibração** (selo INMETRO/RBC ou interno) — vincula nº cert + data + próxima — re-emitida a cada calibração.
Separar: `Export 1a: Etiqueta identificação permanente` + `Export 1b: Selo de calibração` (selo é módulo `certificados`).

### C3 — Vínculo equipamento↔certificado: query reverse O(1) com índice
Índice composto `(tenant_id, equipamento_id, data_emissao DESC)` em `certificado`. RNF "ficha 360° p95 ≤ 1.5s mesmo com 200 certs".

### C4 — Equipamento órfão (cliente excluído/inativado)
PII do cliente apagada via crypto-shredding (chave por tenant+cliente), mas **vínculo identificador opaco** sobrevive no equipamento. Ficha 360° mostra "cliente original removido — referência: hash_opaco" sem PII.
Job diário: identifica equips cujo `cliente_atual_id` aponta pra cliente inativo > 12 meses → status `orfao_pendente_decisao` → notifica suporte tenant.

### C5 — Status `inativo` ambíguo
- `inativo_temporario` (cliente suspendeu uso) — reativar livremente.
- `aposentado` (vida útil terminou, cliente não usa mas guarda) — reativar exige avaliação técnica.
- `sucata` — terminal.
- `orfao_pendente_decisao` (C4).
- `extraviado` (cliente reportou perda/roubo) — alerta se QR escaneado.

### C6 — PRD §4 "Transferência entre clientes" sem distinguir cliente_id_original × cliente_atual_id
Reescrever pra deixar claro: transferência altera `cliente_atual_id` e cria evento; nunca toca `cliente_id_original`.

### C7 — INV-004c (versão software no certificado) — interseção
`EquipamentoEvento.calibrado` carrega no payload `numero_certificado` + `software_version` daquela emissão (rastreabilidade reversa pra recall).

### C8 — Ficha 360° sem camadas de visibilidade por papel (cl. 4.2)
- Metrologista: tudo.
- Atendente: cadastro + próxima calibração.
- Técnico campo: cadastro + histórico certs.
Fotos de chegada + `decisao_apos_anomalia` só pra metrologista.

## (D) Campos a acrescentar ao modelo (texto pronto)

No agregado `Equipamento`:
```
- foto_principal_url: URL (imutável após primeira foto — só re-upload via "errata cadastro inicial")
- material_etiqueta: enum {poliester_laminado, vinil_termico, metalica_alumarca}
- numero_etiqueta_calibracao_atual: FK opcional pro selo vigente (módulo certificados)
- perfil_tenant_no_momento_cadastro: enum {A,B,C,D} — IMUTÁVEL (snapshot anti-downgrade — B4)
- procedimento_calibracao_aplicavel: ref a procedimento documentado (preenchido na 1ª calibração; versionável após)
- intervalo_recalibracao_meses: integer (versionável)
- consentimento_compartilhamento_historico_em_transferencia: boolean (B6)
```

Entidade nova `EquipamentoEntrada` (B1 + B2):
```
EquipamentoEntrada:
  - equipamento_id: FK
  - numero_entrada_lab: identificador sequencial (TAG provisória de bancada)
  - data_hora_recebimento: timestamp
  - recebido_por: usuario_id
  - condicao_visual_chegada: enum {integro, amassado, lacre_violado, contaminado, sem_acessorios, outros}
  - fotos_chegada: array<URL>  (≥1 obrigatória em perfil A)
  - anomalias_observadas: text
  - decisao_apos_anomalia: enum {prosseguir, contatar_cliente_aguardando, recusar_devolver, prosseguir_com_ressalva}
  - justificativa_decisao: text (≥30 chars se decisao != prosseguir)
  - lacre_chegada: text opcional
  - status_fluxo_lab: máquina de estados (B3)
  - data_hora_devolucao: timestamp nullable
  - condicao_visual_devolucao: enum
  - fotos_devolucao: array<URL>
  - termo_devolucao_assinado_url: URL (assinatura cliente — pode ser portal)
```

Enum de motivos em `EquipamentoVersao.motivo_mudanca` (B7):
```
motivo_mudanca: enum {
  correcao_cadastro_inicial,
  reparo_reclassificou,
  recalibracao_revelou_drift_permanente,
  troca_componente_principal,
  reidentificacao_fabricante,
  outros  (justificativa ≥100 chars + aprovação gestor qualidade)
}
+ exige_assinatura_a3_rt: boolean (true em A para classe/faixa)
+ assinatura_a3_hash: text nullable
```

## (E) Eventos faltantes pra rastreabilidade

```
Equipamento.recebido_no_lab           → metrologia, comercial
Equipamento.devolvido_ao_cliente      → comercial, financeiro (gatilho fatura)
Equipamento.anomalia_recebimento      → qualidade (abre NC se grave), comercial
Equipamento.nao_conformidade_aberta   → módulo nao-conformidades, comercial
Equipamento.nao_conformidade_resolvida → nao-conformidades, metrologia (libera emissão)
Equipamento.sucateado_com_certificado_vigente → comercial, comunicacao-omnichannel
Equipamento.orfao_detectado           → suporte tenant, dashboard
Equipamento.extraviado_reportado      → comercial, dashboard alerta
Equipamento.qr_escaneado              → analytics (heatmap), seguranca (anomalia geo)
Equipamento.transferencia_solicitada  → cliente cedente (aceite consentimento)
Equipamento.transferencia_aceita      → comercial
Equipamento.transferencia_recusada    → comercial
Equipamento.perfil_tenant_no_cadastro_congelado → emite uma vez no cadastro (B4)
Equipamento.classe_exatidao_alterada  → qualidade (revalida calibrações em aberto), RT (assina)
Equipamento.faixa_medicao_alterada    → qualidade, RT
```

## Próximos passos
1. Acatar B1–B7 antes de promover PRD a STABLE.
2. PRD volta pra DRAFT v2 com B1–B7 endereçados.
3. INV-025 ganha extensão escrita (cláusula B4 anti-downgrade). Possível desdobrar em `INV-EQP-001..004`.
4. Hook novo `equipamento-imutabilidade-check.sh` quando Wave A começar a codar.
5. **Antes de buscar acreditação RBC com este módulo em produção:** dossiê de validação ISO 17025 cl. 7.11 (URS/IQ/OQ/PQ) precisa ser revisado por consultor humano credenciado.
