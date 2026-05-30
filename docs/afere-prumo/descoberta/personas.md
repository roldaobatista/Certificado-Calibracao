---
owner: roldao
revisado-em: 2026-05-28
status: stable
ordem-descoberta: 02/17
proximo: docs/descoberta/jornadas.md
idioma: pt-BR
limite-linhas: 200
proposito: descreve quem usa e quem compra o produto.
---

<!--
template: personas.md
destino: docs/descoberta/personas.md
uso: 2-5 personas, 1-2 páginas por persona. Distinguir USUÁRIO de COMPRADOR se forem pessoas diferentes.
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §3
limite: ≤200 linhas. Se passar, fatiar em arquivos por persona dentro de docs/descoberta/personas/.
-->

# Personas — Aferê Prumo

> Personas derivadas da auto-entrevista do dono (`EE-AUTO-001`). Campos não validados com
> a própria pessoa estão marcados `(PROVISÓRIO)`. Nomes são fictícios.
>
> ⚠️ **Nota de status (auditoria 2026-05-29):** o `status: stable` aqui significa **"fundamentado no briefing do
> dono"**, NÃO "validado em campo". O critério de promoção (≥1 entrevista/observação real por persona) **ainda
> não foi cumprido** — fica como **validação marcada para o piloto** (entrevistar ≥3 pessoas por papel interno e
> ≥5 clientes externos; liga a H-003/H-004). Até lá, tratar as personas como hipótese fundamentada, não fato.

## P-001 — Carla — Atendente / comercial (usuário interno)

- **Papel**: atende cliente e monta orçamento das quatro frentes (venda, manutenção, calibração, locação).
- **Contexto**: é uma das **2 pessoas do escritório** que, juntas, absorvem **~50 atendimentos/semana**; muitas conversas em paralelo, pouco tempo por atendimento.
- **Contexto técnico**: fluência digital média; usa WhatsApp e planilha o dia todo. `(PROVISÓRIO)`
- **Frustrações principais**:
  - Responde as mesmas perguntas dezenas de vezes por dia (preço, prazo, "vocês calibram tal balança?").
  - Refaz orçamento do zero porque não há modelo nem histórico fácil de achar.
  - Perde o fio de qual cliente já respondeu e o que ficou pendente.
- **Job to be done**: "Quando chega um cliente no WhatsApp, eu quero responder e orçar na hora, para que eu não acumule fila nem deixe ninguém sem resposta."
- **Métrica de sucesso pra ela**: responder e orçar em minutos, sem refazer trabalho.
- **Comprador?**: não — comprador é P-C-001 (Roldão).

## P-002 — Jorge — Técnico de calibração / manutenção (usuário interno)

- **Papel**: executa calibração com selo (Inmetro/IPEM/RBC) e conserto em campo/oficina; emite certificado. São **5 técnicos em campo**.
- **Contexto**: roda entre clientes, muitas vezes **sem sinal de internet** ("no meio do mato"); precisa do histórico do equipamento e do checklist na mão; preenche OS, tira fotos (antes/durante/depois), registra peças, cliente assina na tela.
- **Requisito crítico**: o app do técnico tem que funcionar **offline-first** (registra sem internet e sincroniza depois).
- **Contexto técnico**: fluência digital média-baixa; prefere algo simples no celular. `(PROVISÓRIO)`
- **Frustrações principais**:
  - Chega no cliente sem o histórico do equipamento (último serviço, peça trocada, data da última calibração).
  - Ordem de serviço no papel se perde ou volta incompleta.
  - Prazo de calibração não tem alarme — descobre que venceu quando o cliente reclama.
- **Job to be done**: "Quando eu atendo um equipamento, eu quero ver e registrar o histórico dele na hora, para que o serviço saia certo e o prazo seguinte fique agendado."
- **Métrica de sucesso pra ele**: histórico e OS num lugar só, sem papel.
- **Recursos de campo (teto do app offline-first)**: checklist/inspeção estruturado; captura de **assinatura na tela**; **foto antes/durante/depois** amarrada à OS; **ler QR/código de barras do equipamento** para puxar o histórico na hora (delight para fluência média-baixa); fila de sincronização com **resolução de conflito**.
- **Comprador?**: não — comprador é P-C-001 (Roldão).

## P-003 — Cliente da Balanças Solution (usuário externo)

- **Papel**: dono de comércio/indústria que compra, aluga, conserta ou calibra balança.
- **Contexto**: quer resolver rápido, normalmente pelo WhatsApp; não quer ligar e esperar.
- **Contexto técnico**: variado; o canal natural é WhatsApp/mensagem. `(PROVISÓRIO)`
- **Frustrações principais**:
  - Demora pra receber resposta e orçamento.
  - É ele quem precisa lembrar do prazo de calibração — ninguém o avisa antes.
  - Não tem onde consultar o que já foi feito no equipamento dele.
