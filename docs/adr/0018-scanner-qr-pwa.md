---
owner: claude-code
revisado-em: 2026-05-18
status: proposta
---

# ADR-0018 — Scanner QR em PWA até Flutter chegar

> **Status:** **proposta** (18/05/2026 — aceitar antes de implementar US-EQP-003).
> **Autor:** Claude Code (orquestrador) + parecer subagente `tech-lead-saas-regulado`
> **Origem:** auditoria PRD `equipamentos` Wave A Marco 2 — Tela 5 (Scanner QR mobile) depende de ADR-0003 (mobile) que ainda é proposta. Wave A não pode bloquear em ADR-0003 nem prometer Flutter pronto.
> **Depende de:** ADR-0001 (stack), ADR-0010 (HTMX + 4 SPAs)
> **Bloqueia:** US-EQP-003 (ficha 360° + scan QR)
> **Relacionado:** ADR-0003 (mobile do técnico de campo — proposta)

---

## Glossário rápido (pra Roldão)

| Termo técnico | O que é, na prática |
|---|---|
| **PWA (Progressive Web App)** | Site que se comporta como app no celular — pode ficar com ícone na tela inicial, abrir tela cheia, usar câmera. Não passa por loja (App Store/Play). |
| **BarcodeDetector API** | "Receita" pronta dentro do Chrome (e Safari iOS 17+) pra ler QR Code pela câmera. Vem de graça — não precisa baixar nada extra. |
| **jsQR** | Biblioteca JavaScript "raspa" que faz o mesmo, pra navegadores que não têm BarcodeDetector. ~45KB. |
| **Fallback** | "Plano B" se o "Plano A" não funcionar. |

---

## Contexto

PRD `equipamentos` Marco 2 inclui **Tela 5 (Scanner QR mobile)** — técnico de campo (P-OP-01) e atendente (P-COM-01) escaneiam QR colado no equipamento pra abrir ficha 360°.

Problema: ADR-0003 (mobile do técnico de campo — Flutter) ainda é **proposta**. Esperar Flutter pronto pra entregar Tela 5 atrasa Wave A em 2-3 meses.

**Alternativas avaliadas:**

1. **Aguardar Flutter (ADR-0003 fechada):** atrasa Wave A; viola memória `feedback_sem_codigo_descartavel` se fizermos "scanner temporário em HTML" pra jogar fora.
2. **Cortar Tela 5 da Wave A:** PRD vira inconsistente; cliente piloto (Balanças Solution) perde funcionalidade central.
3. **PWA + BarcodeDetector + fallback jsQR:** entrega Tela 5 sem bloquear em ADR-0003; PWA continua útil pra clientes finais mesmo após app Flutter (clientes finais não instalam app do tenant).

---

## Decisão

Adotar **PWA com BarcodeDetector API + fallback jsQR** para a Tela 5 (Scanner QR) da Wave A Marco 2.

**Detalhes técnicos:**

- **Stack:** HTML + JS vanilla (sem framework SPA pesada — alinha com ADR-0010); manifest.json + service worker mínimo (cache da página de scanner offline).
- **Câmera:** `navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })` — câmera traseira default.
- **Detecção:**
  - **Plano A** (Chrome Android, Safari iOS 17+, Edge): `window.BarcodeDetector` nativo — performance ~30 fps sem overhead.
  - **Plano B** (Safari iOS ≤16, Firefox sem flag): biblioteca `jsQR` (~45KB gzip) processando frames a 10 fps.
- **Endpoint backend:** **único** — `GET /v1/qr/{hash}` (já especificado em INV-051). O PWA só chama esse endpoint; quando Flutter chegar (Wave B), reusa o mesmo endpoint.
- **UX:**
  - Detecção bem-sucedida → redireciona pra ficha 360° (Modo A se sessão do mesmo tenant; Modo B com payload mínimo caso contrário — ver INV-051).
  - Permissão de câmera negada → fallback pra input file `<input type="file" accept="image/*" capture="environment">` que decodifica imagem estática via jsQR.
