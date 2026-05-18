---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
us: US-CLI-003
autor: advogado-saas-regulado
plano: docs/dominios/comercial/modulos/clientes/planos/US-CLI-003.md
revisor: subagente advogado-saas-regulado (IA — NÃO substitui OAB)
tipo: revisao-juridica-consultiva
---

# Parecer Jurídico Consultivo — US-CLI-003 (LGPD + CDC + cadeia de responsabilidade)

> **Aviso legal obrigatório:** sou subagente IA, não tenho OAB ativa, este texto é minuta consultiva. Antes de qualquer go-live público de importação em massa de dados de titulares finais, advogado humano licenciado precisa revisar — em especial o **termo de procedência do dado** que o tenant declara no upload, o **template do aviso ao titular** (R6) e o **catálogo de motivos de rejeição** visível ao tenant.

---

## 1. Veredito

**APROVADO COM RESSALVAS BLOQUEANTES (R1–R9).** O plano US-CLI-003 acerta na arquitetura genérica (CSV no Marco 1, parsers Cali/Bling diferidos, dedup reaproveitando UNIQUE INDEX parcial do US-CLI-005, lote 1000 linhas, audit `cliente.importacao_executada`). **Porém, 9 lacunas LGPD/CDC precisam ser tampadas antes do code-complete:** a dispensa de aceite para PJ está formulada de modo perigosamente genérico (R1); a importação de PF sem rota de aceite é inviabilizada por base legal incorreta (R2); o arquivo CSV bruto não tem ciclo de vida definido — é o maior risco LGPD da Story (R3); falta entrada em RAT (R4); audit precisa enum + payload sanitizado sem PII (R5); falta declaração obrigatória de procedência pelo tenant (R6); relatório final exibido ao usuário pode listar PII e cair em INV-013 (R7); CPF de sócio em PJ exige tratamento explícito (R8); dados sensíveis precisam filtro de descarte (R9).

## 2. Resumo executivo (≤5 linhas)

Importação 1-clique amplifica em escala todos os riscos individuais de cadastro: 800 linhas com PII num arquivo bruto + um único endpoint que cria 800 titulares de uma vez. A arquitetura proposta está sólida — falta saneamento de **três fronteiras**: (a) procedência do dado (o tenant **precisa declarar** que tem base legal); (b) ciclo de vida do **arquivo importado** (não pode ficar em disco indefinidamente — é um data dump); (c) tratamento de **PF em lote** (rejeitar sem rota é correto para MVP-1 mas precisa cravar base legal explícita). Audit + relatório final espelham os vetos das US-CLI-001/002/004/005 (PII zero no audit, INV-013 cobrindo qualquer leitura de PII).

---

## 3. Ressalvas numeradas (R1–R9)

### R1 — Dispensa de aceite LGPD para PJ está mal formulada (BLOQUEANTE)

**Problema.** O plano grava `aceite_lgpd_origem="importacao"` + `aceite_lgpd_dispensa_motivo="pj_sem_pf_associada"` para **toda PJ importada**, independente do conteúdo das colunas. CSV típico de Cali/Bling traz, junto com CNPJ, **e-mail do contato**, **telefone do contato**, **nome do contato** e — frequentemente — **CPF do responsável/sócio**. Esses são dados pessoais de pessoa física (art. 5º I LGPD); a PJ deixa de ser "limpa" no momento em que qualquer um aparece preenchido.

**Base legal (LGPD).** Lei 13.709/2018 art. 1º (lei só protege PF), art. 5º I (PII), art. 7º V (execução de contrato) — combinado com a decisão R3 do parecer US-CLI-001 que cravou: aceite só dispensado em PJ **sem** PF associada.

**Correção exigida.**
1. Antes de gravar `dispensa_motivo`, o use case `importar_clientes` precisa **inspecionar** cada linha PJ:
   - Se houver coluna mapeada como `contato_cpf`, `socio_cpf`, `responsavel_cpf`, `email_pessoal`, `telefone_pessoal`: tratar como **"PJ com PF associada"** → mesma regra de R3 do US-CLI-001 (aceite obrigatório).
   - Se houver **apenas** `email_corporativo` (genérico tipo `contato@empresa.com.br`) e `telefone_corporativo` (sem nome de pessoa): admitir dispensa.
