---
owner: corretora-seguros-saas (subagente)
revisado-em: 2026-05-18
status: stable
escopo: PRD draft equipamentos — review risco operacional + RC + cyber
---

# Revisão Corretora — PRD `equipamentos`

**Resumo:** INV-025 cobre fraude documental mas deixa **4 vetores de risco descobertos** (troca física, QR transplantado, sucatamento contestado, transferência mal-feita) que disparam RC profissional E&O. Superfície de QR Code multi-tenant hoje é buraco de cyber + cross-tenant. **2 BLOQUEADORES** pra STABLE; 6 CONCERNs; 4 recomendações que cortam prêmio estimado em 15-25%.

## (A) Risco residual

| Risco | Vetor | Severidade | Aciona seguro? |
|---|---|---|---|
| R-018-A: troca física de instrumento sem rebadge | Operador desonesto/erro campo | Alta | RC profissional E&O |
| R-018-B: QR Code arrancado e colado em outro | Cliente final fraudando IPEM | Alta | RC profissional + criminal terceiro |
| R-018-C: equip sucateado com cert ainda referenciando | Falha processo do tenant | Média | RC profissional |
| R-018-D: transferência cliente A→B com cert do A ainda válido | Disputa contratual | Alta | RC profissional |
| R-027: `/v1/qr/{hash}` enumerable ou forjável | Cyber externo | **Crítica** | Cyber + LGPD ANPD |
| R-LGPD-foto: foto futura vazando rótulo com CPF/endereço | Cyber + LGPD | Média | Cyber |
| R-058-A: técnico P-OP-01 sai pra concorrente com QR no celular | Vendor↔tenant | Média | RC profissional (defesa) |
| R-099 (NOVO): agente IA introduz bug que viola INV-025 → NC CGCRE → tenant aciona Aferê | Vendor↔tenant — modelo 100% agentes IA | **Crítica** | RC profissional + D&O |
| R-100 (NOVO): INV-025 "Absoluta em A; configurável em B/C/D" → perfil não-acreditado relaxa → fraude → tenant culpa Aferê | Contratual | Alta | RC profissional |

## (B) BLOQUEADORES

### B1 — `GET /v1/qr/{hash}` — modelo de ameaça ausente
Contrato API diz "(público autenticado)" — contradição. Sem decisão:
- Hash precisa ser **opaco, ≥128 bits entropia, HMAC sobre (equipamento_id, tenant_id, salt_tenant)** — não sequencial.
- 404 idêntico para "QR inválido" e "QR de outro tenant" (sem oracle de enumeração).
- Rate limit insuficiente — precisa também **60 req/min/IP não-autenticado** + alerta após 10 404s consecutivos.
- Sem isso, INV-027 (cross-tenant) violada na fronteira pública. Cyber subscritor EXCLUI cobertura de incidente em endpoint público sem rate-limit por IP.

### B2 — Definir responsabilidade explícita "agente IA introduziu bug que violou INV-025"
Modelo 100% agentes IA é diferencial mas vira **causa de exclusão clássica em RC profissional** se for tratado como "atos dolosos do segurado". Precisa **antes do 1º tenant pago:**
- ADR ou cláusula declarando: "código gerado por agente IA é responsabilidade do Aferê como editor do software, equivalente a código escrito por funcionário humano".
- Suite de testes obrigatória pra INV-025 (hook `inv-025-immutability-check.sh` análogo a `migration-rls-check`).
- Sem isso, seguradora pode argumentar "ausência de revisão humana = neglect" e negar sinistro.

## (C) CONCERNs

### C1 — Sucatamento sem trilha física auditável
`POST /sucatear` sem exigir:
- Foto do instrumento sucateado;
- Assinatura A3 do RT do tenant;
- Evento WORM com hash da foto + timestamp + geolocalização.
Cliente pode alegar "vocês declararam sucata mas o equipamento estava bom". Disputa cível → RC profissional. **Mitigação:** ADR-0014 (transições regulatórias) cobre — confirmar.

### C2 — Transferência entre clientes — vácuo contratual
Falta:
- Aceite explícito do cliente atual + cliente novo;
- Bloqueio se equipamento tem OS aberta OU cert vigente últimos 12 meses;
- Evento `Equipamento.transferido` com `aceite_cliente_origem_id` e `aceite_cliente_destino_id`.

