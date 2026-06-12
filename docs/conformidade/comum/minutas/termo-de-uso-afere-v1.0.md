---
owner: roldao
revisado-em: 2026-06-12
status: minuta
aguarda-revisao-oab: true
selo: "MINUTA — REQUER VALIDAÇÃO OAB ANTES DE EXECUÇÃO/PUBLICAÇÃO"
---

# Termo de Uso — Plataforma Aferê

> ❄️ **CONGELADO (decisão Roldão 2026-06-12, auditoria de cerimônia R19):** emendas de cláusulas por módulo estão suspensas até os gates GATE-LGPD-TOU-1 / GATE-LGPD-DPA-MASTER-1. O subagente `advogado-saas-regulado` atua no P2 (revisão de plano) SOMENTE para risco de DESIGN (estrutura de dado, texto de tela visível ao titular) — não para polir prosa desta minuta que será reescrita por OAB humana pré-produção.

> Minuta jurídica preparada por subagente IA (`advogado-saas-regulado`). **Não substitui parecer de advogado(a) com OAB ativa.** Antes de publicação ou aceite com tenant externo, esta minuta deve ser revista por advogado humano.

---

## 1. Objeto e Aceite

1.1. Estes Termos regulam o uso da plataforma Aferê (doravante "Plataforma"), software-como-serviço (SaaS) multi-tenant para gestão de empresas de assistência técnica e laboratórios de calibração metrológica, oferecida pela [RAZÃO SOCIAL — a definir] (doravante "Aferê", "Contratada" ou "Operador").

1.2. O aceite destes Termos por agente representante do tenant ("Contratante", "Controlador" ou "Cliente Corporativo") com poderes para tanto vincula a pessoa jurídica contratante.

1.3. O Cliente Corporativo declara ter lido, compreendido e aceito integralmente estes Termos, a Política de Privacidade e o DPA (Data Processing Agreement) referenciado no item 6.

---

## 2. Escopo dos Serviços

2.1. A Plataforma oferece, conforme plano contratado:
- gestão de clientes finais do Contratante;
- gestão de equipamentos sob custódia ou propriedade do Contratante e/ou de seus clientes;
- emissão e gestão de Ordens de Serviço (OS) e Atividades;
- gestão metrológica conforme ISO/IEC 17025 (calibração, padrões, certificados);
- emissão de documentos fiscais (NFS-e via integração);
- gestão financeira básica (contas a receber/pagar, comissões);
- outros módulos conforme catálogo vigente.

2.2. **Não está no escopo** desta Plataforma:
- substituir Responsável Técnico (RT) credenciado do Contratante (atribuição pessoal do RT);
- substituir advogado, contador, auditor ou consultor RBC do Contratante;
- emitir certificados ou assinar documentos com chave do Contratante (assinatura A3 é client-side via Lacuna);
- prestar serviço de DPO ao Contratante (Contratante mantém seu próprio Encarregado).

---

## 3. Cadastro e Acesso

3.1. Cadastro do tenant exige razão social, CNPJ ativo, e-mail corporativo, telefone, dados do administrador inicial e aceite destes Termos + Política de Privacidade + DPA.

3.2. Senhas são pessoais e intransferíveis. MFA é obrigatório para perfis administrador, financeiro e RT.

3.3. O Contratante é responsável por manter atualizada a lista de usuários ativos e revogar acessos de pessoas desligadas em até 48h (interligado com INV-INT-011).

---

## 4. Responsabilidades

4.1. **Da Aferê:**
- manter a Plataforma operacional conforme SLA do plano contratado;
- aplicar medidas técnicas e organizacionais de segurança (LGPD art. 46);
- notificar o Contratante de incidentes de segurança que afetem seus dados em até 24h (DPA cl. 10.1);
- manter a documentação técnica e regulatória atualizada;
- atender direitos do titular (art. 18 LGPD) na qualidade de Operador, redirecionando ao Controlador quando aplicável.

4.2. **Do Contratante:**
- usar a Plataforma para fins legítimos e dentro do escopo contratado;
- não tentar contornar limites técnicos, de plano ou de feature flags;
- garantir que seus usuários conheçam e cumpram estes Termos;
- responder pela conduta de seus usuários e clientes finais;
- manter dados de cadastro atualizados;
- nomear formalmente seu próprio DPO/Encarregado;
- não usar a Plataforma para emissão de documento regulatório fora do seu escopo acreditado.

---

## 5. Suspensão e Encerramento

5.1. A Aferê pode suspender o acesso do Contratante em caso de:
- inadimplência ≥ 30 dias com prévio aviso;
- uso indevido confirmado;
- ordem judicial;
- requisição da ANPD ou de órgão regulador competente.

5.2. O Contratante pode encerrar o contrato a qualquer momento com aviso prévio de 30 dias.

5.3. Após encerramento, dados sob custódia do Contratante são preservados conforme matriz de retenção (`docs/conformidade/comum/retencao-matriz.md`). Pedido de eliminação anterior ao prazo segue ADR-0021 (Zonas A/B/C).