2. Gravar `aceite_lgpd_dispensa_motivo` com 3 valores possíveis e auditáveis:
   - `pj_sem_pf_associada` (caso ideal — sem nenhuma coluna PF mapeada).
   - `pj_com_pf_aceite_declarado_pelo_tenant` (tenant marca checkbox declarando que coletou aceite — ver R6 abaixo).
   - `pj_com_pf_pendente_aceite` (linha entra com `aceite_lgpd_pendente=true` + flag visível na 360° "este contato ainda não aceitou LGPD" — bloqueia comunicação WhatsApp RAT-06 enquanto pendente).
3. Task nova **T-CLI-049**: validador que decide qual dos 3 valores aplicar por linha.

**Severidade.** ALTA.

### R2 — Importação de PF: base legal não pode ser apenas "execução de contrato" implícita (BLOQUEANTE)

**Problema.** O plano oferece duas opções no non-goal: "rejeita ou exige flag de aceite presencial". Sem cravar a base legal explícita, o tenant fica num limbo: ou (a) **rejeita** PF em lote (UX ruim — o tenant tem 800 PF no Bling) ou (b) tenant marca um checkbox e o sistema confia sem prova.

**Base legal (LGPD).** Art. 7º V (execução de contrato) **cobre** PF que tem relação contratual pré-existente com o tenant (o Bling/Cali registrava cobranças, OS, NF-e — há prova). Não cobre lead frio ou contato comprado. Art. 7º IX (legítimo interesse) é **descartado** para importação de PF — sem LIA documentada por linha, vira carta branca. Art. 7º I (consentimento) exige aceite explícito **prévio** (não-bundle, não-presumido).

**Correção exigida.**
1. **Manter rejeição automática de PF** no Marco 1 como **default seguro** (`opcao_pf_em_lote: rejeitar` é o default na API). Justificativa cravada no plano: art. 7º I requer consentimento, importação em massa não consegue provar consentimento individual.
2. **Liberar PF condicionalmente** via flag explícita do tenant na chamada da API: `pf_aceite_origem` ∈ {`contrato_preexistente_documentado`, `consentimento_coletado_offline`, `migracao_sistema_anterior_com_aceite`}. Quando o tenant passa essa flag, ele declara legalmente (R6) que tem prova; cliente é criado com `aceite_lgpd_origem="importacao"` + `aceite_lgpd_base_legal="art_7_v"` ou `"art_7_i"`, e `aceite_lgpd_em_efetivo=NULL` (porque o aceite original é offline, fora do sistema) + `aceite_lgpd_evidencia_externa=<hash do termo declarado pelo tenant>`.
3. **Bloquear comunicação WhatsApp** (RAT-06 opt-in marketing) até que titular ré-aceite via portal/contato direto — importação não gera opt-in pra comunicação ativa, só pra registro cadastral.
4. Task nova **T-CLI-050**: campos `aceite_lgpd_base_legal` (enum) + `aceite_lgpd_evidencia_externa` (string opcional) no model `Cliente`.

**Severidade.** CRÍTICA.

### R3 — Arquivo CSV bruto não tem ciclo de vida — risco LGPD em escala (BLOQUEANTE)

**Problema.** O plano não menciona onde o arquivo importado vai parar. Ele é PII em massa (centenas a milhares de linhas com CPF/CNPJ/nome/email/telefone). Cenários ruins prováveis:
- Arquivo fica no disco do servidor indefinidamente.
- Arquivo entra no backup B2 sem retenção definida → daqui 5 anos ainda tem 800 CPFs num dump.
- Arquivo é re-enviado para Procrastinate em Wave A e fica em fila Redis/PG sem TTL.
- Operador Aferê em suporte forense vê o arquivo bruto e lê CPFs do tenant.

**Base legal (LGPD).** Art. 6º III (necessidade) — o arquivo é necessário **para executar a importação**, não para manter; manter além disso viola necessidade. Art. 6º V (qualidade) — manter dump bruto cria divergência com o estado pós-importação (origem da verdade vira ambígua). Art. 46/48 (segurança) — arquivo em disco sem encriptação adicional é vetor de vazamento.

