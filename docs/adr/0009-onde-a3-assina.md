# ADR-0009 — Onde a assinatura digital A3 (token físico ICP-Brasil) acontece

> **Status:** proposta (17/05/2026 noite final) — aguardando aprovação do Roldão. Bloqueante do Portão 2 da ADR-0001 candidata.
> **Autor:** Claude Code (orquestrador) + Roldão (decisor)
> **Origem:** Parecer 1 da 2ª auditoria de 10 agentes — *"nenhuma stack faz A3 server-side bonito; padrão de mercado em ERP regulado é assinar A3 no cliente"*. ADR-0001 v2 propôs `python-pkcs11` server-side sem confrontar a opção cliente-side.
> **Depende de:** ADR-0001 v2 (stack Django + Flutter), `docs/arquitetura/anti-corrosion-layer.md` (porta `SignatureProvider`)
> **Relacionado:** R-018 score 25 (certificado sem cadeia rejeitado por CGCRE — INV-002 deve estar atendida)

---

## Glossário rápido (pra Roldão)

| Termo técnico | O que é, na prática |
|---|---|
| **ICP-Brasil** | Infraestrutura de Chaves Públicas brasileira — a "carteira de identidade digital" oficial do governo pra pessoas e empresas assinarem documentos com valor legal. |
| **A1 vs A3** | Tipos de certificado ICP-Brasil. **A1** = arquivo no PC (mais cômodo, validade curta 1 ano). **A3** = token físico (pendrive especial com chip — mais seguro, validade 3-5 anos, exigido em alguns processos). |
| **PKCS#11** | Padrão técnico de como software conversa com tokens físicos (drivers nativos do SO). |
| **Token PKCS#11** | "Pendrive especial" — SafeNet, Aladdin, Watchdata são marcas comuns. |
| **CMS / PKCS#7** | Formato do "carimbo digital" que vai dentro do PDF assinado. |
| **PAdES-LTV** | Padrão de assinatura PDF que continua válido por anos (essencial pra ISO 17025). |
| **Web PKI** | Componente do navegador que permite o site invocar o token físico do usuário sem expor a senha ao servidor. |

---

## Contexto