- **Distribuição:**
  - URL pública servida por Django (`/equipamentos/scanner`).
  - Tenant pode adicionar ao "Início" do celular via menu do navegador.
  - Não passa por loja — instalação em segundos.

**Não construir descartável (memória `feedback_sem_codigo_descartavel`):** o PWA **permanece em produção** mesmo depois que o app Flutter chegar. Cliente final do tenant não instala app do tenant; PWA é a única forma de o cliente final escanear o QR colado no próprio equipamento dele. Funções complementares:
- App Flutter (Wave B): técnico de campo do tenant — autenticado, com OS, offline-first.
- PWA: clientes finais + atendentes do tenant sem app + visitantes/auditores — leitura rápida sem login.

---

## Trade-offs

- ✅ Não bloqueia Wave A; entrega Tela 5 no Marco 2 do módulo equipamentos.
- ✅ Não joga código fora — PWA continua útil indefinidamente.
- ✅ Sem dependência de loja (App Store/Play) pra clientes finais escanearem.
- ✅ Mesmo endpoint backend `/v1/qr/{hash}` serve PWA hoje e Flutter amanhã.
- ❌ iOS Safari pré-17 sem BarcodeDetector nativo → carrega jsQR (~45KB gzip). Em 2026, base iOS 17+ é majoritária (lançado set/2023).
- ❌ Performance câmera ativa em browser inferior a app nativo — mas Tela 5 é uso esporádico (não streaming), não impacta UX.
- ❌ Cliente final precisa autorizar câmera no navegador — friction de 1 clique extra vs app nativo.

---

## Non-goals

- NÃO substitui o app Flutter do técnico de campo (esse continua na ADR-0003 quando Wave B chegar).
- NÃO entrega funcionalidades offline-first além do scanner em si (sync de OS, formulários offline = ADR-0004 + Wave B).
- NÃO empacota como app Play/App Store — fica como PWA pura instalável via navegador.

---

## Validação / Critérios de aceite

- ✅ Tela 5 funciona em Chrome Android (BarcodeDetector nativo) — teste manual em dispositivo real.
- ✅ Tela 5 funciona em Safari iOS 17+ (BarcodeDetector nativo a partir de iOS 17).
- ✅ Tela 5 funciona em Safari iOS 16 (fallback jsQR).
- ✅ Tela 5 funciona em Firefox Android (fallback jsQR).
- ✅ Endpoint `/v1/qr/{hash}` responde Modo A (autenticado mesmo-tenant) ou Modo B (anônimo/outro-tenant) conforme INV-051.
- ✅ Permissão de câmera negada → fallback pra input file.
- ✅ Página de scanner cacheada via service worker (funciona offline pra abrir; resolução do hash exige rede).
- ✅ Lighthouse PWA score ≥ 90.

---

## Riscos / Mitigações

| Risco | Mitigação |
|---|---|
| BarcodeDetector instável em algum navegador | Fallback automático para jsQR; teste em matriz de browsers reais |
| Cliente final em browser muito antigo (Android 5, iOS 12) | Fallback pra input file + jsQR funciona até IE11 (não suporta WebRTC mas suporta input file) |
| Performance jsQR em CPU fraca | Reduzir frame rate dinamicamente; mostrar "aponte o QR e mantenha estável" se não detectar em 3s |
| Cliente final desconfia de pedir permissão de câmera | Tela explicativa antes do prompt + link "como funciona" |

---

## Como evolui

- Quando ADR-0003 (Flutter) for aceita e app real estiver em produção (Wave B):
  - PWA permanece (clientes finais não migram pra app do tenant).
  - App Flutter ganha scanner nativo (via plugin `mobile_scanner`) reusando o mesmo endpoint `/v1/qr/{hash}`.
  - Apenas técnicos do tenant migram da PWA pro app.
- Caso BarcodeDetector tenha suporte 100% mainstream (improvável até 2028), remover jsQR fallback.
- Métrica observada: % de scans via PWA vs app Flutter (Wave B+).