**Correção exigida.**
1. **Arquivo NÃO persiste após a importação executar.** Fluxo:
   - `POST /importar-preview/`: arquivo entra em **memória ou tempfile**; após retornar preview, o tempfile é **deletado**. Preview retorna `upload_token` (UUID) + as 10 linhas; arquivo **não fica salvo entre preview e executar**.
   - `POST /importar-executar/`: o tenant **reenvia** o arquivo (não é o mesmo upload — o front-end mantém o blob localmente); validador confere que `hash(arquivo)` bate com algo gravado no preview se quisermos defesa anti-troca; após executar, **deletar tempfile imediatamente** (try/finally).
   - **NÃO gravar arquivo em B2/disco persistente em nenhuma hipótese** — nem para "auditoria", nem para "reproduzir importação". O que fica é o audit `cliente.importacao_executada` com hash do arquivo + totais, **não o arquivo**.
2. Comentar no plano e no use case: "arquivo de importação é dado transitório, retenção = duração da chamada HTTP".
3. Task nova **T-CLI-051**: garantir delete do tempfile em `finally`; teste `test_arquivo_csv_apagado_apos_execucao` que verifica que o tempfile não existe após o endpoint retornar (sucesso OU erro).
4. Settings do Django: `FILE_UPLOAD_MAX_MEMORY_SIZE` ajustado pra que arquivos < limite ficam em memória (sem tempfile); arquivos maiores usam tempfile + delete garantido.
5. **Tamanho máximo do upload:** alinhar com o limite 1000 linhas — cap em 2 MB pra CSV (DoS + memória).

**Severidade.** CRÍTICA.

### R4 — Falta entrada em RAT (Registro de Atividade de Tratamento) (BLOQUEANTE)

**Problema.** Importação em massa é operação de tratamento de PII de centenas de titulares de uma vez. LGPD art. 37 exige RAT atualizado. O catálogo `docs/conformidade/comum/lgpd-rat.md` cobre RAT-01 (cadastro tenant), RAT-02 (usuário operacional), RAT-03 (cliente final manual), mas **não cobre importação em massa**. RAT-03 fala em "cadastro" — interpretação ambígua se cobre importação em lote.

**Base legal (LGPD).** Art. 37 (registro de operações de tratamento) + art. 6º VI (transparência).

**Correção exigida.**
1. Criar **RAT-17 — Importação em massa de cadastro de cliente final do tenant** em `docs/conformidade/comum/lgpd-rat.md`:
   - Dados tratados: nome, CPF/CNPJ, e-mail, telefone, endereço.
   - Base legal: art. 7º V (execução de contrato — quando há contrato preexistente declarado pelo tenant) **ou** art. 7º I (consentimento — só com prova externa declarada R2).
   - Finalidade: migração de sistema anterior do tenant para o Aferê.
   - Retenção: mesma de RAT-03 (vigência do contrato tenant + 5 anos default fiscal).
   - **Categoria de risco:** elevada (volume + velocidade).
   - DPIA: **DPIA-06** (criar) — "Importação em massa de cadastro de cliente final" — avalia risco de re-uso indevido, vazamento de arquivo bruto (R3), aceite presumido (R1/R2).
2. Task nova **T-CLI-052**: adicionar RAT-17 ao `lgpd-rat.md` antes do go-live MVP-1 (basta dogfooding gerar a primeira importação).
3. Task nova **T-CLI-053**: DPIA-06 **diferida pra Wave A** (não bloqueia Marco 1 dogfooding-only — Roldão importando dados da própria Balanças Solution é caso interno).

**Severidade.** ALTA.

### R5 — Audit `cliente.importacao_executada` precisa enum + payload sanitizado (BLOQUEANTE)

**Problema.** T-CLI-046 fala em "totais + nenhuma PII". Bom princípio, mas falta especificar o payload — sem isso o implementador "esquece" e grava nome/CPF da linha rejeitada "pra investigar depois". Espelho dos vetos US-CLI-001, US-CLI-002 R1, US-CLI-004 R1/R2, US-CLI-005 R1/R2.

**Base legal (LGPD).** Art. 6º III (necessidade) — audit prova **que** houve importação, **quantos** registros, **resultado agregado**, **não quais titulares**. Cross-tenant blast radius — admin Aferê suporte forense lê audit sem ler PII.

**Correção exigida — payload sanitizado:**

