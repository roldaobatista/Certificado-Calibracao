---
owner: advogado-saas-regulado (subagente)
revisado-em: 2026-05-18
status: stable
escopo: PRD draft equipamentos — review LGPD + contratos
---

# Parecer Jurídico Consultivo — Módulo `equipamentos`

> **Aviso legal obrigatório:** subagente IA, sem OAB ativa, texto consultivo. Antes do go-live público (não dogfooding) envolvendo QR Code aberto, advogado humano licenciado precisa revisar: termo de transferência D2, avisos UX E1/E3/E4, cláusulas DPA D1/D3/D4, política de blur facial em fotos.

## (A) Veredito
**APROVADO COM RESSALVAS BLOQUEANTES (B1–B5).** PRD acerta na arquitetura: INV-025 + versionamento + audit imutável estão corretos. Mas silencia em 5 áreas que clientes Marco 1 já fechou e este não pode regredir.

## (B) BLOQUEADORES

### B1 — `cliente_id_original` imutável colide com LGPD art. 18 VI
Substituir por dois campos:
- `cliente_id_original_hash: bytes(32)` — SHA-256 salgado por tenant (mesmo salt do hash de PII de clientes Marco 1). Sobrevive ao crypto-shredding do Cliente A e mantém rastreabilidade.
- `cliente_id_original: UUID NULL` — referência mutável "viva" enquanto Cliente A existir; vira NULL quando Cliente A for crypto-shredded; FK `ON DELETE SET NULL`.

Certificado emitido referencia `(equipamento_id, versao_n, cliente_id_original_hash)` — não o UUID. Conciliação ISO 17025 cl. 8.4 × LGPD art. 18 VI.

### B2 — Transferência sem aceite formal (`POST /transferir`)
5 elementos jurídicos essenciais faltam:
1. **Aceite duplo:** cedente cede vínculo; cessionário assume responsabilidade.
2. **Forma (Lei 14.063/2020 + MP 2.200-2):** MVP-1 = simples (clique + IP hash + timestamp + texto versionado); configurável A3 em V2.
3. **Trilha auditável:** evento `Equipamento.transferido` carrega (payload sanitizado): `cliente_origem_id_hash`, `cliente_destino_id_hash`, `aceite_origem_em`, `aceite_origem_versao_texto`, `aceite_origem_ip_hash`, `aceite_destino_*`, `motivo_categoria` (enum: `venda`/`comodato`/`doacao`/`correcao_cadastral`/`outro`), `motivo_texto_hash`, `usuario_id_tenant`.
4. **Base legal:** não há compartilhamento de PII entre A e B — Aferê é operador executando instrução do tenant (art. 7º V + VI).
5. **Bloqueio defensivo:** se Cliente A bloqueado ou com fatura aberta referente ao equipamento → bloqueia transferência.

API mínima:
```json
POST /v1/equipamentos/{id}/transferir
{
  "novo_cliente_id": "uuid",
  "motivo_categoria": "venda|comodato|doacao|correcao_cadastral|outro",
  "motivo_detalhe": "string ≤500 chars com regex anti-PII",
  "aceite_origem": { "via": "portal|presencial|email_confirmado", "texto_versao_id": "uuid", "evidencia_id": "uuid" },
  "aceite_destino": { "via": "...", "texto_versao_id": "uuid", "evidencia_id": "uuid" }
}
```

### B3 — Endpoint público `/v1/qr/{hash}` sem allowlist (espelho INV-035)

Catálogo PROIBIDO em scan sem sessão do tenant dono:

| Campo | Anônimo | Outro tenant | Tenant dono |
|---|---|---|---|
| Nome do cliente final | NÃO | NÃO | SIM |
| CPF/CNPJ do cliente | NÃO | NÃO | SIM |
| Endereço/localização física | NÃO | NÃO | SIM |
| Telefone/e-mail do cliente | NÃO | NÃO | SIM |
| TAG do tenant | NÃO | NÃO | SIM |
| Número de série completo | NÃO | NÃO | SIM |
| Fabricante + modelo | OK | OK | SIM |
| Status (vigente/sucateado) | OK | OK | SIM |
| Próxima calibração (data) | NÃO | OK | SIM |
| Foto do equipamento | NÃO | NÃO | SIM |
| Histórico de certificados | NÃO | NÃO | SIM |
| Nome fantasia do tenant dono | NÃO | NÃO | SIM |
| Mensagem genérica "contate operador" | OK | OK | n/a |