- **Job to be done**: "Quando eu preciso de balança ou de calibração, eu quero pedir pelo WhatsApp e ser avisado antes do prazo vencer, para que eu não fique parado nem fora de norma."
- **Métrica de sucesso pra ele**: resposta rápida + aviso de prazo antes de vencer.
- **Comprador?**: não (é cliente final do serviço, não comprador do sistema de IA).

## P-004 — Motorista / logística (usuário interno)

- **Papel**: leva e busca equipamentos (entrega/retirada de locação, deslocamento para serviços em campo).
- **Contexto**: na rua o dia todo; precisa saber o que entregar/buscar, onde e quando.
- **Frustrações**: rota e agenda passadas de forma solta; risco de equipamento esquecido em cliente (locação).
- **Job to be done**: "Quando saio pra rua, eu quero saber exatamente o que entregar/buscar e onde, para não voltar errado nem esquecer item."
- **Comprador?**: não.

## Personas-comprador (distintas dos usuários)

### P-C-001 — Roldão — dono / idealizador
- **Papel**: dono da Balanças Solution; decide e paga o projeto; também é usuário (visão gerencial).
- **Faceta "orquestrador/governador da IA"**: Inbox + Resumo Matinal + Minhas Regras + cockpit fazem dele o "Control Room humano"; seu sucesso é **zerar a fila rápido** e ir **soltando automação com segurança**. **Ver o que a IA fez sem ele** (histórico auditável por agente) é o gatilho de confiança para delegar mais.
- **Critérios de compra** (em ordem): resolver as dores reais > simplicidade pra equipe adotar > custo > prazo de implantação.
- **Objeções típicas**: "minha equipe não vai usar se for complicado"; "já tenho planilha"; "vai dar trabalho migrar"; **"por que não usar um HubSpot/Zoho/CRM com IA que já existe?"** → resposta de produto: nenhum deles tem **equipamento como entidade**, **prazo de calibração por equipamento**, **certificado** nem **app de campo offline** — o coração da nossa operação (ver `concorrentes.md §4`).
- **Como mede ROI**: horas de atendimento economizadas + contratos de calibração que deixam de vencer sem aviso (receita recorrente preservada). Fórmula a fechar quando os números `(A VALIDAR)` forem medidos.

## Personas-cliente (empresas que ASSINAM — revisado 2026-05-28)

> Virada de escopo: a IA é vendida por assinatura aos clientes do Aferê. Logo, **outras empresas de
> calibração/assistência técnica são o PÚBLICO-ALVO pagante** (não anti-personas). Há uma **persona-
> comprador por porte/perfil** — espelhando os perfis A/B/C/D do Aferê. A Balanças Solution é o perfil B.

- **P-CL-001 — Lab pequeno (1-3 pessoas)**: dono faz quase tudo; quer simplicidade extrema; sensível a preço. `(PROVISÓRIO — validar)`
- **P-CL-002 — Empresa média tipo Balanças Solution (~9 pessoas, multi-frente)**: o caso do 1º cliente; equipe de escritório + técnicos de campo + motorista.
- **P-CL-003 — Empresa maior (vários técnicos/filiais)**: precisa de papéis/permissões por setor mais ricos, mais volume, configuração mais fina. `(PROVISÓRIO — validar)`
- **Configurável por empresa**: nº de funcionários, quais agentes ligar, parâmetros (limites, avisos, níveis de automação), papéis/permissões — tudo ajustável no onboarding do tenant.

## Anti-personas (quem NÃO é o público)

- Consumidor final pessoa física comprando balança de cozinha no varejo — não é o cliente B2B alvo.
- Empresa que **não** assina o Aferê (a IA é add-on do Aferê — sem o ERP por baixo, fora do escopo por ora).
- Lab que não atende clientes externos (calibração interna corporativa pura) — outro perfil de produto.

## Como esta lista foi montada

- Entrevistas: 1 auto-entrevista do dono (`EE-AUTO-001`). Falta entrevistar clientes reais (P-003) e a equipe (P-001/P-002).
- Observação direta: pendente.
- Inferência do briefing: papéis, contexto técnico e parte das frustrações — marcados `(PROVISÓRIO)`.
- Dados de mercado: pendente (ver `concorrentes.md`).

## Critério para promover de `draft` para `stable`

- [ ] Cada persona validada com pelo menos 1 entrevista real ou observação direta.
- [ ] Comprador e usuário distintos quando aplicável.
- [ ] Anti-personas explícitas.
- [ ] Frustrações citam gatilho concreto (sem "é difícil", "não é prático" — qualificar).