```python
{
  "tenant_id": "<uuid>",
  "usuario_id": "<uuid>",
  "timestamp": "...",
  "arquivo_hash": "<sha256 do CSV bruto>",
  "arquivo_tamanho_bytes": 142933,
  "arquivo_linhas_total": 812,
  "totais": {
      "criados": 540,
      "atualizados": 230,
      "rejeitados": 42,
      "pf_rejeitadas_por_falta_aceite": 28,
      "pj_dispensa_aceite": 510,
      "pj_com_pf_pendente_aceite": 30
  },
  "rejeicoes_por_motivo": {
      "cnpj_invalido": 15,
      "cpf_invalido": 5,
      "pf_sem_aceite": 28,                # categoria, não a linha
      "dados_sensiveis_filtrados": 0,     # ver R9
      "outro": 2
  },
  "linhas_rejeitadas_hashes": [
      {"linha_numero": 42, "linha_hash": "<sha256>", "motivo": "cnpj_invalido"},
      ...
  ],
  "ip_hash": "<sha256(ip+salt_tenant)>",
  "procedencia_declarada": "migracao_bling_v3"   # ver R6
}
```

**Regras:**
- **Nunca** gravar nome, CPF, e-mail, telefone, endereço em texto cru no audit.
- `linhas_rejeitadas_hashes` permite ao tenant re-executar a investigação localmente cruzando com o CSV (que ele tem) sem que o audit retenha PII.
- Teste de regressão **T-CLI-054**: `test_audit_importacao_sem_pii_cru` rodando regex de CPF/CNPJ/email/telefone no payload serializado.

**Severidade.** CRÍTICA.

### R6 — Falta declaração obrigatória de procedência pelo tenant (BLOQUEANTE)

**Problema.** O tenant exportou um CSV da Cali/Bling. **Quem é o controlador dos dados nesse momento?** Cali/Bling era operador do tenant lá; quando o tenant traz pro Aferê, há **continuidade do tratamento**, não nova coleta. Mas o Aferê **não tem como saber** se o tenant coletou aceite originalmente — e se aceitar importação sem nada, fica como **co-responsável** por dado importado sem base legal.

**Base legal (LGPD).** Art. 5º VI (controlador), art. 5º VII (operador), art. 39 (responsabilidade solidária quando operador descumpre obrigação ou age fora da instrução). O Aferê **é operador**; se o tenant traz dado ilícito e o Aferê processa sem questionar, fica exposto (art. 39 §único: solidariedade).

**Correção exigida.**
1. **Termo de procedência obrigatório no upload.** Antes de o tenant clicar "Executar importação", precisa marcar checkbox(es) e digitar campo livre curto (≤200 chars):
   - ☐ "Declaro que **tenho base legal documentada** (contrato, consentimento ou obrigação legal) para tratar os dados pessoais presentes neste arquivo."
   - ☐ "Declaro que **comuniquei aos titulares** (ou comunicarei em até 10 dias úteis) que seus dados foram migrados para o Aferê, conforme LGPD art. 9º."
   - ☐ "Declaro que **não há dados sensíveis** (art. 5º II LGPD: saúde, biometria, origem racial, opinião política, filiação sindical, dado genético, vida sexual) nas colunas mapeadas."
   - Campo livre: "Origem do dado (sistema anterior, ex.: 'Bling v3 export 2026-04')" — vira `procedencia_declarada` no audit (R5).
2. Gravar essas declarações em **tabela separada** `cliente_importacao_declaracao` (RLS por tenant, retenção 5 anos), referenciada pelo audit por hash. Não joga no audit WORM (porque a declaração pode precisar ser correlacionada com solicitação ANPD depois — operacional, não imutável-para-sempre).
3. Sem as 3 declarações marcadas, endpoint `executar` retorna **400 Bad Request** com mensagem clara — não há "executar mesmo assim".
4. Tasks novas **T-CLI-055** (modelo `ImportacaoDeclaracao`) + **T-CLI-056** (validação no use case).

**Severidade.** CRÍTICA.

### R7 — Relatório final exibido ao tenant pode vazar PII + INV-013 obrigatório (BLOQUEANTE)

**Problema.** AC-CLI-003-2 fala em "relatório final (criados/atualizados/rejeitados)". Implementação ingênua: lista linha por linha com nome/CPF de quem foi criado/rejeitado. Quem pode ler esse relatório? Quanto tempo fica disponível? Cai em INV-013 (log de acesso a dado de cliente)?

**Base legal (LGPD).** Art. 6º III (necessidade), INV-013 (log de visualização de dado de cliente — cl. 4.2 ISO 17025), art. 18 II (titular saber quem tratou — quando Wave B vier).

