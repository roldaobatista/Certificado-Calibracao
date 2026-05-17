---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
---

# Personas do módulo Marketplace

> Personas específicas. Personas transversais ficam em `../../personas.md` (domínio) e `docs/comum/personas.md` (produto).

---

## P-MKT-01: Visitante anônimo

**Identidade:** pessoa que chega ao site do tenant pela primeira vez (busca Google, WhatsApp, indicação). Pode ser pessoa física ou comprador de empresa. Não tem login. Tempo de atenção curto (< 3 min até desistir).

**Goals deste módulo:**
- Entender rapidamente o que a empresa oferece.
- Ver preço (ou faixa) sem precisar ligar.
- Pedir orçamento sem ter que cadastrar conta completa.

**Frustrations específicas:**
- Site que esconde preço atrás de "fale conosco".
- Formulário que pede CNPJ, CEP, fax e cargo só para mostrar produto.
- Não saber se a empresa atende a região dele.

**Jornada típica:**
1. Chega pelo Google buscando "calibração balança em [cidade]".
2. Vê vitrine com serviços + faixa de preço.
3. Adiciona "calibração balança 30kg" ao carrinho.
4. Preenche nome + telefone + e-mail + termo LGPD.
5. Envia solicitação e recebe confirmação por WhatsApp.

**Devices:** mobile (60%) + desktop (40%).
**Frequência:** uma única visita até virar lead; depois vira P-MKT-02.

---

## P-MKT-02: Cliente cadastrado autoatendimento

**Identidade:** cliente que já fechou pelo menos 1 OS com o tenant e tem login na área do cliente. Geralmente comprador técnico (engenheiro, gerente de manutenção) que recebe a senha após primeiro fechamento.

**Goals deste módulo:**
- Pedir novo serviço sem repetir cadastro.
- Acompanhar status de OS em andamento sem ter que ligar.
- Baixar certificados/notas/faturas históricos.
- Aprovar orçamento pendente.
- Assinar/cancelar serviços recorrentes.

**Frustrations específicas:**
- Ter que pedir 2ª via de certificado por e-mail.
- Não conseguir ver previsão de chegada do técnico.
- Não saber se a fatura está em atraso ou paga.

**Jornada típica:**
1. Login na área do cliente.
2. Vê aba "OS em andamento" — calibração agendada pra amanhã.
3. Baixa fatura de mês passado.
4. Solicita renovação do contrato de calibração anual (recorrente).

**Devices:** desktop (escritório) + mobile (consulta rápida).
**Frequência:** semanal/mensal.

---

## P-MKT-03: Gestor de catálogo do tenant

**Identidade:** funcionário comercial/marketing do tenant que decide o que aparece na vitrine, qual é destaque, qual tabela de preço é pública, qual é privada. Geralmente o próprio dono em empresa pequena; gerente comercial em empresa média.

**Goals deste módulo:**
- Curar vitrine (destaques, ordenação, ocultar itens).
- Definir tabela pública × tabela por cliente.
- Acompanhar funil de conversão (visita → solicitação → fechamento).
- Ajustar imagens, descrições, FAQs por item.

**Frustrations específicas:**
- Ter que editar HTML para mudar destaque.
- Não ver quantas pessoas viram o item antes de pedir.
- Site que mostra item esgotado/descontinuado.

**Jornada típica:**
1. Abre dashboard de funil — vê que serviço X tem 200 visualizações e 0 carrinhos.
2. Investiga: descrição confusa.
3. Edita descrição + adiciona foto melhor.
4. Marca como destaque por 7 dias.

**Devices:** desktop.
**Frequência:** semanal.

---

## Convenções

- Persona específica = papel com responsabilidade ÚNICA neste módulo.
- Se persona aparece em ≥2 módulos com mesma responsabilidade, promover para `../../personas.md`.
- Se aparece em ≥2 domínios, promover para `docs/comum/personas.md`.