Perfil A (laboratório acreditado RBC) exige certificado digital ICP-Brasil — **A1** (arquivo PKCS#12 protegido por senha) **ou A3** (token físico hardware com chip protegido). INV-017 marca obrigatório.

**Problema A3 server-side:**
- Token físico precisa estar **fisicamente conectado** numa máquina — não dá pra "ter um A3 no servidor" multi-tenant (cada tenant teria que mandar token físico pro nosso datacenter? Inviável).
- Drivers PKCS#11 do token (SafeNet/Aladdin/Watchdata) precisam estar instalados no servidor.
- Cada modelo de token tem driver diferente. Manter compatibilidade com TODOS os tokens dos clientes é impossível.
- Brecha de segurança: token central significa qualquer comprometimento do servidor expõe assinatura de TODOS os tenants.

**Problema A3 cliente-side:**
- Navegador → componente Web PKI (Lacuna/BRy) chama o token local do usuário
- App desktop (Flutter desktop ou .NET) → invoca PKCS#11 nativo do SO
- Servidor só recebe o **hash já assinado** (CMS/PKCS#7) e o anexa ao PDF/XML
- Esse é o padrão de mercado (e-CAC Receita Federal, NF-e webservices, NFS-e via browser, ConectaSUS, etc).

**Padrão de mercado já estabelecido:** todos os softwares regulados BR que exigem A3 (governamentais e privados) implementam **cliente-side**. Tentar server-side seria divergir do padrão sem ganho real.

---

## Decisão

**A3 sempre cliente-side. Servidor nunca toca token físico.**

A1 pode ser server-side ou cliente-side conforme preferência do tenant.

### 1. Fluxo de assinatura A3 cliente-side

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│              │  (1)    │              │  (2)    │              │
│   Servidor   │────────►│   Cliente    │────────►│   Token A3   │
│   (Django)   │ payload │  (browser    │  hash   │   físico     │
│              │ p/ ass  │   ou desk)   │ p/ ass  │  (PKCS#11)   │
└──────────────┘         └──────────────┘         └──────────────┘
       ▲                        │                        │
       │                        │                        │
       │   (4) CMS/PKCS#7       │   (3) assinatura       │
       └────────────────────────┴────────────────────────┘
       │
       │ (5) servidor anexa CMS ao PDF/XML
       ▼
┌──────────────┐
│ PAdES-LTV    │
│ ou XMLDSig   │
│   completo   │
└──────────────┘
```

**Passos:**

1. **Servidor gera "documento a assinar":**
   - Pra PDF: hash SHA-256 do PDF + estrutura PAdES (CMS attribute set, signing time, etc)
   - Pra XML (NFS-e, certificado RBC XML): hash da `<SignedInfo>` + parâmetros XMLDSig

2. **Cliente (browser ou Flutter desktop) recebe o hash + invoca componente Web PKI ou nativo:**
   - Web (Web PKI Lacuna): `webPki.signWithRestPki(hash, certificateThumbprint)` — abre dialog do navegador pedindo senha do token físico
   - Desktop (Flutter FFI PKCS#11): invoca biblioteca nativa do SO (`libpkcs11.so` Linux, `eToken.dll` Windows)

3. **Token físico assina o hash** com chave privada que nunca sai do hardware.

4. **Cliente devolve a assinatura CMS/PKCS#7** pro servidor via HTTPS.

5. **Servidor anexa CMS ao PDF/XML via `pyhanko`** (PAdES) ou `signxml` (XMLDSig) e completa cadeia LTV:
   - Adiciona timestamp ICP-Brasil ITI (carimbo do tempo qualificado)
   - Adiciona cadeia de certificados (DSS dictionary pra PAdES, ds:KeyInfo pra XMLDSig)
   - Adiciona CRLs / OCSP responses pra LTV

### 2. Implementações cliente-side

**Browser (atendente/RT/dono no escritório):**

| Componente | Vendor | Custo | Pros | Cons |
|---|---|---|---|---|
| **Web PKI Lacuna** | Lacuna Software (BR, líder mercado) | ~R$ 30-80/usuário/mês ou pacote volumétrico | Padrão indústria BR, suporta TODOS tokens ICP-Brasil, SDK estável, ~20 anos no mercado | Licença paga por usuário |
| **BRy SignerSuite** | BRy Tecnologia | Similar | Alternativa Lacuna, integração com BRy outros produtos | Menor adoção |
| **Componente próprio WebExtension** | Auto-desenvolvido | Tempo de dev | Sem custo recorrente | Reinventar a roda, manter compatibilidade com tokens em evolução |

**Recomendação:** Web PKI Lacuna como 1ª implementação (`LacunaWebPkiProvider` no anti-corrosion layer). Pacote volumétrico se passar de 20 usuários ativos.

**Flutter desktop (Roldão e signatários técnicos no PC):**

| Componente | Pros | Cons |
|---|---|---|
| **Flutter FFI + libpkcs11 nativo** | Sem custo recorrente, controle total | Trabalho de F-D, binding nativo pra cada SO (Windows/macOS/Linux) |
| **Flutter + WebView com Web PKI Lacuna** | Reaproveita licença Web PKI | Menos integrado, exige rede |

**Recomendação:** começar com Flutter FFI + libpkcs11 pra perfil A interno (Roldão + 1-2 signatários); migrar pra Web PKI se complexidade FFI provar inviável.

### 3. A1 — caminho híbrido

A1 não é token físico — é arquivo `.pfx`/`.p12` protegido por senha. Pode ser:

**Opção 1: Server-side com KMS** (RECOMENDADA pra perfil B/C/D)
- Cliente upload do `.pfx` + senha (criptografada com KMS sa-east-1 antes de salvar)
- Servidor desencripta on-demand pra assinar
- Audit trail registra cada uso
- Vantagem: assinatura "fica fácil" pro cliente, sem precisar de driver/Web PKI

**Opção 2: Cliente-side** (alternativa pra perfil A que prefere)
- Mesmo fluxo do A3 (Web PKI ou Flutter FFI)
- Vantagem: chave nunca toca servidor

### 4. Interface `SignatureProvider` (anti-corrosion layer)

```python
class SignatureProvider(Protocol):
    def prepare_document_to_sign(
        self,
        pdf_or_xml_bytes: bytes,
        format: SignatureFormat,  # PAdES_LTV | XMLDSig
        signer_info: SignerInfo,
    ) -> DocumentHash:
        """Servidor gera hash + estrutura. Retorna pro cliente."""
        ...

    def attach_signature(
        self,
        pdf_or_xml_bytes: bytes,
        cms_signature: bytes,    # vinda do cliente (token) ou KMS (A1 server-side)
        timestamp_token: bytes,  # do ACT ICP-Brasil
        cert_chain: list[bytes], # cadeia de certificados pra LTV
    ) -> SignedDocument:
        """Servidor anexa CMS + completa cadeia LTV."""
        ...

    def verify(self, signed_document: bytes) -> VerificationResult:
        """Verifica assinatura — pyhanko/signxml."""
        ...
```

Implementações:
- `A3ClientSideProvider` — Web PKI (browser) OU Flutter FFI (desktop)
- `A1ServerSideProvider` — A1 com KMS sa-east-1
- `A1ClientSideProvider` — A1 via mesmo fluxo do A3
- `MockSignatureProvider` — testes

### 5. Carimbo do tempo ICP-Brasil ITI (obrigatório pra PAdES-LTV + ISO 17025)

ITI = Instituto Nacional de Tecnologia da Informação. ACTs ICP-Brasil (Autoridade de Carimbo do Tempo) certificadas: **Bry**, **Serasa**, **Valid**, **Soluti**.

Integração via REST (RFC 3161 TSP):
- Servidor envia hash do CMS já assinado
- ACT devolve token de tempo (assinado pela ICP-Brasil)
- Servidor anexa ao DSS dictionary do PAdES

Custo: ~R$ 0,10-0,50 por carimbo (depende do volume). Negociar pacote anual.

---

## Itens a fazer

### Bloqueantes pra F-A começar
- [ ] **`SignatureProvider` Protocol** em `infrastructure/signature/provider.py`
- [ ] **`MockSignatureProvider`** pra testes E2E
- [ ] **Decisão final: Web PKI Lacuna como 1ª impl** ou desenvolvimento Flutter FFI
- [ ] **Cotação Web PKI Lacuna** (pacote inicial 5-20 usuários)
- [ ] **`PyhankoProvider` pra attach_signature** + verify (PAdES-LTV)
- [ ] **`SignxmlProvider` pra XMLDSig** (NFS-e e certificado RBC em XML)

### Pré-MVP-1 (PoC)
- [ ] **PoC Flutter desktop + token físico** (SafeNet 5110 ou equivalente que Roldão tem) — comprovar FFI funciona
- [ ] **PoC Web PKI Lacuna em browser** — assinatura E2E em PDF de teste
- [ ] **Integração ACT ICP-Brasil ITI** (escolher Bry/Serasa/Valid/Soluti) — orçar volume

### Pós-MVP-1
- [ ] **Tutorial em vídeo pro Roldão** explicando: "como cadastrar seu A3 no Aferê e assinar pela primeira vez"
- [ ] **Documentação cliente:** "compatibilidade de tokens ICP-Brasil suportados"

---

## Consequências

### Positivas
- **Token físico nunca sai do cliente** → soberania perfeita, sem ataque centralizado.
- **Custo zero de driver PKCS#11 no servidor** → simplifica deployment.
- **Padrão de mercado** → cliente regulado reconhece o fluxo (mesma UX do e-CAC, NF-e, ConectaSUS).
- **Conformidade ICP-Brasil garantida** → Web PKI Lacuna é homologado pela ITI.
- **Sem responsabilidade vendor sobre token comprometido** → quem perde o A3 é o cliente, não o Aferê.
- **PAdES-LTV via pyhanko** → atende ISO 17025 cláusula 8.4 (retenção legível por anos).

### Negativas
- **Web PKI Lacuna/BRy é pago** → ~R$ 30-80/usuário/mês. Orçar.
- **Flutter desktop com FFI PKCS#11** → trabalho extra de F-D (binding nativo Windows + macOS + Linux).
- **Cliente perde token = não assina** → mas é problema do cliente, não do produto (UX precisa avisar antes do prazo de validade do A3).
- **Curva de aprendizado** → cliente novo precisa entender Web PKI / driver token; tutorial em vídeo obrigatório.

### Trade-offs explícitos

| Trade-off | Escolha | Razão |
|---|---|---|
| A3 server-side vs cliente-side | Cliente-side | Padrão de mercado + soberania + impossibilidade técnica de centralizar tokens físicos |
| Web PKI Lacuna (pago) vs componente próprio | Lacuna 1ª impl | Maturidade + suporte a todos tokens + homologação ITI. Componente próprio em V3+ se volume justificar |
| Flutter FFI vs Flutter + WebView Web PKI | FFI primeiro | Sem dependência de rede no desktop; migrar pra WebView se FFI inviabilizar |
| A1 server-side com KMS vs cliente-side | Server-side default + cliente-side opcional | UX melhor pra perfil B/C/D; perfil A pode escolher |
| Carimbo do tempo ITI via REST vs lib direta | REST | Adapter REST é trivial; lib RFC 3161 em Python é desatualizada |

---

## Critérios de reversão

| Sinal | Resposta |
|---|---|
| Volume de assinaturas justifica componente próprio | Avaliar substituir Lacuna em V3+ |
| Web PKI Lacuna virar incompatível com algum token específico do cliente | Adicionar BRy ou pkcs11 nativo como fallback |
| ICP-Brasil mudar padrão (improvável em 5 anos) | Re-avaliar fluxo inteiro |
| Cliente farma TOP-3 exige assinatura biométrica adicional | Avaliar combinação A3 + biometria móvel |

---

## Aprovação

- [ ] **Roldão (decisor):** aceita A3 cliente-side + Web PKI Lacuna como 1ª impl? — pendente
- [ ] **Auditor 5 (compliance):** confirma conformidade ICP-Brasil + ISO 17025 PAdES-LTV? — pendente
- [ ] **Auditor 6 (segurança):** confirma fluxo sem brecha (token nunca toca servidor)? — pendente
- [ ] **PoC Flutter desktop + token SafeNet do Roldão** verde — pendente