**Correção exigida.**
1. **Relatório imediato (resposta HTTP da chamada `/importar-executar/`):**
   - Estrutura: totais (igual audit, R5) + **lista de até 50 linhas rejeitadas** com `{linha_numero, motivo_codigo, motivo_descricao_curta}`. **Sem nome, sem CPF, sem e-mail.** Tenant cruza com o CSV dele localmente (ele tem o arquivo).
   - Estrutura **não inclui** nome dos criados/atualizados — quem quiser ver os criados consulta a lista de clientes normalmente (cada consulta gera log INV-013).
2. **Relatório persistido (consulta posterior):**
   - Não persistir relatório com PII. Persistir apenas o `audit_import_id` + permitir consulta retornando os mesmos totais + linhas rejeitadas hash (R5).
   - Histórico de importações fica em tela `/clientes/importacoes/` listando `{usuario, timestamp, arquivo_hash, totais, procedencia_declarada}` — perfil `admin_tenant` (mesma authz que dispara a importação).
3. **INV-013 aplicada:** quando o admin abrir o relatório, gera log `acessos_dados_cliente` com `finalidade = "consulta_relatorio_importacao"` (adicionar ao enum de finalidades acesso, US-CLI-002 R2) + `cliente_id=NULL` + `recurso={tabela: "cliente_importacao", id: <import_id>}`. Cada um dos clientes criados, quando aberto individualmente, gera seu próprio log INV-013.
4. Tasks novas **T-CLI-057** (relatório sem PII) + **T-CLI-058** (endpoint `GET /clientes/importacoes/` + INV-013).

**Severidade.** ALTA.

### R8 — CPF de sócio/responsável em PJ exige tratamento explícito (ALTA)

**Problema.** Cali/Bling/sistemas BR rotineiramente trazem **CPF do sócio/responsável legal** junto com CNPJ (campo "CPF do responsável"). O plano não define se esse CPF entra como **atributo do PJ** (campo `Cliente.cpf_responsavel`), se gera **PF separada** vinculada como contato, ou se é **descartado**.

**Base legal (LGPD).** Art. 5º I (CPF é PII), art. 7º V (execução de contrato) ou art. 7º II (obrigação fiscal — NF-e PJ exige CPF do responsável em alguns municípios). PJ deixa de ser "limpa" no momento que CPF aparece (R1).

**Correção exigida.**
1. Mapeamento sugerido (`AC-CLI-003-1`) deve detectar colunas tipo `cpf_responsavel`, `cpf_socio`, `responsavel_legal_cpf` e oferecer **3 destinos** ao tenant:
   - (a) Gravar como `Cliente.cpf_responsavel_legal` (atributo da PJ) — pra fins fiscais (NF-e).
   - (b) Criar contato separado em `Cliente.contatos[]` com o CPF como `documento_pessoal` + `aceite_lgpd_pendente=true` (R1, caminho `pj_com_pf_pendente_aceite`).
   - (c) Descartar (não importar essa coluna).
2. Default seguro: **(b)** — porque cria registro auditável de PF associada e força aceite pendente.
3. Documentar no plano que opção (a) só é apropriada quando o tenant declara (R6) que tem aceite do responsável.
4. Task nova **T-CLI-059**: detector heurístico de coluna CPF-em-PJ no preview + opções ao tenant.

**Severidade.** ALTA.

### R9 — Dados sensíveis precisam filtro de descarte explícito (ALTA)

**Problema.** O plano de non-goals não menciona dados sensíveis (art. 5º II LGPD: saúde, biometria, origem racial, opinião política, filiação sindical, dado genético, vida sexual). Cenário concreto: cliente do Roldão é uma clínica/hospital e o CSV exportado tem coluna "tipo de paciente atendido" (saúde) ou "religião" ou "raça/cor" (campos comuns em sistemas hospitalares antigos). Importação acrítica processa dado sensível **sem base legal própria** (art. 11 LGPD exige base específica, não basta art. 7º V).

**Base legal (LGPD).** Art. 5º II (definição de dado sensível), art. 11 (bases legais específicas — mais restritas que art. 7º).

