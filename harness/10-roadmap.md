# 10 — Roadmap por fatias verticais auditáveis

> **P1-4**: substitui o roadmap original de 4 semanas (otimista) por sequência de fatias verticais com gate regulatório de saída.

## Princípio

Cada fatia é **emitível ponta a ponta** dentro do seu escopo e tem dossiê de validação fechado **antes** de a próxima iniciar. Não há "fatia parcial" — ou a fatia sai com gate verde, ou não sai.

O roadmap vigente segue a ordem lógica de construção de software:

1. fundação técnica;
2. cadastros principais;
3. fluxo operacional central;
4. portal e extras;
5. Qualidade e camadas regulatórias avançadas.

**Regra dura de interpretação**: artefato canônico, tela de leitura ou contrato implementado fora de ordem **não fecha a fatia** correspondente. Para uma fase contar como concluída, ela precisa entregar banco, API, UI e testes reais do núcleo daquela fase.

## Fatias

### V1 — Fundação técnica
**Escopo**
- Banco, schema, migrações, seeds e contratos básicos do núcleo operacional.
- Autenticação, sessão, RBAC e persistência reais no backend.
- Ambiente local reprodutível com API, web, portal e dependências de runtime.

**Gate de saída**
- Migrações e seeds canônicos rodam limpos no ambiente local e em CI.
- Login, sessão e RBAC reais funcionam com isolamento multitenant ativo.
- APIs centrais deixam de depender de cenários estáticos para o núcleo operacional.
- Dossiê V1 fechado em `compliance/validation-dossier/releases/v1.md`.
- Release-norm V1 aprovado por `product-governance`.
- Pacote normativo v1.0.0 assinado e em uso.

**Prazo realista estimado:** 4–6 semanas.

---

### V2 — Cadastros principais
**Escopo**
- CRUD real de clientes, equipamentos, padrões/pesos, procedimentos e usuários.
- Vínculos obrigatórios entre cliente, endereço, equipamento, padrão e competência.
- Busca, filtros básicos, arquivamento e trilha mínima de auditoria dos cadastros.

**Gate de saída**
- Todos os cadastros principais criam, editam, listam e arquivam dados reais no banco.
- As regras de elegibilidade de padrão, vínculo de equipamento e competência ficam aplicadas sobre dados persistidos.
- O back-office deixa de depender apenas de catálogos canônicos nos cadastros principais.
- Dossiê V2 fechado em `compliance/validation-dossier/releases/v2.md`.

**Prazo realista:** +4–6 semanas.

---

### V3 — Fluxo operacional central
**Escopo**
- Abertura e ciclo real da OS.
- Revisão técnica, assinatura e emissão oficial do certificado.
- Numeração sequencial, declaração metrológica, eventos críticos e persistência do fluxo ponta a ponta.

**Gate de saída**
- Existe caminho real ponta a ponta de OS até certificado emitido em ambiente controlado.
- Revisão técnica, assinatura e audit trail rodam sobre dados persistidos e atores reais.
- Numeração e declaração do certificado saem do fluxo operacional, não de cenários estáticos.
- `product-governance` libera release V3.

**Prazo realista:** +6–8 semanas.

---

### V4 — Portal e extras
**Escopo**
- Portal do cliente com dashboard, carteira de equipamentos e visualização do certificado.
- Verificação pública por QR e reemissão controlada sobre certificados reais persistidos.
- Canal mobile/offline e sync entram aqui como extensão operacional após o fechamento do fluxo central.

**Gate de saída**
- Portal do cliente opera sobre dados reais de equipamentos e certificados.
- Verificação pública responde com metadados mínimos e autenticidade de certificados reais.
- Reemissão controlada preserva histórico, QR anterior e trilha de aprovação.
- O canal mobile/offline, quando habilitado, mantém matriz de conflitos e fila humana verdes no dossiê V4.

**Prazo realista:** +6–8 semanas.

---

### V5 — Qualidade e camadas regulatórias avançadas
**Escopo**
- Módulo de Qualidade operando sobre OS, revisões, certificados e evidências reais.
- Não conformidades, auditorias internas, indicadores, análise crítica e governança de release.
- Camadas regulatórias avançadas, incluindo perfil Tipo A, escopo/CMC e pareceres formais.

