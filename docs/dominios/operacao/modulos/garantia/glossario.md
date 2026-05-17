---
owner: Roldão
revisado-em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
modulo: garantia
dominio: operacao
relacionados:
  - docs/comum/glossario.md
---

# Glossário — Módulo Garantia

> Termos específicos. Transversais em `docs/comum/glossario.md`.

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| Garantia de serviço | Compromisso de refazer serviço executado sem custo dentro de prazo | "retrabalho gratuito" | tipo de garantia vinculada a uma OS-mãe concluída | CDC + boa prática |
| Garantia de peça | Compromisso de substituir peça aplicada que falhou dentro de prazo | "troca" | tipo de garantia vinculada a peça específica usada na OS-mãe | CDC + fornecedor |
| Garantia de equipamento vendido | Compromisso pós-venda de equipamento entregue ao cliente | "garantia da venda" | tipo de garantia vinculada a número de série do equipamento | CDC |
| Garantia procedente | Análise concluiu que a reclamação tem fundamento → não cobra | "garantia válida", "OK garantia" | cobrança bloqueada, custo lança em CUSTO_GARANTIA | módulo |
| Garantia improcedente | Análise concluiu que não há fundamento → cobra normal | "garantia negada" | cobrança liberada, custo lança em CUSTO_SERVIÇO | módulo |
| Garantia parcial | Procedência só de parte do escopo da OS-filha | "meio-meio" | parcela definida em laudo é cobrada | módulo |
| Laudo de garantia | Documento textual que justifica a decisão procedente/improcedente | "parecer" | texto + anexos, gravado imutável após assinatura | INV-001 |
| OS-mãe | OS original cuja garantia foi acionada | "OS de referência" | OS concluída há ≤ prazo, vínculo no banco | módulo OS |
| OS-filha em garantia | OS aberta para executar o atendimento em garantia | "OS de garantia" | OS com flag em_garantia=true e fk OS-mãe | módulo OS |
| Prazo de garantia | Janela em dias durante a qual a garantia vale | "validade" | configurado por tipo (serviço, peça, equipamento) e versionado | tenant |
| Reincidência | Repetição de garantia procedente em cliente/técnico/peça/equipamento dentro de janela | "padrão" | flag REINCIDENTE no dashboard | módulo |
| Garantia do fornecedor | Garantia que o fornecedor da peça oferece ao tenant | "garantia do supplier" | controle separado de envio + retorno + ressarcimento | módulo Fornecedores |
| Ressarcimento | Valor recuperado do fornecedor pela peça em garantia | "reembolso" | crédito ou peça-nova; fecha ciclo de garantia-fornecedor | módulo |
| Bloqueio de cobrança | Sistema impede emissão de NF na OS-filha em garantia procedente | "não cobrar" | flag financeira BLOQUEADO_GARANTIA | INV-001 |
| CUSTO_GARANTIA | Conta gerencial onde lança custo de OS em garantia procedente | "retrabalho" | aparece em dashboard separado do custo normal | módulo |

---

## Como evolui

- Termo novo → adicionar + verificar conflito com glossário comum (hook valida).
- Termo descontinuado → `@deprecated` + janela 3 meses.