**Correção exigida.**
1. Preview (`AC-CLI-003-1`) detecta colunas com nomes suspeitos (regex case-insensitive de palavras-chave: `saude|saúde|cid|diagnostico|raça|raca|cor|religiao|religião|orientacao|sexual|biometr|dna|genetic|sindical|sindicato|politic`) e **avisa o tenant**: "Coluna 'X' parece conter dados sensíveis (LGPD art. 5º II). Estes campos serão **descartados** na importação. Se você precisa importá-los, isso exige base legal própria art. 11 — abra ticket de suporte."
2. Use case `importar_clientes` **descarta** automaticamente colunas marcadas como sensíveis (não há "importar dado sensível" no MVP-1). Contagem `dados_sensiveis_filtrados` vai pro audit (R5).
3. Documentar no plano (non-goals): "importação de dados sensíveis (LGPD art. 11) é V2+ com fluxo dedicado — DPIA + base legal específica + consentimento explícito por linha quando aplicável."
4. Task nova **T-CLI-060**: detector + descarte automático + entrada no audit.

**Severidade.** ALTA.

---

## 4. Riscos jurídicos (não bloqueantes, mas dignos de nota)

| Risco | Probabilidade | Impacto | Observação |
|---|---|---|---|
| Tenant declara procedência falsa (R6) para forçar importação ilícita | Média | Aferê fica como co-responsável solidário (art. 39 §único) | Mitigação via DPA: cláusula "tenant assume responsabilidade pela legalidade da procedência declarada; Aferê não verifica veracidade material" + auditoria amostral em Wave B |
| Titular descobre que dado foi importado sem aceite e exerce art. 18 IV (oposição) → tenant precisa reverter | Média | Reclamação ANPD + retrabalho do tenant | R2 (PF default-rejeita) + R6 (declaração) reduzem; mitigação adicional: comunicação proativa do tenant em 10 dias (R6 checkbox 2) |
| Importação grava dado de **menor de idade** (raro em B2B mas possível em clínica/odonto pediátrica) | Baixa | Art. 14 LGPD exige consentimento dos pais — base específica | V2: detector heurístico de data nascimento + filtro; Marco 1: documentar no non-goal "dados de menores exigem fluxo dedicado V2" |
| Re-importação do mesmo arquivo (CSV mexido ligeiramente) cria audits duplicados | Baixa | Polui audit + investigação confusa | `arquivo_hash` no audit (R5) permite detectar; UX warning "este arquivo já foi importado em [data]" |
| Crypto-shredding do tenant em 2031 — audit retém `arquivo_hash` que não é PII, mas `linhas_rejeitadas_hashes` referencia linhas que continham PII | Baixa | Hash sem sal não é PII LGPD (irreversível), mas com sal por tenant fica ainda mais defensável | Usar `sha256(linha + salt_tenant)` em vez de `sha256(linha)` puro |
| Operador Aferê em suporte forense lê audit `cliente.importacao_executada` e descobre que o tenant importou 800 clientes (informação comercial sensível, não PII mas sensível ao tenant) | Média | Quebra de confidencialidade comercial do tenant (não LGPD, mas DPA) | Mesma mitigação US-CLI-004 R6 — view sanitizada para admin Aferê + RAT-15 obrigatória pra acesso direto |
| Importação executada por usuário não-`admin_tenant` (escalada de privilégio) | Baixa | Funcionário operacional importa dados sem aprovação do dono | T-CLI-047 já restringe a `admin_tenant` — mantido |

---

## 5. Pontos fortes (validados como corretos)

- ✅ **Lote 1000 linhas + CSV-only no Marco 1**: dimensionamento prudente — limita blast radius de bug, simplifica auditoria forense, evita dependência Procrastinate.
- ✅ **Síncrono no Marco 1**: evita complexidade de job em background que ainda não tem worker. Trade-off claro e correto.
- ✅ **Dedup reaproveita UNIQUE INDEX parcial do US-CLI-005 R4**: consistência arquitetural — importação não cria caminho alternativo de criação de cliente que escape do dedup. Bom.
- ✅ **Authz `clientes.importar` exigindo `admin_tenant`**: ação de alto impacto merece perfil restrito (SEC-LEAST-PRIV-001). Espelho correto do US-CLI-005 (`mesclar`) e US-CLI-004 (`bloquear`).
- ✅ **Non-goal claro pra Cali/Bling parsers, Excel, async e PF com aceite individual**: limites desta fase bem desenhados.
- ✅ **Audit `cliente.importacao_executada` previsto** (faltou só especificar payload — R5).
- ✅ **PJ tratada como caso comum, PF como exceção**: ordem correta — PJ é a maioria do B2B do tenant; PF é minoria sensível.
- ✅ **Mensagem "pula linha exigindo aceite explícito pra PF"**: instinto correto (R2 só formaliza a base legal).
- ✅ **Plano cita explicitamente `advogado-saas-regulado` como subagente a consultar** com 3 perguntas: aceite em lote, retenção do arquivo, RAT — este parecer responde as três (R1/R2, R3, R4).
- ✅ **Sequência de 8 tasks bem dimensionada**: preview separado de executar, lógica em use case puro, adapter Django isolado, audit como task dedicada, authz como migration seed, testes em 8 cenários cobrindo happy + unhappy + DoS + audit + authz.