**Gate de saída**
- Qualidade deixa de ser apenas leitura canônica e passa a operar sobre dados persistidos do núcleo.
- Regras de perfil regulatório, escopo/CMC e pacote normativo ficam integradas ao fluxo real.
- Auditoria interna dry-run e governança de release ficam arquivados no dossiê V5.
- `product-governance` libera V5 com pareceres necessários e pacote normativo vigente.

**Prazo realista:** +6–8 semanas.

---

## Total realista

**V1 → V5: ~26–36 semanas** (≈ 6–9 meses).

Compara com o roadmap original de 4 semanas do `HARNESS_DESIGN.md` — que era, reconhecidamente, otimista para o escopo do PRD.

## Regras de gate

1. Nenhuma fatia inicia sem gate da anterior fechado em `compliance/release-norm/`.
2. Gate de saída inclui: dossiê de validação, pacote normativo vigente, guardrails verdes, aprovação `product-governance`.
3. Regressão em fatia anterior (teste que era verde fica vermelho) = release da nova fatia bloqueado.
4. Fatia pode ser **dividida** se escopo crescer, mas nunca **mesclada**; cada uma mantém gate próprio.
5. Adiantamentos canônicos fora de ordem contam como ativos preparatórios, não como fechamento da fatia.

## Gate executável

`pnpm roadmap-check` valida `compliance/roadmap/v1-v5.yaml` como fonte canônica operacional:

- ordem estrita V1 → V5;
- dependência sequencial entre fatias;
- exigência de gate anterior antes da próxima fatia;
- `epic_id` e `linked_requirements` por fatia para agregação L0 na cascata;
- integridade de `linked_requirements` contra `requirements.yaml`, sem REQ inexistente ou duplicado entre fatias;
- bloco `coverage` explicitando quais `REQ-PRD-*` o roadmap cobre e quais ficam excluídos por serem gates transversais;
- `compliance/roadmap/transversal-tracks.yaml` mapeando cada exclusão para uma trilha transversal com owner, referência de harness e comandos de gate canônicos;
- release-norm, dossiê e pacote normativo por fatia;
- escopo, agentes primários e gates de saída por fatia.

`pnpm roadmap-backlog-check` valida `compliance/roadmap/execution-backlog.yaml` como complemento operacional do roadmap:

- cadeia explícita `V1.1 ... V5.x`;
- coerência entre `id`, `slice` e as fatias declaradas em `v1-v5.yaml`;
- dependências apenas para itens anteriores;
- janelas `now`, `next` e `later` sem regressão de prioridade;
- `linked_requirements` do item restritos aos requisitos já atribuídos à fatia correspondente.

Os dois gates entram em `pnpm check:all` e no pre-commit quando arquivos P1-4 mudam.

## Backlog operacional

`compliance/roadmap/execution-backlog.yaml` traduz o roadmap em sequência executável. Ele não substitui V1-V5; ele responde "qual é o próximo passo?" sem reabrir a governança macro.

Regras de leitura:

- cada item do backlog pertence a exatamente uma fatia;
- fechar um item não fecha a fatia por si só;
- a janela `now/next/later` orienta prioridade, não aprovação regulatória;
- a conclusão da fatia continua dependendo do gate de saída declarado em `v1-v5.yaml`.

## Paralelização possível

Dentro de uma fatia, agentes podem trabalhar em paralelo (Tier 2) em áreas não conflitantes:
- V1: `backend-api` + `db-schema` + `web-ui` em paralelo após specs aprovadas.
- V2: `backend-api` + `web-ui` + `db-schema` fatiam os cadastros por domínio.
- V3: `backend-api` + `web-ui` + `metrology-calc` fecham o fluxo central.
- V4: `backend-api` + `web-ui` + `android` atacam portal, reemissão e canal offline sem reabrir o núcleo.
- V5: `backend-api` + `web-ui` + `regulator` + `product-governance` consolidam Qualidade e camadas regulatórias.
