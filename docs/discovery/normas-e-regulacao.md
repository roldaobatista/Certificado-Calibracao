# Discovery — Normas e regulação

> **Artefato Rodada 0** — mapeamento das normas e regulações que afetam cada módulo do ERP (assistência técnica + calibração).
> **Atualizado:** 2026-05-16. Toda afirmação carrega fonte; marcações `[a confirmar]` indicam dado de fonte secundária ou cuja vigência precisa ser revalidada antes de virar invariante de produto.
> **Escopo:** consolidar para entrada em `REGRAS-INEGOCIAVEIS.md` e priorizar matriz município × NFS-e (risco #1 do tema fiscal).

---

## 1. NFS-e — situação por município (urgente)

### 1.1 Quadro nacional (Reforma Tributária + LC 214/2025)

- **Lei Complementar 214/2025 — art. 62**: a partir de **01/01/2026** todos os municípios e o DF devem usar o **padrão nacional da NFS-e**, com compartilhamento obrigatório de NFS-e via Ambiente de Dados Nacional (ADN). Municípios que não aderirem podem perder transferências voluntárias da União e ter limitações de participação no IBS. ([abrasf.org.br](https://abrasf.org.br/comunicacao/noticias/nova-fase-nfs-e-adesao-ao-modelo-nacional-encerra-atualizacoes-do-modelo-abrasf), [folhape.com.br](https://www.folhape.com.br/economia/padronizacao-da-nota-de-servicos-sera-obrigatoria-em-2026-e-ameaca/430999/))
- **Resolução CGSN 169/2022**: obriga MEI prestador de serviço a usar a NFS-e Padrão Nacional desde set/2023. ([legisweb.com.br](https://www.legisweb.com.br/legislacao/?id=434589))
- **Resolução CGSN 189/2026**: torna obrigatória a NFS-e Padrão Nacional para **todas** as ME e EPP do Simples Nacional a partir de **01/09/2026** (emissor web, app ou API). ([gov.br/receitafederal](https://www.gov.br/receitafederal/pt-br/assuntos/noticias/2026/abril/nfs-e-de-padrao-nacional-sera-obrigatoria-para-optantes-do-simples-nacional))
- **ABRASF** anunciou o **encerramento das atualizações do modelo ABRASF** (último 2.04, 2018). Quem está em ABRASF "puro" sem ponte com ADN vai ficar sem suporte. ([abrasf.org.br](https://abrasf.org.br/comunicacao/noticias/nova-fase-nfs-e-adesao-ao-modelo-nacional-encerra-atualizacoes-do-modelo-abrasf), [totvs.com](https://www.totvs.com/blog/fiscal-clientes/abrasf-anuncia-fim-de-atualizacoes-do-modelo-proprio-de-nfs-e-e-reforca-adocao-do-padrao-nacional/))
- **Modelos de adesão possíveis** (cada município escolhe):
  1. **Emissor Nacional exclusivo** (web/app/API gov.br) — município abandona sistema próprio.
  2. **Sistema próprio integrado ao ADN** — município mantém portal/WS local, mas espelha cada NFS-e para o ADN.
- **Novos campos obrigatórios (em vigor 01/01/2026)**: grupos IBSCBS, código **NBS** (9 dígitos), **INDOP/cIndOp** (6 dígitos). Em 2026 IBS/CBS são informativos (alíquotas simbólicas) e a ausência **não rejeita** a nota — mas a obrigação legal segue. ([reformatributaria.com](https://www.reformatributaria.com/brasil/cidade-de-sao-paulo-lanca-manual-com-informacoes-sobre-novo-layout-da-nfs-e/))

> **Resposta direta à pergunta "NFS-e Nacional já entrou em vigor?":**
> **Sim, parcialmente.** Para MEI: desde set/2023. Para todos os municípios (lado da prefeitura): desde 01/01/2026. Para ME/EPP do Simples Nacional: **obrigatória a partir de 01/09/2026** (CGSN 189/2026). Para demais contribuintes (Lucro Real/Presumido): obrigatória desde 01/01/2026, com transição até 31/12/2032 e 2026 considerado "período de testes" (LC 214/2025).

### 1.2 Matriz município × padrão NFS-e (15 prioritários)

| Município | Modelo de adesão | Status 05/2026 | Fonte |
|---|---|---|---|
| **São Paulo (SP)** | Sistema próprio mantido, com adaptação ao padrão nacional e integração ao ADN. **Não** migra pro Emissor Nacional. | Em vigor com novo layout. | [wk.com.br](https://wk.com.br/blog/municipio-sao-paulo-mantera-emissor-proprio-nfse/), [machadomeyer.com.br](https://www.machadomeyer.com.br/pt/inteligencia-juridica/publicacoes-ij/tributario-ij/municipios-de-sao-paulo-e-rio-de-janeiro-se-pronunciam-sobre-o-novo-leiaute-da-nfs-e) |
| **Rio de Janeiro (RJ)** | **Emissor Nacional exclusivo** (Resolução SMF 3.419/2026). | Obrigatório desde 01/01/2026. | [notagateway.com.br](https://notagateway.com.br/blog/rio-de-janeiro-rj-regulamenta-emissao-da-nfs-e-no-padrao-nacional/), [totvs.com](https://www.totvs.com/blog/fiscal-clientes/nfs-e-nacional-no-rio-de-janeiro-novas-regras-obrigacoes-e-medidas-transitorias/) |
| **Belo Horizonte (MG)** | Adesão gradual ao Emissor Nacional. | Em produção desde jan/2026. | [wk.com.br](https://wk.com.br/blog/modelo-abrasf-de-nfse-e-encerrado/) |
| **Curitiba (PR)** | Migração por grupos para Emissor Nacional. | Em produção (última leva 01/01/2026). | [ajuda.sankhya.com.br](https://ajuda.sankhya.com.br/hc/pt-br/articles/35830167578263-Saiba-Mais-Migra%C3%A7%C3%A3o-das-Prefeituras-para-o-Emissor-Nacional) |
| **Porto Alegre (RS)** | **Emissor Nacional exclusivo** desde 01/11/2025; **API DANFSe local descontinuada em 01/07/2026** — sistemas externos têm que se adaptar ao DANFSe nacional até essa data. | Obrigatório; deadline DANFSe 07/2026. | [prefeitura.poa.br](https://prefeitura.poa.br/smf/noticias/nfs-e-nacional-passa-ser-obrigatoria-em-porto-alegre-em-1o-de-novembro), [prefeitura.poa.br DANFSe](https://prefeitura.poa.br/smf/noticias/empresas-terao-ate-julho-para-adaptar-sistemas-para-emissao-do-danfse) |
| **Salvador (BA)** | Adesão pioneira ao padrão nacional desde fim de 2022 (piloto da Receita). | Em produção. | [qive.com.br](https://qive.com.br/blog/nfse-nacional) |
| **Recife (PE)** | **Emissor Nacional exclusivo** desde 01/01/2026 (Portaria SMF 42/2025). Sistema local segue apenas pra DAM, confissão e consulta. | Obrigatório. | [recifeemdia.recife.pe.gov.br](https://recifeemdia.recife.pe.gov.br/nfsetransicao) |
| **Fortaleza (CE)** | Adesão pioneira ao padrão nacional desde fim de 2022. | Em produção. | [qive.com.br](https://qive.com.br/blog/nfse-nacional) |
| **Brasília (DF)** | **Modelo SP** — emissor próprio ISSnet + integração ao ADN (espelhamento obrigatório). ABRASF antigo desativado em 01/01/2026. | Obrigatório desde 01/01/2026. | Secretaria de Economia DF + Contábeis |
| **Goiânia (GO)** | Sistema próprio (**SGISS**, Decreto 2.824/2025) integrado ao padrão nacional/ABRASF 2.04. | Em produção desde 01/10/2025. | [pedroreisconsultoria.com.br](https://pedroreisconsultoria.com.br/novo-modelo-de-nfs-e-padrao-nacional-abrasf-2-04-prefeitura-de-goiania/) |
| **Manaus (AM)** | **Emissor Nacional exclusivo** (web/app/API). | Obrigatório desde 01/2026. | [manaus.am.gov.br](https://www.manaus.am.gov.br/noticia/financas/prefeitura-semef-nfs-e/) |
| **Campinas (SP)** | Substituição total do ABRASF antigo pelo padrão nacional + integração ao ADN. | Obrigatório desde 01/01/2026. | [escritoriotaquaral.com.br](https://www.escritoriotaquaral.com.br/adequacao-nfs-e-campinas-reforma-tributaria/) |
| **Florianópolis (SC)** | **Emissor Nacional exclusivo** desde 01/12/2025 (Decreto 28647/2025). Nota Fiscal Avulsa descontinuada. | Obrigatório (antecipou ao prazo nacional). | [crcsc.org.br](https://www.crcsc.org.br/noticia/view/48179/florianopolis-inicia-migracao-para-o-emissor-nacional-de-nota-fiscal-de-servico-eletronica), [cdlflorianopolis.org.br](https://www.cdlflorianopolis.org.br/postagem/noticias/emissao-da-nfs-e-nacional-passa-a-valer-em-florianopolis-a-partir-de-1-de-dezembro) |
| **Vitória (ES)** | **Emissor Nacional exclusivo** desde 01/01/2026. DME e Serviços Tomados continuam no ISISS local. | Obrigatório. | [vitoria.es.gov.br](https://vitoria.es.gov.br/noticia/vitoria-adota-sistema-emissor-nacional-de-nota-eletronica-55000), [notagateway.com.br](https://notagateway.com.br/blog/vitoria-es-adota-o-sistema-emissor-nacional-de-nfs-e-a-partir-de-1o-de-janeiro-de-2026/) |
| **Natal (RN)** | **Duas fases**: (i) emissor próprio "Nota Natalense" adaptado ao padrão nacional desde 01/01/2026 (Portaria 078/2025, layout 2.1); (ii) **migração total para Emissor Nacional em 01/05/2026**. | Em transição. | [legisweb.com.br](https://www.legisweb.com.br/noticia/?id=32865), [totvs.com](https://www.totvs.com/blog/fiscal-clientes/natal-migrara-emissao-da-nfs-e-para-o-emissor-nacional-a-partir-de-maio-de-2026/) |

### 1.3 Provedores homologados (BaaS fiscal)

Os provedores SaaS de NFS-e/NF-e mais usados no mercado BR (todos com cobertura nacional via API REST/SOAP, abstraindo padrão nacional e municípios próprios):

- **Focus NFe** — focusnfe.com.br
- **NFE.io** — nfe.io
- **eNotas** — enotas.com.br
- **PlugNotas** — plugnotas.com.br
- **TecnoSpeed** — tecnospeed.com.br
- **MigrateNotas** — migratenotas.com.br
- **WebmaniaBR** — webmania.com.br
- **Brasil NFe** — brasilnfe.com.br

> **Recomendação técnica:** integrar com **um** BaaS fiscal (Focus, PlugNotas ou TecnoSpeed são os mais maduros) em vez de manter integração direta por município. O custo de manter manualmente o emissor próprio de SP + ADN nacional + variações municipais residuais é alto e instável. **Decisão deve ir pra ADR depois da escolha de stack.**

---

## 2. ISO/IEC 17025 e guias técnicos

### 2.1 ISO/IEC 17025

- **Versão vigente em 05/2026: ISO/IEC 17025:2017** — confirmada por revisão sistemática (systematic review) da ISO com **65 votos a favor da confirmação contra 7 a favor de revisão** (72 votos válidos). A versão fica em vigor por mais 5 anos. ([conformita-rs.com.br](https://www.conformita-rs.com.br/post/a-vers%C3%A3o-atual-da-iso-iec-17025-permanecer%C3%A1-igual-por-mais-5-anos))
- ABNT NBR ISO/IEC 17025:2017 é a versão brasileira oficial.

### 2.2 Cláusulas críticas pro software (resumo de 1-2 linhas)

| Cláusula | O que exige (resumo) |
|---|---|
| **4.2 Confidencialidade** | Laboratório deve garantir confidencialidade das informações obtidas/geradas (cliente, resultados, conhecimento técnico). Acesso por terceiros só com autorização do cliente OU obrigação legal — com notificação ao cliente. **Implica controle de permissão por dado + log de acesso + DPA com cliente.** |
| **6.2 Pessoal** | Define competência, qualificação, treinamento e autorização de pessoal. Inclui requisitos do signatário técnico de certificados. **Sistema precisa registrar autorizações vigentes por escopo e por pessoa.** |
| **6.5 Rastreabilidade metrológica** | Resultados de medição devem ser rastreáveis ao SI por cadeia ininterrupta de calibrações com incertezas declaradas. **Sistema deve guardar a cadeia: instrumento → padrão usado → certificado do padrão → incerteza.** |
| **7.7 Garantia da validade dos resultados** | Monitoramento contínuo da validade: controles internos, intercomparações, ensaios de proficiência, análise de tendências. **Sistema deve ter dashboard de controle estatístico/cartas de controle por método.** |
| **7.8 Relato de resultados** | Define conteúdo mínimo do certificado/relatório, regra de decisão, declaração de conformidade, opiniões e interpretações. **Template do certificado deve ser blindado por validação.** |
| **7.10 Trabalho não conforme** | Procedimento documentado pra ação quando trabalho não atende requisitos. Inclui retenção/comunicação ao cliente e decisão sobre reemissão. **Sistema precisa de workflow de NC com bloqueio de emissão.** |
| **7.11 Controle de dados e gerenciamento da informação** | **A cláusula mais crítica pro software.** Sistemas precisam ser **validados antes de uso** (incluindo software comercial), protegidos contra acesso/alteração não autorizados, com integridade preservada, e qualquer falha tem que ser tratada como NC. **Implica: ambiente validado + change control + backup + trilha de auditoria imutável.** |
| **8.3 Controle de documentos** | Documentos (manuais, procedimentos, formulários) revisados/aprovados antes de uso, com identificação de versão e controle de obsoletos. |
| **8.4 Controle de registros** | Registros mantidos legíveis, recuperáveis, com período de retenção definido. Inclusive registros eletrônicos. |
| **8.5 Ações pra abordar riscos e oportunidades** | Pensamento baseado em risco em todo o sistema de gestão. |
| **8.6 Melhoria** | Ações de melhoria contínua, com input de feedback de clientes (positivo e negativo). |
| **8.7 Ação corretiva** | Quando NC ocorre: reagir, avaliar causa-raiz, implementar, monitorar eficácia. |

Fonte cláusulas: [kayeinstruments.com](https://www.kayeinstruments.com/pt/news/blog-post/iso-iec-17025-2017-the-global-standard-for-calibration-laboratories), [jusbrasil.com.br](https://www.jusbrasil.com.br/artigos/iso-iec-17025-confiabilidade-tecnica-e-padronizacao-em-laboratorios-de-ensaio-e-calibracao/4467231613).

### 2.3 ILAC G-series (estado da arte)

- **ILAC G8:09/2019 — Guidelines on Decision Rules and Statements of Conformity**: vigente. Define como aplicar regras de decisão ao declarar conformidade em certificados (cobre lacuna criada pela 17025:2017 cláusula 7.8.6). ([ilac.org](https://ilac.org/latest_ilac_news/revised-ilac-g8-published/))
- **ILAC G17:01/2021** — Incerteza de medição em **ensaios** (não calibração). ([ilac.org/publications-and-resources/ilac-guidance-series/](https://ilac.org/publications-and-resources/ilac-guidance-series/))
- **ILAC G18:01/2024** — Descrição de escopos de acreditação.
- **ILAC G24:2022** — Determinação de intervalos de recalibração.
- **ILAC P10:07/2020** — Política de rastreabilidade metrológica.

> **Atenção:** o usuário pediu "ILAC G8 — estado da arte da validação de software". **G8 trata de regras de decisão, não de validação de software.** As referências consagradas de **validação de software metrológico** são **WELMEC 7.2** (software em instrumentos de medição regulados) e **OIML D 31** (requisitos pra software de instrumentos legalmente regulados). `[a confirmar]` se Roldão quis dizer G8 mesmo ou WELMEC 7.2.

### 2.4 EURACHEM / CITAC (incerteza)

- **EURACHEM/CITAC Guide CG4 — Quantifying Uncertainty in Analytical Measurement (QUAM)** — **3ª edição, 2012** (sem nova edição até 05/2026). Ellison & Williams. ISBN 978-0-948926-30-3. ([eurachem.org](https://www.eurachem.org/index.php/publications/guides/quam))
- Aplica o GUM (Guide to the Expression of Uncertainty in Measurement) ao contexto químico/analítico.
- Estrutura: (1) Especificação do mensurando → (2) Identificação de fontes de incerteza → (3) Quantificação dos componentes → (4) Cálculo da incerteza combinada.
- Complementar: **EURACHEM/CITAC Guide — Measurement Uncertainty Arising from Sampling** (incerteza de amostragem).
- **EA-4/02** — versão europeia (EA — European co-operation for Accreditation) de referência pra expressão de incerteza em calibração; base do DOQ-CGCRE-008 brasileiro.
- **VIM** — versão vigente em 05/2026 é **JCGM 200:2012** (3ª edição, reedição bilíngue). **VIM 4ª edição (CD)** ainda está em Committee Draft, **não publicado oficialmente**. Correção de erro de doc anterior que citava "JCGM 200:2024".

---

## 3. RBC / INMETRO / CGCRE

### 3.1 Documentos vigentes (com versão)

| Documento | Título | Versão atual | Fonte |
|---|---|---|---|
| **NIT-DICLA-021** | Expressão da incerteza de medição em calibração (alinhado à EA-4/02). | **Revisão 10** (versão vigente no portal CDTN/CGCRE em 05/2026). Erro de doc anterior corrigido. | [Sidoq INMETRO](http://www.inmetro.gov.br/credenciamento/organismos/doc_organismos.asp?tOrganismo=CalibEnsaios) |
| **NIT-DICLA-030** | Rastreabilidade metrológica na acreditação. Define quem (laboratórios, produtores de MR) garante rastreabilidade na cadeia. **Revisão 15 (dez/2024) incluiu item 8.2.6:** Cgcre **não aceita** certificados de calibração que omitam resultados de medição e incertezas associadas. | **Revisão 15** (dez/2024). | [gov.br/cdtn](https://www.gov.br/cdtn/pt-br/assuntos/documentos-cgcre-abnt-nbr-iso-iec-17025/nit-dicla-30) |
| **DOQ-CGCRE-008** | Orientação sobre validação de métodos analíticos (inclui tratamento de incerteza via erro normalizado, tendência, recuperação). | **Revisão 09 (jun/2020)**; portal CDTN atualizou o upload em ago/2024 (data de re-upload, não da revisão). | [gov.br/cdtn DOQ-008](https://www.gov.br/cdtn/pt-br/centrais-de-conteudo/documentos-cgcre-abnt-nbr-iso-iec-17025/doq-cgcre-008/view) |
| **DOQ-CGCRE-019** | Exemplos de estimativa de incerteza em ensaios químicos. | Rev. 04 (abr/2019). | Sidoq INMETRO |
| **DOQ-CGCRE-053** | Exemplos de estimativa de incerteza em ensaios microbiológicos. | Rev. 00 (fev/2014). | Sidoq INMETRO |
| **DOQ-CGCRE-090** | Estimativa de incerteza em vazão/velocidade de fluidos e hidrômetros. | Rev. 00 (jun/2018). | Sidoq INMETRO |
| **DOQ-CGCRE-001** | Documentos necessários pra acreditação de laboratórios. | Rev. 03 (consultar Sidoq). | Sidoq INMETRO |

### 3.2 Outros documentos relevantes pra software de calibração

`[a confirmar se Roldão quer cobertura específica]`:
- **NIT-DICLA-016** — Auditorias internas em laboratórios.
- **NIT-DICLA-028** — Avaliação na acreditação.
- **DOQ-CGCRE-007** — Tratamento de itens não conformes.
- **DOQ-CGCRE-027** — Diretrizes pra calibração de volume.

> **Recomendação:** baixar e cachear o Sidoq na fase de spike técnico — INMETRO publica revisões sem aviso, e usar versão desatualizada gera NC em auditoria de cliente.

---

## 4. LGPD + ANPD

### 4.1 Lei base e atualizações

- **Lei 13.709/2018 (LGPD)** + alterações (Lei 13.853/2019 instituiu ANPD; Lei 14.010/2020; Decreto 10.474/2020 estrutura ANPD; Resolução CD/ANPD 2/2022 agentes de pequeno porte; e seguintes).

### 4.2 Resolução CD/ANPD 15/2024 — comunicação de incidente

- Publicada em **24/04/2024**. ([gov.br/anpd](https://www.gov.br/anpd/pt-br/assuntos/noticias/anpd-aprova-o-regulamento-de-comunicacao-de-incidente-de-seguranca))
- **Atenção a um mito comum:** o prazo **não é 72 horas (GDPR)**, e sim **3 dias úteis** contados do conhecimento de que o incidente afetou dados pessoais — para ANPD (art. 6º) **e** para o titular (art. 9º). Pode ser complementada em até 20 dias úteis. Prazo dobrado pra agentes de pequeno porte. ([anpd Comunicação](https://www.gov.br/anpd/pt-br/canais_atendimento/agente-de-tratamento/comunicado-de-incidente-de-seguranca-cis), [lgpd.ms.gov.br](https://www.lgpd.ms.gov.br/wp-content/uploads/2024/05/REGULAMENTO-DE-COMUNICACAO-DE-INCIDENTE-DE-SEGURANCA-ABRIL-2024-ANPD-.pdf))
- **Art. 10:** controlador deve manter **registro de TODOS** os incidentes (mesmo os que não foram comunicados) por **5 anos mínimo**.
- Demora injustificada → sanção administrativa (art. 52 LGPD).

### 4.3 Resolução CD/ANPD 18/2024 — Encarregado (DPO)

- **Publicada em 16/07/2024 / DOU 17/07/2024 / vigência imediata.** ([in.gov.br DOU](https://www.in.gov.br/en/web/dou/-/resolucao-cd/anpd-n-18-de-16-de-julho-de-2024-572632074), [tjba.jus.br PDF](https://www.tjba.jus.br/extrajudicial/wp-content/uploads/2024/08/RESOLUCAO-ANPD-No-18-Encarregado-de-Dados.pdf))
- Pontos centrais:
  - Designação por **ato formal, escrito, datado e assinado**.
  - Pode ser **pessoa natural ou jurídica** (DPO as a Service é permitido).
  - **Identidade + contato devem ser públicos** no site do agente de tratamento (nome completo se PF; razão social + responsável se PJ).
  - Agente de Tratamento de Pequeno Porte (ATPP, Res. 2/2022): **dispensa** obrigatória da designação.
  - **Operador**: indicação facultativa (mas conta como boa prática).
  - Pode acumular funções e atender múltiplos agentes, desde que sem conflito de interesse.
  - Responsabilidade pela conformidade fica com controlador/operador, não com o DPO.

### 4.4 Enunciado CD/ANPD nº 4 (DPO em multi-tenant)

> **`[a confirmar]`** — busca não retornou texto específico do **Enunciado nº 4** com a interpretação sobre arquiteturas SaaS multi-tenant. Resultados localizaram apenas o Enunciado CD/ANPD 1/2023 (sobre dados de crianças). Precisa ser **consultado direto** no portal www.gov.br/anpd → Atos Normativos → Enunciados, antes de incluir como invariante.

### 4.5 Fiscalização ANPD 2025-2026 (relevante pra SaaS)

- **Mapa de Temas Prioritários 2026-2027** publicado em dez/2025 — 4 eixos: (i) direitos dos titulares; (ii) crianças/adolescentes (ECA Digital, Lei 15.211/2025); (iii) Poder Público; (iv) IA e tecnologias emergentes. ([gov.br/anpd Mapa](https://www.gov.br/anpd/pt-br/assuntos/noticias/anpd-publica-mapa-de-temas-prioritarios-para-o-bienio-2026-2027-e-atualiza-agenda-regulatoria-2025-2026))
- **A "era da orientação" acabou:** desde dez/2024 ANPD abriu fiscalização direcionada a 20 empresas grandes por descumprimento do art. 41 (designação de DPO) + Res. 18/2024. ([truzzi.com.br](https://truzzi.com.br/a-era-da-orientacao-acabou-as-primeiras-multas-da-anpd-e-o-novo-cenario-da-lgpd/), [tiinside.com.br](https://tiinside.com.br/23/09/2025/cinco-anos-da-lgpd-sancoes-timidas-riscos-crescentes/))
- **Sanções disponíveis** (art. 52 LGPD): advertência → multa simples (até 2% do faturamento bruto anual, limitada a R$ 50 mi por infração) → multa diária (Deliberação CD-10/2025).
- **Resolução CD/ANPD 19/2024** — Transferências internacionais de dados pessoais. Crítico pra SaaS multi-tenant em AWS/GCP/Azure. ([sindinfor.org.br](https://sindinfor.org.br/guia-pratico-das-novas-normativas-da-anpd-como-se-preparar-e-evitar-riscos-regulatorios/))
- **Brasil ↔ UE:** reconhecimento mútuo de adequação LGPD/GDPR (maior acordo do tipo globalmente) eleva expectativa de conformidade.
- **ECA Digital (Lei 15.211/2025), vigente desde mar/2026:** qualquer plataforma acessível por menor precisa de configuração de privacidade restritiva por padrão + verificação de idade.

---

## 5. Open Finance / Bacen (cibersegurança)

> Aplicável se o ERP integrar com bancos (extrato OFX, conciliação automatizada, pagamentos via PIX/boleto direto).

- **Resolução BCB 32, de 29/10/2020** — Requisitos técnicos e operacionais do Sistema Financeiro Aberto (Open Finance). Norma central do arranjo. ([openfinancebrasil.org.br](https://openfinancebrasil.org.br/atos-normativos/))
- **Resolução BCB 206/2022** — encaminhamento de proposta de crédito no Open Finance.
- **Resolução BCB 295/2023** — dispensa de participação obrigatória no Open Finance.
- **Resolução BCB 400/2024** — diretrizes da Estrutura de Governança do Open Finance.
- **Resolução BCB 406/2024** — compartilhamento de iniciação de pagamento sem redirecionamento.
- **Instrução Normativa BCB 305/2022** — **Manual de Segurança do Open Finance v4.0** (FAPI 2.0, mTLS, DCR, mensagens assinadas JWS).
- **Resolução CMN/BCB Conjunta 1/2020** — institui o Open Banking no Brasil. `[a confirmar número exato — busca não detalhou]`
- **Resolução Bacen 4.658/2018** — Política de segurança cibernética + requisitos pra processamento e armazenamento de dados e computação em nuvem em instituições financeiras. ([blog.ecotrust.io](https://blog.ecotrust.io/resolucao-4-658-entenda-tudo-sobre-essa-normativa-do-bacen/), [ibliss.com.br](https://www.ibliss.com.br/como-cumprir-a-resolucao-4658-do-bacen/))
  - **Aplica também a prestadores de serviço** que processam dados sensíveis pra instituições reguladas.
  - Política de segurança + nomeação de gestor de segurança + plano de resposta a incidentes + retenção da documentação por **5 anos**.
  - Baseada em ISO 27001/27002 e ISO 22301.
  - Adequação obrigatória: instituições financeiras até 31/12/2021; aprovação da política até 06/05/2019 (financeiras) ou 29/11/2018 (instituições de pagamento).

### 5.1 PIX (2025-2026)

> **Atenção:** a busca **não confirmou a existência de uma "Instrução Normativa BCB 207/2022"** como norma central do PIX. A norma fundadora do PIX é a **Resolução BCB 1, de 12/08/2020** (Regulamento do Pix). O número 207/2022 pode ser confusão; revalidar.

Atualizações relevantes de 2025 ([mattosfilho.com.br](https://www.mattosfilho.com.br/en/unico/banking-3quarter-2025-updates/), [demarest.com.br](https://www.demarest.com.br/forum-pix/)):

- **Resolução BCB 482/2025 (jun/2025)** — Pix por aproximação (NFC) + reforço de segurança no Pix Automático.
- **Resolução BCB 493/2025 (ago/2025)** — Melhoras de segurança no MED (bloqueio imediato ao receber notificação de infração) + nova funcionalidade "**recuperação de fundos**" (opcional desde 23/11/2025, obrigatória a partir de **02/02/2026**) + chave aleatória só pode ser alterada por iniciativa do participante.
- **Resolução BCB 496/2025 (set/2025)** — Instituições de pagamento não autorizadas devem solicitar credenciamento entre 01/01/2026 e 01/05/2026; limite R$ 15.000 por transação pra IP não autorizadas.
- **Instrução Normativa BCB 669/2025 (29/09/2025)** — Novos limites: noturno de R$ 1.000 padrão (PF), salvo solicitação expressa; PJ definidos diariamente conforme perfil de risco.
- **Instrução Normativa BCB 673/2025 (03/10/2025)** — Versão 7.2 do documento "Requisitos Mínimos para a Experiência do Usuário" do Pix.
- **Instrução Normativa BCB 678/2025 (30/10/2025)** — Testes de homologação do MED.
- **Instrução Normativa BCB 634/2025 (jun/2025)** — Verificação contínua de idoneidade do usuário recebedor (CNPJ, CNAE, faturamento, histórico).

---

## 6. Receita Federal / SPED / SEFAZ (NF-e, CT-e)

### 6.1 NF-e modelo 55

- **Ajuste SINIEF 07/05** — instituiu a NF-e. Continua sendo a base normativa.
- **Manual de Orientação ao Contribuinte (MOC) NF-e/NFC-e v7.0** — aprovado pelo Ato COTEPE/ICMS de 26/11/2020. **Permanece como versão vigente em 05/2026**, complementado por Notas Técnicas. ([nfe.fazenda.gov.br](https://www.nfe.fazenda.gov.br/portal/listaConteudo.aspx?tipoConteudo=ndIjl+iEFdE%3D), [confaz.fazenda.gov.br](https://www.confaz.fazenda.gov.br/legislacao/arquivo-manuais/moc7-visao-geral.pdf))
- **Anexos do MOC 7.0**: I (Leiaute), II (DANFE), III (DANFE NFC-e + QR Code v6.0 — mar/2025), Contingência, Integração/Webservices.
- **CSRT (Código de Segurança do Responsável Técnico)** obrigatório em PR após 01/04/2025; outras UFs verificar localmente. `[a confirmar UF a UF]`

### 6.2 Notas Técnicas 2025-2026 (Reforma Tributária)

- **NT 2026.001 — Split Payment**: introduz grupo de informações de vinculação da transação de pagamento nos DF-e (NF-e, NFC-e, CT-e, BP-e, NF3e, NFCom, NFAg, NFGas).
- **2ª NT 2026 — IBS/CBS/IS**: inclusão de campos pra IBS, CBS e IS em NF-e e NFC-e a partir de jan/2026 (caráter informativo em 2026, obrigatório efetivo conforme cronograma da reforma).

### 6.4 CNPJ alfanumérico — IN RFB nº 2.229/2024

- **IN RFB nº 2.229/2024** (publicada 16/10/2024) — vigência **julho/2026**. Novos CNPJs poderão ter letras `[A-Z]` nas 12 primeiras posições (raiz + ordem do estabelecimento); 2 dígitos verificadores continuam numéricos. CNPJs antigos permanecem válidos para sempre.
- **Formato:** `^[A-Z0-9]{12}[0-9]{2}$` (14 caracteres, sempre maiúsculo na persistência).
- **Algoritmo DV:** Módulo 11 com pesos 2–9; conversão de caractere = `ord(c) - 48` (retrocompatível com numérico antigo). Nota Técnica Conjunta NF-e/NFS-e 2025.001 detalha integração fiscal.
- **Códigos de referência Serpro** disponíveis em Python, Java e TypeScript em https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/acoes-e-programas/programas-e-atividades/cnpj-alfanumerico
- **Decisão arquitetural:** ADR-0017 (proposta 18/05/2026).

### 6.3 Contingência NF-e (estado atual)

- **SCAN está MORTO desde 30/09/2014** (NT 007/13). Quem ainda referencia SCAN está com sistema antigo. ([sefaz.pe.gov.br](https://www.sefaz.pe.gov.br/Servicos/nota-fiscal-eletronica/Paginas/Conting%C3%AAncia-SVC-RS.aspx), [enotas.com.br](https://enotas.com.br/blog/tipos-de-contingencia/))
- **Substituído por SVC** (Sefaz Virtual de Contingência):
  - **tpEmis=6** — SVC-AN (Ambiente Nacional)
  - **tpEmis=7** — SVC-RS (Rio Grande do Sul)
- Distribuição de UF (confirmada via auditoria):
  - **SVC-AN**: AC, AL, AP, DF, ES, MG, PB, **PI**, RJ, RN, RO, RR, RS, SC, SE, SP, TO
  - **SVC-RS**: AM, BA, **CE**, GO, MA, MS, MT, **PA**, PE, PR
  - Correção: CE e PA estão em SVC-RS (estavam ambíguos no doc anterior); PI é SVC-AN.
- **EPEC (tpEmis=4)** — Evento Prévio de Emissão em Contingência. Ativo desde 01/12/2014.
- **FS-DA (tpEmis=5)** — em desuso, formulário de segurança.
- **CC-e** (Carta de Correção, art. 7º Ajuste SINIEF 07/05) — corrige erros não tributários; até 30 dias.
- **Cancelamento NF-e** — até 24h.
- **Inutilização de numeração** — pra faixas não usadas no mês.

### 6.4 Endpoints

Endpoints **devem ser obtidos do Portal Nacional** (www.nfe.fazenda.gov.br → Serviços → Webservices) em tempo de homologação — mudam por NT. Schema atual é **NF-e 4.00** (`NFeAutorizacao4`, `NFeRetAutorizacao4`, etc.). Os endpoints SVC-RS 3.10 ainda aparecem em docs antigas mas estão obsoletos pra novos integradores.

### 6.5 Retenção fiscal

- **NF-e (XML autorizado)**: 5 anos (CTN art. 173/174) + recomendação prática de arquivamento permanente.
- **Decreto 3000/99 (RIR/99)** está **REVOGADO** desde 22/11/2018 pelo **Decreto 9.580/2018 (RIR/2018)**. Quem ainda cita 3000/99 está com base legal desatualizada. `[a confirmar art. específico de retenção no RIR/2018]`
- **CT-e**: MOC do CT-e mantido pelo CONFAZ; consultar portal cte.fazenda.gov.br. Versão atual `[a confirmar 4.00 ou superior]`.

---

## 7. Outros

### 7.1 CDC (Lei 8.078/90)

- Aplica quando orçamento aprovado vira contrato de consumo (B2C). PME contratante PF: relação de consumo plena.
- Implicações: direito de arrependimento (7 dias se contratação à distância), inversão do ônus da prova, vícios do serviço.

### 7.2 Marco Civil da Internet (Lei 12.965/2014)

- **Provedor de conexão**: logs por **1 ano** (art. 13). Não se aplica ao ERP — só ISPs.
- **Provedor de aplicação** (PJ, organizada, com fins econômicos): logs de acesso por **6 meses** (art. 15). **Aplica ao ERP SaaS.**
- Logs = data/hora de início e fim + IP de origem.
- Pode haver prorrogação cautelar (autoridade policial, MP) com pedido judicial em 60 dias.
- Sigilo dos logs é obrigatório; quebra só por ordem judicial.
- Fonte: [planalto.gov.br L12965](https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2014/lei/l12965.htm), [conjur.com.br](https://www.conjur.com.br/2025-ago-27/incoerencia-dos-prazos-de-guarda-de-dados-no-marco-civil-o-conflito-nao-solucionado-pelo-stf/).

### 7.3 Acessibilidade

- **Lei Brasileira de Inclusão (Lei 13.146/2015)** — art. 63 obriga sites/apps a serem acessíveis. Decreto 5.296/2004 + e-MAG (Modelo de Acessibilidade em Governo Eletrônico).
- **WCAG 2.1 nível AA** é referência prática. WCAG 2.2 publicado (out/2023) e amplamente recomendado; WCAG 3.0 ainda em draft.
- ECA Digital (Lei 15.211/2025) adiciona requisitos pra menores.

### 7.4 PCI-DSS

- **Versão vigente: PCI DSS 4.0.1** — única versão ativa desde **01/01/2025**; transição obrigatória encerrou em **31/03/2025**. ([panoramaabecs.com.br](https://panoramaabecs.com.br/pci-dss-4-0-1-o-que-muda-com-a-atualizacao/), [botech.info](https://botech.info/br/noticias/pci-dss-v4-0-1-entra-em-vigor-em-janeiro/), [training.pcisecuritystandards.org](https://training.pcisecuritystandards.org/pci-dss-v4-0-timelines-portuguese))
- **Todos os 64 requisitos novos/atualizados (incluindo os 51 com "future date")** são plenamente exigíveis desde 31/03/2025. Sem período de carência.
- 4.0.1 vs 4.0: apenas correções tipográficas e esclarecimentos; sem novos requisitos.
- Áreas críticas: req. **6.4.3** (inventário de scripts em página de pagamento + verificação de integridade) e **11.6.1** (detecção de adulteração) — combate a e-skimming/Magecart; **MFA expandida pra TODAS as contas administrativas** (inclusive rede interna); abordagem personalizada baseada em objetivos.
- **Aplicabilidade ao projeto:** SE o ERP processar/transmitir/armazenar dados de cartão (PAN, CVV, dados de autenticação) **diretamente**, é PCI-DSS. **Recomendação técnica:** usar gateway/PSP (Stripe, Pagar.me, PagSeguro, Asaas) com tokenização para reduzir escopo ao mínimo (SAQ A).
- PCI-DSS não é regulatório no BR, mas é exigido contratualmente pelas bandeiras.

### 7.5 Sigilo médico / saúde (se ERP atender laboratórios clínicos)

- **ABNT NBR ISO 15189** — laboratórios clínicos.
- **Resolução CFM 1.821/2007 + Manual de Certificação SBIS-CFM** — prontuário eletrônico.
- LGPD trata dados de saúde como **sensíveis** (art. 5º, II) — base legal específica.

---

## 8. Próximos passos (entrada pra `REGRAS-INEGOCIAVEIS.md` e backlog)

### 8.1 Invariantes a criar (de produto/sistema) — atualizada pós-auditoria + perfis

> **Versão pós-auditoria + decisão de perfis (16/05/2026 — Auditor 2 + Roldão) + auditoria batch 2 (17/05/2026 — Auditor 2 acessibilidade) + auditoria batch 3 (17/05/2026 — 12 agentes):** invariante #4 quebrado em 3 sub-regras testáveis; invariante #7 movido pra ADR; invariantes #10-#14 adicionados; **INV-015 novo (perfil de empresa)**; **INV-016 novo (WCAG 2.1 AA + PDF/UA — Lei 13.146/2015)**; **INV-017 a INV-020 novos (assinatura digital ICP-Brasil, RT vendor publicado, dossiê de validação por release, jornada UMC Lei 13.103)**; coluna "Escopo por perfil" adicionada. Total: **20 invariantes**.

| # | Invariante | Base normativa | Como vira hook | Escopo por perfil |
|---|---|---|---|---|
| **INV-001** | Trilha de auditoria imutável (`quem, quando, antes, depois`) com hash encadeado, em toda operação que toca certificado de calibração ou documento fiscal | 17025 cl. 7.11 + 8.4 + Marco Civil art. 15 + LGPD art. 37 | Banco com WORM + hash em append-only | **Absoluta (todos perfis)** |
| **INV-002** | Toda emissão de certificado grava cadeia de rastreabilidade completa (instrumento → padrão → certificado do padrão → incerteza). Sem cadeia, emissão bloqueia | NIT-DICLA-030 rev. 15 item 8.2.6 + 17025 cl. 6.5 | Pre-commit hook na emissão | **Absoluta em A; configurável em B, C, D** |
| **INV-003** | Signatário só assina dentro do **escopo de autorização vigente na data da assinatura** | 17025 cl. 6.2 + NIT-DICLA-021 | Validação no momento de assinar; congelar autorização vigente | **Absoluta em A; configurável em B, C, D** |
| **INV-004a** | Nenhum deploy em produção sem aprovação documentada do responsável técnico do laboratório | 17025 cl. 7.11 | CI bloqueia merge/deploy sem registro | **Absoluta em A; configurável em B, C, D** |
| **INV-004b** | Toda alteração em rotina de cálculo de incerteza requer revalidação registrada | 17025 cl. 7.11 + EA-4/02 | Hook detecta mudança em arquivos da rotina; bloqueia merge | **Absoluta em A; configurável em B, C, D** |
| **INV-004c** | A versão do software fica gravada em cada certificado emitido | 17025 cl. 7.11 + boa prática (recall) | Campo obrigatório no template do certificado | **Absoluta (todos perfis)** |
| **INV-005** | Comunicação de incidente LGPD em ≤3 dias úteis (ANPD + titular) + registro de TODOS incidentes por ≥5 anos. ATPP tem prazo dobrado | Res. CD/ANPD 15/2024 art. 6º, 9º, 10 | Workflow obrigatório no painel de incidente | **Absoluta (todos perfis)** |
| **INV-006** | DPO publicado no site (identidade + contato em local de destaque) + canal de titular funcional. ATPP dispensado de DPO mas mantém canal | Res. CD/ANPD 18/2024 | Validação no setup do tenant | **Absoluta (todos perfis)** |
| **INV-007** | NF-e: arquitetura preparada pra SVC-AN/SVC-RS desde dia 0 (não como contingência tardia) | NT 2013/007 + boa prática | Cliente sem SVC configurado: deploy de NF-e bloqueado | **Absoluta (todos perfis)** |
| **INV-008** | Logs de acesso à aplicação retidos por ≥6 meses (recomendado 12 meses) com sigilo | Marco Civil art. 15 | Política de retenção no banco de logs | **Absoluta (todos perfis)** |
| **INV-009** | MFA pra usuários com acesso ao CDE (Cardholder Data Environment) — não só admins | PCI 4.0.1 (expansão) | Validação no login | **Absoluta quando PCI aplica** |
| **INV-010** | Registros 17025 com retenção ≥ ciclo de calibração do cliente + 1 ciclo (tipicamente 5–25 anos) | 17025 cl. 8.4 | Política de retenção por tipo de registro; LGPD base "obrigação legal" | **Absoluta em A; configurável em B, C, D** |
| **INV-011** | Emissão de certificado bloqueia se padrão usado tem calibração vencida | 17025 cl. 6.5 + 7.2 | Pre-commit hook na emissão | **Absoluta em A; configurável em B, C, D** |
| **INV-012** | Workflow de Não Conformidade (cl. 7.10 + 8.7) com bloqueio de emissão até resolução documentada | 17025 cl. 7.10 + 8.7 | NC aberta no instrumento → bloqueio na emissão | **Absoluta em A; configurável em B, C, D** |
| **INV-013** | Confidencialidade cl. 4.2: acesso a dados de cliente do laboratório só com permissão explícita + log de toda visualização (incluindo admins) | 17025 cl. 4.2 | RBAC + audit trail visualização | **Absoluta (todos perfis)** |
| **INV-014** | Aceitação de certificado de calibração de padrão externo bloqueada se omitir resultado de medição + incerteza | NIT-DICLA-030 rev. 15 item 8.2.6 | Validação no cadastro de padrão | **Absoluta em A; configurável em B, C, D** |
| **INV-015** ⭐ | **Tenant não pode emitir certificado de tipo superior ao perfil declarado.** Perfil B/C/D não pode emitir com selo RBC; perfil D não pode emitir declarando "rastreável ao RBC" se não tem padrão RBC. Upgrade de perfil exige prova documental | INMETRO + LGPD + CDC (proteção do cliente final contra fraude) | Validação no momento de gerar PDF do certificado + no upgrade de perfil | **Absoluta (todos perfis)** — esse é o invariante que SEPARA os perfis |
| **INV-016** ⭐ NOVO | **Conformidade WCAG 2.1 AA + PDF/UA em toda interface visível pra usuário.** Portal do cliente (BIG-07), app mobile do técnico (BIG-05), certificado PDF, telas de cadastro. | Lei 13.146/2015 (LBI) art. 63 + e-MAG + WCAG 2.1 AA + Lei 14.133/2021 (licitações) | Audit automatizado de acessibilidade no CI (axe-core ou Lighthouse); PDF/UA conformance no gerador de certificado; revisão manual em cada release | **Absoluta (todos perfis)** — Lei não é opcional |
| **INV-017** ⭐ NOVO (Aud-17 batch 3) | **Assinatura digital ICP-Brasil A3/A1 + carimbo do tempo ITI em toda emissão de certificado de calibração.** Sem assinatura + carimbo válidos, emissão bloqueia. | MP 2.200-2/2001 art. 10 (presunção de autenticidade) + Lei 14.063/2020 (uso de assinaturas eletrônicas no setor público + serviços a terceiros) | Hook bloqueia emissão sem A3 (token físico) em perfil A; bloqueia sem mínimo A1 em perfil B; carimbo do tempo ITI obrigatório em todos os perfis | **A: A3 obrigatório (token físico). B: configurável (mínimo A1). C/D: A1 ou carimbo do tempo isolado. Carimbo ITI absoluto em todos** |
| **INV-018** ⭐ NOVO (Aud-17 batch 3 + R-065) | **Vendor (Aferê) mantém RT técnico publicado no site** (engenheiro CREA com competência metrológica). Substituição em até 60 dias máximo. RT assina dossiê de validação por release (INV-019). | ISO 17025 cl. 7.11 (laboratório que usa software comercial pede documentação do vendor) + boa prática de auditoria | Página pública mostra RT vigente; dashboard interno mostra status RT-vendor + alerta de vacância > 60 dias | **Absoluta (responsabilidade do vendor, não do tenant)** |
| **INV-019** ⭐ NOVO (Aud-17 batch 3) | **Dossiê de validação por release pública.** Toda release pública gera: URS + casos de teste + change log + assinatura digital do RT-vendor + carimbo do tempo ITI. Disponibilizado pra tenant em até 48h da publicação. | ISO/IEC 17025 cl. 7.11.2 + NIT-DICLA-016 item 5.8 | CI bloqueia deploy de release pública sem dossiê assinado anexado; portal do tenant disponibiliza download em até 48h | **Absoluta (responsabilidade do vendor, todos perfis)** |
| **INV-020** ⭐ NOVO (Aud-17 batch 3 + R-058) | **Jornada de motorista UMC conforme Lei 13.103/2015 + CLT 235-C.** 30 min descanso a cada 5h30 de direção; 11h ininterruptas entre jornadas; tempo-espera = sobreaviso 1/3 da hora normal. Sistema bloqueia agendamento de viagem que viola. | Lei 13.103/2015 (Lei do Motorista) + art. 235-C §9 CLT (tempo-espera) | Hook valida agenda da UMC antes de confirmar; bloqueia agendamento que infringe descanso/jornada/sobreaviso | **Aplicável a tenants que operam UMC (Unidade Móvel de Calibração)** — todos perfis quando operam UMC |

**Movido pra ADR (não é invariante):**
- ~~Invariante #7 — NFS-e via BaaS único~~ → **ADR fiscal** (decisão de arquitetura, não regra de conformidade). Risco de amarrar produto a fornecedor sem análise custo/SLA.

### 8.2 Documentos a criar (em conformidade/comum/ e por domínio)

- `conformidade/comum/fiscal-contingencia.md` — playbook SVC-AN/SVC-RS/EPEC/CC-e/cancelamento.
- `conformidade/comum/retencao-matriz.md` — matriz dado × base legal × prazo × destino pós-prazo.
- `conformidade/comum/lgpd-resposta-titular.md` — fluxo de atendimento de direitos LGPD.
- `conformidade/comum/lgpd-incidente-72h.md` (nome a corrigir → **3-dias-uteis**) — runbook de incidente.
- `dominios/metrologia/modulos/calibracao/17025-mapping.md` — cada cláusula da 17025 → feature do produto que a atende.
- `conformidade/comum/nfse-por-municipio.md` — matriz operacional priorizada (atualização trimestral).

### 8.3 Spikes técnicos sugeridos (`docs/discovery/spikes-tecnicos/`)

- Emissão de NF-e de teste no município com **padrão próprio** mais complexo (SP) via BaaS escolhido.
- Validação de cadeia de rastreabilidade num certificado de teste contra NIT-DICLA-030 rev. 15.
- Teste de comunicação de incidente ANPD em ambiente de homologação (formulário CIS).

### 8.4 Itens a confirmar antes de fechar a matriz

- [ ] **Brasília (DF)**: modelo de adesão NFS-e — consultar www.fazenda.df.gov.br.
- [ ] **NIT-DICLA-021**: número da revisão vigente em 05/2026 — baixar do Sidoq.
- [ ] **Enunciado CD/ANPD nº 4** — texto e aplicabilidade a multi-tenant.
- [ ] **Resolução BCB / Instrução Normativa do PIX** — confirmar se a referência "207/2022" do enunciado original existe ou se é número equivocado (norma raiz é Res. BCB 1/2020).
- [ ] **Resolução CMN/BCB Conjunta 1/2020** — confirmar número exato.
- [ ] **VIM 4ª ed.** — confirmar publicação efetiva (JCGM 200).
- [ ] **WELMEC 7.2 / OIML D 31** — confirmar se Roldão quis essas referências quando escreveu "ILAC G8 — validação de software" (provavelmente sim).
- [ ] **MOC CT-e versão vigente** — não confirmada na pesquisa.
- [ ] **Retenção fiscal no RIR/2018** (substituiu Decreto 3000/99) — localizar artigo.
- [ ] **CSRT por UF** — mapear quais UFs já exigem.

---

## Como este documento foi montado

- Pesquisa web pública em 16/05/2026; toda afirmação relevante referencia fonte com link inline.
- Cláusulas da 17025 resumidas a partir de literatura técnica brasileira (Kaye, JusBrasil, CRC, Conformita) — texto da norma é proprietário ABNT/ISO e tem que ser adquirido oficialmente pelo laboratório.
- Marcações `[a confirmar]` indicam onde a fonte primária (portal oficial INMETRO, ANPD, BCB) não foi acessada diretamente nesta sondagem; revalidar antes de transformar em invariante.
- Sem opinião sobre stack: este documento é insumo pra discussão na Família 0 do Discovery.