---

## 6. Próximos passos

- ✅ Aplicar R1–R9 no plano `US-CLI-003.md` (autoria: agente implementador — tech-lead ou implementador direto).
- ✅ Tasks novas (resumo): **T-CLI-049** (validador PJ-com-PF), **T-CLI-050** (`aceite_lgpd_base_legal` + `evidencia_externa`), **T-CLI-051** (delete tempfile garantido), **T-CLI-052** (RAT-17 no `lgpd-rat.md`), **T-CLI-053** (DPIA-06 — Wave A), **T-CLI-054** (teste audit sem PII), **T-CLI-055/056** (declaração de procedência), **T-CLI-057/058** (relatório sem PII + INV-013), **T-CLI-059** (CPF de responsável), **T-CLI-060** (filtro dados sensíveis).
- ⚠️ **Antes do go-live público** (não MVP-1 dogfooding): advogado humano OAB ativa revisa (a) texto dos 3 checkboxes de procedência (R6), (b) catálogo de motivos de rejeição visível ao tenant, (c) mensagem ao tenant quando dados sensíveis são detectados (R9), (d) cláusula DPA sobre responsabilidade do tenant pela procedência. Estimar 2-3h de revisão.
- ⏳ Diferido pra Wave A: parsers Cali/Bling com mapeamento automático nativo + Excel/XLSX + Procrastinate worker async + DPIA-06 formal.
- ⏳ Diferido pra Wave B: re-aceite por portal do titular (`lgpd-portal`) para PF importadas com `aceite_lgpd_pendente=true`; auditoria amostral de procedências declaradas; importação de dados sensíveis com base art. 11 + DPIA dedicada; rollback de importação completa.

---

## 7. Referências normativas usadas

- Lei 13.709/2018 (LGPD) — art. 1º, 5º I/II/VI/VII, 6º III/V/VI, 7º I/II/V/IX, 8º §4º, 9º, 11, 14, 16 II, 18 II/IV/VI, 37, 39 §único, 46/48
- Lei 8.078/1990 (CDC) — art. 6º III/IV (informação adequada quando comunicação proativa do tenant ao titular pós-importação ocorrer)
- Res. CD/ANPD 15/2024 — incidentes (categoria de risco elevada por volume)
- ISO/IEC 17025 cl. 4.2 (confidencialidade) — INV-013 aplicada ao relatório
- INV-001, INV-013, INV-024, INV-AUTHZ-001/002, INV-TENANT-001/002, SEC-LEAST-PRIV-001 (`REGRAS-INEGOCIAVEIS.md`)
- RAT-03 (cadastro cliente final manual) + **RAT-17 a criar** (importação em massa) (`docs/conformidade/comum/lgpd-rat.md`)
- `docs/conformidade/comum/retencao-matriz.md` §2 (linha "Audit trail" + linha "Cadastro de cliente final")
- US-CLI-001 revisão (`US-CLI-001-advogado.md`) — precedente R3 (PJ-com-PF) e veto PII em audit
- US-CLI-002 revisão (`US-CLI-002-advogado.md`) — precedente R1 (audit sanitizado), R2 (enum finalidade de acesso)
- US-CLI-004 revisão (`US-CLI-004-advogado.md`) — precedente R1/R2 (enum + regex anti-PII), R6 (view sanitizada admin Aferê)
- US-CLI-005 revisão (`US-CLI-005-advogado.md`) — precedente R1 (payload sem PII), R2 (enum + sanitizador), R4 (UNIQUE INDEX parcial)
