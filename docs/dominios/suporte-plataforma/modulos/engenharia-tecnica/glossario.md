---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/comum/glossario.md
---

# Glossário do módulo Engenharia Técnica

> Termos específicos deste módulo. Transversais ficam em `docs/comum/glossario.md`.

---

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| Projeto Técnico | Conjunto de artefatos (desenho, BOM, memorial, cálculos) que descreve uma solução técnica | "projeto" sozinho | pasta lógica que agrupa revisões | — |
| Revisão | Versão imutável de um Projeto Técnico identificada por letra (A, B, C...) | "versão" no contexto de software | snapshot aprovado ou rascunho | ABNT |
| Desenho Técnico | Representação gráfica (CAD, PDF, imagem) anexa ao projeto | "imagem", "PDF" sozinho | arquivo anexo classificado como desenho | — |
| Diagrama Elétrico | Esquema com componentes elétricos e conexões | "esquemático" | anexo classificado como diagrama | — |
| Esquema de Ligação | Diagrama focado em como conectar fios/pinos | "wiring diagram" | anexo classificado como esquema | — |
| BOM | Bill of Materials / Lista Técnica de Materiais — itens, quantidade, posição | "lista de peças" | tabela estruturada de componentes | ISO 10303 |
| Memorial Descritivo | Documento estruturado com escopo, premissas, soluções e normas | "relatório técnico" sozinho | doc gerado a partir de formulário | NBR |
| Especificação Técnica | Conjunto de parâmetros técnicos (capacidade, IP, tensão, classe) | "ficha técnica" | bloco de campos estruturados | — |
| Cálculo Técnico | Memória de cálculo (dimensionamento, balanço, deflexão) | "memória de cálculo" | planilha anexa + campos-chave | — |
| Biblioteca de Componentes | Cadastro centralizado de itens reutilizáveis com fabricante/modelo/datasheet | "catálogo", "componentes" | menu "Engenharia > Biblioteca" | — |
| Componente | Item da biblioteca (sensor, motor, célula, relé, controlador) | "peça" sozinho (peça é Estoque) | linha da biblioteca | — |
| Datasheet | PDF do fabricante com especificações do componente | "manual" | anexo do componente | — |
| Aprovação Técnica | Ato formal do engenheiro responsável que valida revisão | "validação", "OK" | status `aprovada` + assinatura | CREA/CFT |
| Engenheiro Responsável | Pessoa com CREA ativo que assina aprovação | "RT" | persona aprovador | CREA |
| Revisão Obsoleta | Revisão marcada como não-utilizável mas mantida no histórico | "deletada" | flag visual + filtro default exclui | NBR |
| Diff de Revisão | Comparação lado-a-lado entre duas revisões | "comparação" | tela "comparar A vs B" | — |
| Anexo CAD | Arquivo nativo de software CAD (DWG, DXF, EPLAN, KICAD) | "fonte" sozinho | upload classificado | — |
| Rastreabilidade Bidirecional | Capacidade de navegar projeto↔OS↔Orçamento↔Equipamento nos dois sentidos | "link" | "ver onde é usado" | — |

---

## Como esta lista evolui

- Termo novo → adicionar + verificar conflito com glossário comum (hook).
- Termo descontinuado → `@deprecated` + janela 3 meses.
- Mudança de definição → bump CHANGELOG.

## Convenções

- Termos em PT-BR. Inglês quando virou padrão mercado (BOM, CAD, datasheet).
- Origens regulatórias citadas quando aplicável (NBR, ISO, CREA).