Defaults técnicos:
- Token opaco (UUID + HMAC), não slug humano.
- Scan sem sessão → tela genérica "este ativo está cadastrado no Aferê; contate o operador" + logo Aferê. Sem identificação do tenant.
- Rate limit 60 req/min por IP + lockout após 100 4xx em 1h.
- Audit registra todo scan (inclusive anônimo) com IP hash + UA hash + decisão.
- **INV-EQP-QR-001 nova** (= INV-051 do tech-lead).

### B4 — Foto do equipamento sem RAT/aviso/EXIF/retenção

Bloqueios:
1. **RAT-EQP-FOTO** novo em `docs/conformidade/comum/lgpd-rat.md`:
   - Categoria: equipamento físico + potencialmente dado pessoal de terceiros + potencialmente sensível (biometria facial).
   - Base legal: art. 7º V (registro técnico) **com ressalva**: rosto identificável vira art. 11 § 4º (sensível) — exige consentimento OU anonimização (blur).
   - Finalidade: identificação visual + evidência de estado.
   - Retenção: mesma do equipamento + 5 anos pós-sucateamento; ISO 17025 cl. 8.4 quando há cert vinculado.
2. **Aviso UX obrigatório na Tela 5** antes da câmera (E1).
3. **Processamento server-side:**
   - Detecção facial + blur sugerido (V2 se ML não pronto).
   - **Stripping EXIF obrigatório** (GPS, timestamp device, modelo celular).
   - Validação tamanho/formato.
4. **Política de exclusão isolada da foto** (audit do delete preservado).
5. **Direito do funcionário fotografado:** tenant tem 15 dias úteis (canal LGPD do tenant); Aferê fornece ferramenta de exclusão.

### B5 — `localizacao_fisica` como texto livre = PII indireto

Validação backend regex anti-PII (CPF, CNPJ, e-mail, telefone, nomes capitalizados >2 palavras consecutivas) — espelho exato US-CLI-004 R2/US-CLI-005 R2. Limite 200 chars. Mensagem UI clara. Em scan público, localização NÃO aparece independente de conter PII.

**INV-EQP-LOC-001 nova** — localização_fisica validada anti-PII no save + endpoint rejeita 400.

---

## (C) CONCERNS

### C1 — Retenção dual ISO 17025 (~25 anos) × LGPD art. 18 VI quando equipamento é sucateado
Conciliação proposta:
- Equipamento status=sucata → não emite mais cert; vínculo `cliente_atual_id` pode ser anonimizado (NULL) após 5 anos (garantia fiscal default).
- `cliente_id_original_hash` (B1) preserva rastreabilidade ISO.
- `EquipamentoEvento` (audit) preserva 25 anos com payload já sanitizado.

Atualizar `docs/conformidade/comum/retencao-matriz.md` com linhas: `equipamento_ativo`, `equipamento_sucateado`, `equipamento_evento`, `qrcode`, `equipamento_foto`.

### C2 — Re-emissão de QR + revogação não-instantânea
Janela de 2 QRs válidos: novo QR vira ativo + antigo válido por 90 dias + tela informa "este QR foi atualizado" + cron job revoga após 90d. Documentar como **política**, não invariante.

### C3 — Listagem `GET /v1/equipamentos?busca=&cliente_id=` sem autorização por escopo
AuthorizationProvider.can("equipamentos.listar", {cliente_id, tenant_id}):
- `admin_tenant`: lista qualquer cliente.
- `metrologista`: lista qualquer cliente.
- `atendente`: lista apenas clientes com OS aberta ou últimos 90d de atividade (necessidade — art. 6º III).
- `tecnico_campo`: lista apenas equipamentos das OSs atribuídas.

### C4 — Idempotency-Key sem TTL definido
TTL 7 dias default; mutações destrutivas (sucatear, transferir) recusam reuso após 24h com 409.

---

## (D) Cláusulas de contrato a acrescentar