### C3 — Foto do equipamento — escopo "futuro" sem guardrails
Antes de habilitar:
- Limite ≤5MB;
- Scan automático OCR + bloqueio se CPF/CNPJ no rótulo;
- Storage Backblaze B2 com bucket separado por tenant (crypto-shredding LGPD).
Sem isso, vazamento = LGPD ANPD = cyber acionado.

### C4 — INV-025 "Absoluta em A; configurável em B/C/D" — brecha contratual
**Mitigação obrigatória:**
- Cláusula contrato Aferê↔tenant: "ao operar em perfil B/C/D com INV-025 relaxada, tenant assume responsabilidade exclusiva por integridade dos dados pós-alteração; Aferê fica isento";
- UI alerta visível ("você está desligando proteção que garante validade do documento — confirme com assinatura A3");
- Evento WORM imutável da relaxação.

### C5 — Técnico P-OP-01 leva QR Codes pra concorrente
- Revogação de sessão mobile no logout/demissão revoga **todas** URLs em cache;
- QR Code com TTL curto (24h) renovado por sessão ativa — não permanente;
- Alternativa: QR redireciona pra endpoint que valida sessão; sessão revogada = 401 mesmo com QR físico válido.

### C6 — `cliente_id_original` imutável vs. transferência — documentar comportamento UX
Cliente novo escaneia QR e vê "certificado emitido para Cliente A" — pode reclamar. Documentar na UI e contrato.

## (D) Recomendações de produto que reduzem prêmio

| Recomendação | Desconto estimado |
|---|---|
| D1. Hook `inv-025-immutability-check.sh` + suite E2E auditável pré-merge | 10-15% |
| D2. QR Code com HMAC + TTL + revogação por sessão | 5-10% |
| D3. Backblaze B2 WORM + crypto-shredding por tenant (já decidido ADR-0002) | 5% |
| D4. Suite obrigatória pra agentes IA antes de merge tocando INV-025 (extensão `policy-test-coverage`) | 5% |

**Total: 20-30% redução sobre baseline.** Em capital R$ 1-3M RC + R$ 500k-2M cyber → R$ 2-7k/ano economizados.

## (E) Cláusulas contratuais a adicionar

### E1 — Limitação de responsabilidade Aferê↔tenant
> A responsabilidade total do Aferê por evento decorrente de defeito em módulo `equipamentos` está limitada a (i) 12 meses de mensalidade paga pelo tenant ou (ii) o capital efetivamente recebido em apólice RC profissional, o que for maior. Excluídos lucros cessantes, danos morais a terceiros e multas regulatórias do tenant.

### E2 — Cláusula INV-025-relaxada (perfil B/C/D)
> Ao desabilitar imutabilidade pós-emissão (perfil não-acreditado), tenant declara ciência de que assume responsabilidade exclusiva pela integridade documental subsequente. Aferê fica isento de qualquer reclamação de cliente final do tenant decorrente de alteração realizada após desabilitação.

### E3 — Cláusula vendor↔tenant agente IA
> Código gerado por agentes de IA do Aferê é equiparado, para todos os efeitos contratuais e securitários, a código escrito por funcionário humano do Aferê. Bugs introduzidos por agentes IA seguem o mesmo regime de RC profissional E&O.

### E4 — Cláusula transferência de equipamento
> Tenant declara obter aceite expresso do cliente origem E cliente destino antes de invocar transferência. Aferê não verifica autorização externa; falha de processo do tenant é risco do tenant.

### E5 — Cláusula sucatamento
> Status `sucata` no Aferê é declaração unilateral do tenant. Tenant garante que sucatamento físico ocorreu conforme NIT-DICLA-021 e mantém evidência local (foto + protocolo) por 8 anos (ISO 17025 cl. 8.4).

## Próximos passos
- Apólice precisa ser emitida por corretora SUSEP humana — **NÃO contratar antes do 1º tenant pago** (memória `project_sem_cliente_externo_agora`).
- Briefing pra corretora especializada em **Tech E&O + Cyber pra SaaS regulado BR** (Marsh, AON Tech, Howden) quando momento chegar.
- BLOQUEADORES B1/B2 devem cair antes de PRD virar STABLE.
- CONCERNs C1-C6 podem entrar em backlog Wave A com tasks rastreáveis, exceto C4 (cláusula contratual hoje).
