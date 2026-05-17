---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: fiscal
dominio: financeiro
---

# Modelo de Domínio — Fiscal

## Decisão fundadora: Aferê NÃO calcula imposto

**Non-goal explícito:** o sistema **não calcula** ISS, retenções, ICMS, PIS/COFINS, IRRF, INSS. Aferê **exibe campos** pra tenant preencher conforme orientação do contador dele. Modelo guarda os valores informados; cálculo é responsabilidade do tenant + contador.

Razão: regimes (Simples Nacional, Lucro Presumido, Lucro Real), substituições, retenções, alíquotas municipais → matriz combinatória inviável de manter sem ser ERP contábil completo. Aferê foca em **emitir corretamente o que o contador configurou**.

## Agregados

### `ConfiguracaoFiscal` (por tenant)

Atributos:
- `id`, `tenant_id`
- `regime_tributario`: enum (`simples-nacional` | `lucro-presumido` | `lucro-real`)
- `cnpj`, `inscricao_municipal`, `inscricao_estadual` (opcional)
- `regime_iss`: `normal` | `substituido` (informativo, não recalcula)
- `aliquota_iss_padrao` (informativa)
- `codigos_servico_lc116[]` (códigos que tenant emite)
- `certificado_digital`: `tipo` (`a1`/`a3`), `valido_de`, `valido_ate`, `armazenamento` (referência cofre)
- `baas_provider`: `plugnotas` | `focus` (configurado por ADR-0008)

### `DocumentoFiscal` (raiz — NFS-e ou NFe)

Atributos:
- `id`, `tenant_id`, `tipo`: `nfs-e` | `nfe`
- `numero` (numeração sequencial do tenant)
- `serie`
- `municipio_emissor` (NFS-e) / `uf` (NFe)
- `cliente_id`, `cliente_doc`, `cliente_nome`
- `os_id?`, `titulo_id?` (rastreio origem)
- `valor_servico`, `descricao`
- `codigo_lc116` (snapshot)
- **Campos fiscais informados pelo tenant** (não calculados): `valor_iss_retido`, `valor_inss`, `valor_irrf`, `valor_pis`, `valor_cofins`, `valor_csll`, `aliquota_iss` (todos opcionais, snapshot do que tenant ou config preencheu)
- `xml_url` (WORM)
- `pdf_url`
- `status`: `rascunho` | `emitida` | `cancelada` | `corrigida` | `em-contingencia`
- `modo`: `normal` | `svc-an` | `svc-rs` | `epec` | `contingencia-municipal`
- `protocolo_autorizacao` (SEFAZ/município)
- `emitida_em`, `cancelada_em`, `cancelamento_razao`

### `EventoFiscal` (subentidade — CC-e, cancelamento, inutilização)

Atributos:
- `id`, `documento_id`, `tipo`: `cc-e` | `cancelamento` | `inutilizacao`
- `payload` (texto correção / razão cancelamento)
- `xml_evento_url` (WORM)
- `protocolo`
- `emitido_em`

### `Numeracao` (entidade por tenant + tipo + serie)

- `proximo_numero`
- `buracos[]` (números que falharam emissão — aguardando inutilização)
- `prazo_inutilizacao_dias` (default 25, alerta antes)

## Regras de negócio

- **INV-007 contingência:** módulo entra em produção com contingência funcionando. Sem isso = bloqueio absoluto.
- **WORM imutável:** XML nunca alterado pós-WORM (verificado por hash).
- **Cancelamento < 24h:** automático via BaaS. Extemporâneo: comunica tenant + sugere suporte municipal.
- **CC-e:** corrige descrição, datas, alguns campos; nunca valor/CPF/CNPJ.
- **Idempotência emissão:** tenant clicar 2× não emite 2 NFs.
- **Auditor:** endpoint emissão sem MFA → FAIL; XML sem WORM → FAIL; cancelamento sem razão → CONCERN.

## Eventos emitidos

- `NFSeEmitida(documento_id, valor, cliente_id, xml_url)` → consumido por: Comercial (timeline 360°), Contas a Receber (anexa à fatura)
- `NFeEmitida(...)` (mesmo padrão; V2)
- `NFCancelada(documento_id, razao)`
- `CCeEmitida(documento_id, evento_id)`
- `NumeracaoInutilizada(documento_tipo, intervalo)`
- `ContingenciaAtivada(modo)`
- `ContingenciaEncerrada()`

## Eventos consumidos

- `Pago` (Contas a Receber) → opcional gatilho emissão automática (configurável tenant)
- `OSConcluida` (Operação) → emissão pré-preenchida com dados OS

## Adapter FiscalProvider (ADR-0008)

Interface:
```
emitir(documento) → resultado{protocolo, xml, pdf}
cancelar(documento, razao) → resultado
cce(documento, texto) → resultado
inutilizar(intervalo) → resultado
status_servico(municipio|uf) → ok|degraded|down
```

Implementações: `PlugNotasProvider`, `FocusNFeProvider`. Troca sem mudar consumidor.

## Non-goals do modelo

- Cálculo de imposto (decisão fundadora).
- Apuração contábil.
- SPED (V2).
- DDA.
- Múltiplas moedas / NF internacional.

## Invariantes

- INV-007 (contingência dia 0), INV-008 (audit), WORM imutável, idempotência emissão.

## Referências

- ADR-0008, ADR-0009
- `docs/conformidade/comum/fiscal.md` + `fiscal-contingencia.md`
- `docs/comum/integracoes-externas/plugnotas.md`, `focus-nfe.md`, `sefaz-municipios.md`
- `docs/comum/integracoes-inter-modulos.md`
- `REGRAS-INEGOCIAVEIS.md`