### D1 — DPA tenant↔Aferê — operação de equipamentos
> **Cláusula X.Y — Equipamentos físicos do cliente final.**
> O CONTRATANTE (tenant) é exclusivo responsável pela exatidão dos dados cadastrados, pela legalidade do vínculo equipamento↔cliente final, pela obtenção de aceite documentado em transferências, e pelo cumprimento das normas regulatórias aplicáveis (ISO/IEC 17025, NIT-DICLA, RBC, ANVISA, INMETRO). A CONTRATADA (Aferê) opera como operadora (LGPD art. 5º VII), executando instruções documentadas, **sem juízo de mérito** sobre titularidade, transferência ou descarte. A CONTRATADA fornece audit trail imutável (Lei 13.709/2018 art. 37) em conformidade com ISO/IEC 17025 cl. 8.4 e Marco Civil art. 15.

### D2 — Termo de Transferência de Equipamento
> O CLIENTE CEDENTE, sob CPF/CNPJ {HASH_REFERENCIA}, autoriza a transferência da titularidade operacional do equipamento identificado pela TAG **{TAG}** e número de série **{NS}** ao CLIENTE CESSIONÁRIO, sob CPF/CNPJ {HASH_REFERENCIA_DESTINO}, para fins de **{MOTIVO_CATEGORIA}**.
> O CESSIONÁRIO declara aceitar a titularidade, assumindo as obrigações de guarda, manutenção e calibração futuras, bem como o histórico técnico anterior do equipamento, na forma da NBR ISO/IEC 17025.
> Esta transferência **não transfere** documentos fiscais (NF-e), certificados de calibração anteriores nem responsabilidades trabalhistas/tributárias do CEDENTE.
> Assinatura eletrônica simples (Lei 14.063/2020 art. 4º I) ou avançada/qualificada (art. 4º II/III) conforme contratado em DPA específico.

### D3 — Cláusula de imagem em foto de equipamento (DPA)
> **Cláusula X.Z — Imagens de equipamentos.**
> O CONTRATANTE garante que o registro fotográfico (i) é realizado com finalidade exclusivamente técnica; (ii) não captura intencionalmente imagem de pessoa física identificável; (iii) quando, por acidente operacional, capturar imagem de funcionário, terceiro ou cliente identificável, o CONTRATANTE assume o tratamento como controlador (LGPD art. 11 § 4º), informando o titular (art. 9º) OU removerá a imagem em até 5 dias úteis de notificação. A CONTRATADA disponibilizará ferramenta de exclusão isolada da imagem sem afetar registro do equipamento ou certificados.

### D4 — Cláusula de QR Code público (DPA)
> **Cláusula X.W — QR Code físico em ativos.**
> O QR Code impresso aponta para endereço URL operado pela CONTRATADA. Quando escaneado por usuário **não autenticado** ou autenticado em outro tenant, o sistema **não exibe** informação pessoal identificável do CLIENTE FINAL, do CONTRATANTE, da localização física ou do histórico técnico, conforme política técnica em `docs/conformidade/equipamentos/qr-publico-allowlist.md`. O CONTRATANTE reconhece que o QR, fixado em ativo físico potencialmente visível a terceiros, não constitui canal confidencial.

---

## (E) Textos de aviso UX prontos pra colar

### E1 — Aviso Tela 5 antes da câmera
> **Antes de tirar a foto**
> Fotografe apenas o equipamento e, quando necessário, o ambiente técnico (lacre, dano, plaqueta).
> **Evite capturar:**
> - rosto de pessoas (funcionários, clientes ou terceiros);
> - documentos, telas de computador ou crachás;
> - quadros com informações pessoais ao fundo.
>
> A imagem ficará vinculada ao equipamento e poderá ser visualizada por outros usuários autorizados da sua empresa. Se uma pessoa identificável aparecer por engano, exclua e refaça a foto.
> [ Continuar ] [ Cancelar ]

### E2 — Tela 2 (cadastro) — campo `localizacao_fisica`
> **Local físico do equipamento (até 200 caracteres)**
> Exemplo: *"Almoxarifado A — prateleira 3"*, *"Laboratório de qualidade — bancada 2"*.
> Não inclua **nomes de pessoas** — esses ficam no cadastro do cliente. CPF, e-mail e telefone também não devem aparecer aqui.

Erro de validação:
> *"Identifiquei dados pessoais no texto (CPF, e-mail, telefone ou nome). Reescreva apenas com a localização física do equipamento — os dados do cliente já estão no cadastro dele."*

