# Discovery — Domínio de negócio

> **Artefato Rodada 0** (agente faz sozinho, Roldão valida). Modelo conceitual de "como uma empresa de assistência técnica + calibração funciona" + glossário operacional do setor. **Base do glossário comum** (Família 2).

---

## Pra preencher quando Rodada 0 iniciar

### Visão geral do setor

[1–2 páginas em PT-BR explicando: o que é assistência técnica, o que é laboratório de calibração, como os dois se cruzam, qual o ecossistema (clientes, fornecedores, reguladores, ferramentas).]

### Atores típicos

| Ator | Quem é | Relação com empresa |
|---|---|---|
| **Cliente PJ** | Empresa que precisa de manutenção ou calibração de instrumento | Origem de receita |
| **Cliente PF** | (raro mas possível — autônomo) | Idem |
| **Fornecedor de peça** | | |
| **Fornecedor de padrão** | Laboratório acreditado RBC que fornece padrão pra a empresa do Roldão | |
| **INMETRO / CGCRE** | Regulador de calibração | Auditoria, acreditação |
| **SEFAZ estadual / municipal** | | |
| **Receita Federal** | | |
| **Bancos** | | |
| **Operadora telecom** | | |
| **Cartórios / juntas comerciais** | | |

### Papéis dentro da empresa típica

| Papel | Responsabilidade | Frequência de uso de software |
|---|---|---|
| **Dono / sócio** | Estratégia, decisão grande | Semanal (relatório) |
| **Gerente operacional** | Triagem de chamado, agenda de técnico | Diário |
| **Atendente / SAC** | Abrir chamado, falar com cliente | Diário (intenso) |
| **Técnico de campo** | Executar OS no local do cliente | Diário (mobile) |
| **Metrologista (signatário)** | Emitir certificado de calibração | Semanal |
| **Financeiro** | Conta a pagar/receber, NF-e, conciliação | Diário |
| **Comercial / vendedor** | Captação, orçamento, fechamento | Diário |

### Processos típicos (fluxo)

#### Processo: Atender chamado e fazer OS
1. Cliente liga / WhatsApp / e-mail → **chamado** aberto
2. Triagem (gerente decide se é manutenção ou calibração)
3. **Orçamento** elaborado e enviado ao cliente
4. Aprovação do cliente
5. **OS** criada e atribuída a técnico
6. Técnico vai ao local OU cliente leva instrumento ao laboratório
7. Execução do serviço (manutenção / calibração)
8. Se calibração: emissão de **certificado** ISO 17025/RBC
9. Faturamento: emissão de **NF-e/NFS-e**
10. Cobrança, recebimento, conciliação bancária
11. Atualização do **CRM** com histórico do cliente

#### Processo: Calibração específica (regulado ISO 17025)
1. Recebimento do instrumento (entrada controlada)
2. Verificação inicial (medições preliminares)
3. Calibração propriamente dita (medição contra padrão rastreado)
4. Cálculo de incerteza
5. Verificação por segundo caminho (garantia de validade — cláusula 7.7)
6. Emissão do certificado (assinatura digital do metrologista)
7. Armazenamento do certificado em WORM (cláusula 8.4)
8. Devolução do instrumento + entrega do certificado ao cliente

### Documentos físicos que o setor maneja

| Documento | Quem emite | Quem recebe | Retenção |
|---|---|---|---|
| Orçamento | Empresa | Cliente | conforme contrato |
| OS | Empresa | Cliente | conforme contrato + 5 anos (fiscal se vinculado a NF-e) |
| Certificado de calibração | Empresa | Cliente | mínimo 5 anos / ciclo de vida do instrumento |
| NF-e / NFS-e | Empresa | Cliente + SEFAZ | 5 anos (Receita) |
| Recibo / boleto | Empresa | Cliente | conforme política |
| Relatório técnico | Empresa | Cliente | conforme contrato |

### Glossário operacional inicial (semente pro glossário comum)

| Termo | Definição (1 linha) | Origem |
|---|---|---|
| **Chamado** | Solicitação inicial de cliente, não necessariamente convertida em OS | Indústria |
| **Triagem** | Decisão sobre quem/quando vai atender o chamado | Indústria |
| **Orçamento** | Proposta comercial pré-aprovação | Indústria |
| **OS (Ordem de Serviço)** | Documento que autoriza execução de um serviço específico | Indústria |
| **Calibração** | Operação que estabelece relação entre valor indicado e valor de referência (VIM) | VIM 4ª ed |
| **Ajuste** | Operação que altera o instrumento pra reduzir erro (DIFERENTE de calibração) | VIM 4ª ed |
| **Verificação** | Comparação contra requisito (DIFERENTE de calibração) | VIM 4ª ed |
| **Padrão** | Realização da definição de uma grandeza (rastreado ao SI) | VIM 4ª ed |
| **Padrão de referência** | Padrão usado pra calibrar outros padrões no mesmo lab | VIM 4ª ed |
| **Padrão de trabalho** | Padrão usado rotineiramente em medições | VIM 4ª ed |
| **Rastreabilidade metrológica** | Cadeia ininterrupta de calibrações até o SI | VIM 4ª ed |
| **Incerteza de medição** | Parâmetro que caracteriza dispersão de valores atribuídos | VIM 4ª ed |
| **Deriva** | Variação contínua da indicação ao longo do tempo | VIM 4ª ed |
| **RBC** | Rede Brasileira de Calibração (acreditação INMETRO/CGCRE) | INMETRO |
| **ISO/IEC 17025** | Norma de requisitos pra laboratórios de ensaio e calibração | ISO |
| **Certificado de calibração** | Documento que apresenta resultado de calibração com incerteza e rastreabilidade | ISO 17025 |
| **Signatário técnico** | Pessoa física responsável legal pelo certificado emitido | RBC NIT-DICLA-021 |
| **Tenant** | Cliente que usa o ERP em modo SaaS (a empresa de assistência) | Engenharia |
| **Cliente** | Empresa/pessoa atendida pela empresa de assistência | Indústria |
| **SLA** | Service Level Agreement — compromisso de tempo de resposta/resolução | Indústria |
| **Funil de vendas** | Estágios sequenciais de qualificação de prospect até cliente | CRM padrão |
| **DRE** | Demonstrativo de Resultado do Exercício | Contábil |
| **NF-e** | Nota Fiscal Eletrônica (produto/mercadoria, estadual) | SEFAZ |
| **NFS-e** | Nota Fiscal de Serviços Eletrônica (municipal) | Município |

### Particularidades brasileiras

- **Imposto sobre serviço (ISS) varia por município** — afeta NFS-e
- **Diferentes regimes tributários** (Simples Nacional, Lucro Presumido, Lucro Real)
- **Pagamento por boleto bancário** ainda dominante em B2B
- **Pix** crescendo rapidamente
- **WhatsApp Business** é canal de atendimento informal mas dominante
- **Receita Federal exige SPED** dependendo do porte

---

## Como preencher

- Agente lê normas + literatura técnica + observa Roldão na empresa dele.
- Roldão valida porque vive o domínio.
- Validar com entrevistas (Onda 1 onda 2) — ajustar a partir do que outros dizem.

## Saída esperada

- Modelo conceitual sólido do setor
- Glossário inicial (vai pra `docs/comum/glossario.md` após filtragem)
- Lista de papéis (vai pra `personas-detalhadas.md`)
- Lista de processos (vai pra `dores-mapeadas.md` quando entrevistas mapearem dor em cada)
