---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
---

# Personas do módulo App do Técnico

> Personas **específicas** deste módulo. Transversais em `../../personas.md` e `docs/comum/personas.md`.

---

## Persona 1: Técnico de Campo (Field Technician)

**Identidade:** Profissional de assistência técnica/metrologia, 22-55 anos, formação técnica em mecânica/eletrônica/metrologia, dirige veículo da frota (próprio ou da empresa), passa 70-90% do dia fora da base. Tem celular Android intermediário (faixa R$ 1.500–2.500). Pouca paciência com app lento ou com muitos cliques. Trabalha em ambientes com sinal ruim (galpões industriais, zonas rurais, subsolos).

**Goals deste módulo:**
- Ver agenda do dia ao acordar sem abrir email.
- Não digitar duas vezes a mesma coisa (anotar em papel + redigitar na base).
- Documentar serviço com foto/checklist sem perder tempo.
- Receber peça em campo sem voltar à base.
- Lançar despesa quando acontece (não acumular comprovante no bolso).
- Conversar com a equipe sem usar WhatsApp pessoal.

**Frustrations específicas:**
- App que trava quando o sinal cai.
- Formulário longo com muitos campos opcionais.
- Botão pequeno demais pra usar com luva.
- App que descarrega bateria do celular em 4h.
- Perder trabalho de um dia inteiro por crash de sync.

**Jornada típica:**
1. Acorda, abre o app, vê agenda do dia ordenada por horário e proximidade.
2. Toca "Iniciar deslocamento" do primeiro atendimento; app abre Waze.
3. Chega, faz check-in GPS, inicia serviço.
4. Executa, marca peças consumidas, tira fotos, completa checklist.
5. Cliente assina aceite na tela; PDF gerado offline.
6. Vai pra próximo cliente; tudo sincroniza em background quando passa por área com 4G.
7. Fim do dia: lança despesas, prestação de contas se for fim de viagem.

**Devices:** mobile (Android primário, iOS secundário). Tablet eventualmente.
**Frequência:** diário, intensivo (4-12h/dia em uso ativo).

---

## Persona 2: Coordenador de Campo (Field Coordinator)

**Identidade:** Supervisor que comanda 3-15 técnicos. Fica na base mas usa o app pra simular o que o técnico vê e responder dúvidas. Aprovador de adiantamentos, mediador de conflitos de sync, distribuidor de OS de última hora.

**Goals deste módulo:**
- Aprovar adiantamento em <1 dia.
- Resolver conflito de sync sem perder dado.
- Realocar OS entre técnicos via app (não precisa abrir web).
- Receber notificação imediata se técnico ficou offline mais que o esperado.

**Frustrations específicas:**
- Conflito de sync sem diff visual claro.
- Adiantamento sem trilha de aprovação.
- Não saber por que técnico não chegou ao cliente.

**Jornada típica:**
1. Manhã: vê painel de técnicos no campo (último check-in, agenda).
2. Técnico solicita peça → aprova/recusa em ≤1min.
3. Conflito de sync escalado → revisa diff e decide qual versão prevalece.
4. Fim do dia: revisa prestações de contas pendentes.

**Devices:** mobile (espelha visão técnico) + web (operações administrativas).
**Frequência:** diário.

---

## Convenções

- Persona específica = papel que tem responsabilidade ÚNICA neste módulo.
- Técnico de Campo aparece também em Agenda, OS, Estoque — promover pra `../../personas.md` se confirmado em ≥3 módulos.
- Coordenador de Campo idem.
- Hook valida não-duplicação entre os 3 níveis.