5.4. Backup do tenant em formato exportável é disponibilizado por até 30 dias após encerramento, mediante solicitação formal.

---

## 6. Dados Pessoais e LGPD

6.1. O tratamento de dados pessoais é regido pela Política de Privacidade (`politica-de-privacidade-afere-v1.0.md`) e pelo Data Processing Agreement (DPA — `dpa-modelo.md`), que são parte integrante destes Termos.

6.2. A Aferê atua como Operador (LGPD art. 39) em relação aos dados de Clientes Finais do Contratante; o Contratante atua como Controlador.

6.3. A Aferê atua como Controlador em relação a dados de cadastro do próprio Contratante (razão social, dados de contato, dados financeiros do plano contratado).

6.4. Direitos do titular (art. 18) são atendidos em prazo de 15 dias corridos (Res. CD/ANPD 2/2022).

---

## 7. Propriedade Intelectual

7.1. A Plataforma, código-fonte, marcas, layout e documentação são de propriedade exclusiva da Aferê.

7.2. Dados inseridos pelo Contratante e por seus Clientes Finais permanecem de titularidade do Contratante (Operador apenas trata em seu nome).

7.3. É vedado ao Contratante:
- engenharia reversa do código;
- redistribuição, sublicenciamento ou revenda da Plataforma;
- uso da marca Aferê fora dos termos autorizados.

---

## 8. Limite de Responsabilidade

8.1. **Limite máximo de responsabilidade da Aferê:** o MAIOR entre:
(a) R$ 500.000,00 (quinhentos mil reais); ou
(b) 12 (doze) mensalidades efetivamente pagas pelo Contratante nos 12 meses anteriores ao evento gerador.

8.2. **Limite agregado anual:** 36 (trinta e seis) mensalidades efetivamente pagas no período.

8.3. **Cláusula penal específica vazamento de dados:** em caso de vazamento confirmado de dados pessoais por culpa exclusiva da Aferê, multa contratual de 6 (seis) mensalidades efetivamente pagas, sem prejuízo das demais sanções previstas no DPA.

8.4. **Excluídos do escopo de responsabilidade:**
- danos indiretos, lucros cessantes ou perda de chance além dos limites acima;
- danos decorrentes de uso indevido ou contra estes Termos pelo Contratante;
- danos por força maior, caso fortuito ou indisponibilidade de sub-operador (sujeito a coberturas próprias — ver ADR-0028);
- danos por dados inseridos pelo Contratante que violem direito de terceiro.

---

## 9. Anexo III — Disclaimer de Inteligência Artificial

9.1. A Plataforma Aferê utiliza agentes de IA para geração de código, assistência operacional e processamento. **Toda decisão regulatória final (emissão de certificado, regra de decisão ISO 17025, assinatura A3, emissão fiscal) requer ação humana qualificada** — a IA é assistente, não decisora.

9.2. Outputs marcados como "consultivo" não substituem parecer profissional licenciado (OAB, CREA, CRC, CGCRE).

9.3. A defesa Aferê em caso de falha imputada à IA está documentada em ADR-0019 (responsabilidade civil código IA) — controles compensatórios versionados disponíveis para due diligence.

---

## 10. Foro e Resolução de Conflitos

10.1. Eventuais litígios serão resolvidos por **arbitragem na Câmara de Arbitragem do Mercado de São Paulo (CAM-CCBC)**, com sede em São Paulo/SP, regras vigentes na data da disputa, em língua portuguesa.

10.2. Para questões consumeristas (B2C — não aplicável quando ambas as partes são PJ), prevalece o foro do consumidor.

---

## 11. Disposições Gerais

11.1. **Alteração destes Termos:** mediante aviso prévio de 30 dias por e-mail ao administrador do tenant. Continuidade de uso configura aceite.

11.2. **Cessão:** o Contratante não pode ceder direitos/obrigações destes Termos sem aprovação prévia escrita da Aferê.

11.3. **Sub-operadores Aferê:** listados em `subprocessadores.md`. Atualização com aviso prévio de 30 dias; direito de objeção do Contratante por motivo justificado.

11.4. **Disposições legais aplicáveis:** Constituição Federal, Código Civil, Marco Civil da Internet (Lei 12.965/2014), LGPD (Lei 13.709/2018), CDC quando aplicável, ISO/IEC 17025 quando aplicável.

11.5. **Idioma:** estes Termos são redigidos em português (Brasil) e prevalecem sobre quaisquer traduções.

---

## 12. Pendências bloqueantes pré-publicação

- [ ] Razão social da entidade Aferê definida e CNPJ ativo
- [ ] Validação OAB destes Termos
- [ ] DPO formalmente designado
- [ ] DPAs com sub-operadores assinados (`subprocessadores.md` § "pendente")
- [ ] Política de Privacidade publicada
- [ ] DPA modelo aceito e assinável

---

**FIM Termo de Uso v1.0 — MINUTA — REQUER VALIDAÇÃO OAB**