### E3 — Scan QR sem sessão (anônimo ou outro tenant)
> **Este ativo está cadastrado no Aferê.**
> Para acessar os detalhes técnicos deste equipamento, entre em contato com o laboratório responsável.
> _Aferê é uma plataforma de gestão metrológica. Saiba mais em [https://afere.com.br]._
> *(Sem identificação do tenant, sem TAG, sem foto, sem localização.)*

### E4 — Tela de aceite de transferência (cessionário)
> **Aceite de transferência de equipamento**
> O laboratório **[Razão Social do Tenant]** registrou a transferência do equipamento abaixo do cliente **[CEDENTE — descrição genérica]** para você:
> - TAG: **{TAG}**
> - Número de série: **{NS}**
> - Fabricante / Modelo: **{FABRICANTE} / {MODELO}**
> - Motivo da transferência: **{MOTIVO_CATEGORIA_LEGIVEL}**
>
> Ao aceitar, você assume a titularidade operacional perante o laboratório, incluindo responsabilidade pela calibração e manutenção futuras. **Esta transferência não inclui certificados anteriores nem responsabilidades fiscais ou trabalhistas do cedente.**
> [ Aceitar transferência ] [ Recusar ] [ Falar com o laboratório ]
> *Lei 14.063/2020 — sua aceitação digital é registrada com data, hora e identificador do dispositivo.*

### E5 — Tela 2 em modo edição com cert emitido
> **Atenção:** este equipamento já possui certificado de calibração emitido.
> Alterações em **modelo**, **faixa de medição**, **classe**, **descrição** ou **localização** criarão uma **nova versão** do registro. Os certificados anteriores continuam vinculados à versão original — isso é exigência da norma ISO/IEC 17025 cl. 8.4.
> Campos **TAG**, **número de série** e **fabricante** não podem ser alterados após emissão de certificado.

---

## (F) Bases legais (LGPD art. 7º) por finalidade

| Finalidade | Base legal default | Justificativa |
|---|---|---|
| Cadastrar equipamento (CRUD) | art. 7º V (execução de contrato) | Tenant calibra equipamento por contrato; cadastro é meio operacional |
| Versionar atributo pós-cert (INV-025) | art. 7º II (obrigação regulatória) | ISO 17025 cl. 7.8 + 8.4 exigem rastreabilidade imutável; art. 16 I prevalece sobre direito ao esquecimento |
| Imprimir QR Code físico | art. 7º V | Identificação operacional do ativo |
| Ficha 360° via scan (sessão do tenant dono) | art. 7º V + art. 7º VI | Necessidade operacional + INV-013 (log de visualização) |
| Scan anônimo (público) | art. 7º III (interesse legítimo) | Só mensagem genérica E3 — sem PII |
| Transferir equipamento entre clientes finais | art. 7º V + art. 7º VI | Aferê é operador; aceite documentado é obrigação contratual (CC art. 421/422), não LGPD |
| Sucatear equipamento | art. 7º V | Operacional; histórico preserva sob art. 7º II (ISO 17025) |
| Notificação vencimento calibração | art. 7º V + art. 7º II | Comunicação operacional, não marketing |
| Foto do equipamento (sem rosto) | art. 7º V | Registro técnico. Se capturar rosto → art. 11 § 4º (sensível) com consentimento OU anonimização. Tenant é controlador deste tratamento incidental |
| Audit trail (eventos imutáveis) | art. 7º II + art. 16 I | Imutabilidade exigida normativamente; sanitização (hash) preserva rastreabilidade sem perpetuar PII bruta |
| Histórico com `cliente_id_original_hash` pós-shredding | art. 7º II + art. 16 I | Hash satisfaz ISO 17025 cl. 8.4; não é PII reidentificável (salt por tenant) |

---

## Próximos passos
- Aplicar B1–B5 antes de promover PRD a `stable`.
- Atualizar `lgpd-rat.md` com RAT-EQP-FOTO (B4).
- Atualizar `retencao-matriz.md` com 5 linhas novas (C1).
- Cravar **INV-EQP-QR-001** (B3), **INV-EQP-LOC-001** (B5), **INV-EQP-TRANSF-001** (B2) em `REGRAS-INEGOCIAVEIS.md`.
- Criar `docs/conformidade/equipamentos/qr-publico-allowlist.md` (B3).
- Antes do go-live público: advogado humano OAB ativa revisa termo D2 + UX E1/E3/E4 + DPA D1/D3/D4 + política blur.
