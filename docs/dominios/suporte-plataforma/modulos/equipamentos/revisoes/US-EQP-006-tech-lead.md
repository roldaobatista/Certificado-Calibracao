---
owner: tech-lead-saas-regulado
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
us: US-EQP-006
plano_revisado: docs/dominios/suporte-plataforma/modulos/equipamentos/planos/US-EQP-006.md
veredito: APROVADO COM RESSALVAS
---

# Tech Lead Review — Plano US-EQP-006

## Resumo executivo

Plano cobre o essencial (entidade + ≥6 fases + foto perfil A + decisão pós-anomalia + devolução + audit) e mantém coerência com o modelo-de-dominio v2 e com o padrão da OS (`status_os` + trigger PG espelhado). Há, contudo, **6 ressalvas** — três delas bloqueantes para `/implement`. A mais crítica é silenciosa no plano: **`Equipamento` em estado de cadastro provisório ainda não existe** (US-EQP-001 deferiu explicitamente), e US-EQP-006 não pode "esperar pra ver" — ou US-EQP-001 entrega antes, ou US-EQP-006 redefine o pré-requisito.

## Veredito

**APROVADO COM RESSALVAS** (6 ressalvas — 3 bloqueiam `/implement`).

---

## Ressalvas (ordem por gravidade)

### 1. CRÍTICA — Cadastro provisório está deferido em US-EQP-001 e o plano assume que existe

**Problema:** US-EQP-001 §Riscos item 5 diz literalmente "decisão deferida" sobre cadastro provisório (`cliente_id` nullable + flag `cadastro_provisorio=true`). O modelo-de-dominio §`registrar_recebimento` lista pré-condição "equip existe **ou cadastro provisório**". US-EQP-006 lista US-EQP-001 e US-EQP-002 como pré-requisitos — **mas nenhuma das duas entrega cadastro provisório**. O almoxarife do RBC B1/B2 precisa **registrar entrada de equipamento que o cliente trouxe sem cadastro prévio** — sem essa porta, ele inventa workaround (cria Cliente "Não identificado" + Equipamento órfão), o que polui dados.

**Correção exigida (escolher um caminho e cravar no plano antes de `/tasks`):**

- **Caminho A (preferido):** abrir T-EQP-070 dentro de US-EQP-006 que adiciona ao modelo `Equipamento` os campos `cadastro_provisorio: bool = False` + `provisorio_completado_em: timestamp NULL`. O endpoint POST `/v1/equipamentos/` (US-EQP-001) ganha modo `cadastro_provisorio=true` que aceita: só `tag`, `cliente_id` opcional, `descricao` (todos demais campos `null`). Bloquear emissão de certificado enquanto `cadastro_provisorio=True` (invariante nova INV-EQP-PROV-001 + trigger ou check ao gerar certificado em módulo `certificados`). Promoção a definitivo via PATCH normal quando todos os campos obrigatórios chegarem — gera `EquipamentoVersao` com `motivo=promocao_definitivo`.
- **Caminho B:** redefinir US-EQP-006 para exigir cadastro definitivo prévio. Almoxarife que recebe equipamento sem cadastro chama metrologista; metrologista cria cadastro completo via US-EQP-001 antes do recebimento. **Mais simples**, mas contradiz personas.md L52 e contratos/ui.md L137. Só aceitável com OK explícito do RBC.

**Não-aceitável:** deixar como está. "Esperar pra ver no implement" produziu dívida exatamente nesse ponto em US-CLI-003.

### 2. CRÍTICA — `image.copy()` do Pillow NÃO remove EXIF; o plano diz que sim (T-EQP-062 + riscos §1 contradizem entre si)

**Problema:** T-EQP-062 diz "remove EXIF obrigatoriamente (Pillow `image.copy()` sem `_getexif()`)". Isso está **incorreto**. `Image.copy()` preserva o dicionário `info` — incluindo `exif`, `icc_profile`, `xmp` — e quando você chama `image.save(path, "JPEG")` a Pillow re-escreve o EXIF do `info`. A própria seção §Riscos item 1 reconhece isso ("Pillow não remove EXIF in place"), mas a task contradiz. Implementador segue T-EQP-062, teste `test_foto_exif_removido_no_upload` falha, ou pior — passa por acidente (imagem dev sem EXIF) e bug entra em prod.

**Correção exigida — fixar técnica antes do `/implement`:**

```python
# src/infrastructure/equipamentos/foto_upload.py
from io import BytesIO
from PIL import Image

def strip_exif_and_metadata(content: bytes, mime: str) -> tuple[bytes, str]:
    """
    Remove EXIF + ICC + XMP reescrevendo a imagem a partir SOMENTE dos pixels.
    Retorna (bytes_limpos, sha256_hex).
    """
    with Image.open(BytesIO(content)) as img:
        # 1. Aplicar rotação EXIF ANTES de descartar (senão fotos ficam de lado)
        from PIL import ImageOps
        img = ImageOps.exif_transpose(img)
        # 2. Recriar SOMENTE com pixels — descarta info/exif/icc/xmp
        pixels = list(img.getdata())
        clean = Image.new(img.mode, img.size)
        clean.putdata(pixels)
        # 3. Re-encode SEM passar exif=...
        out = BytesIO()
        fmt = "JPEG" if mime == "image/jpeg" else "PNG"
        if fmt == "JPEG":
            clean.save(out, format=fmt, quality=88, optimize=True)
        else:
            clean.save(out, format=fmt, optimize=True)
        clean_bytes = out.getvalue()
    return clean_bytes, hashlib.sha256(clean_bytes).hexdigest()
```

Alternativa mais barata em CPU: `piexif.remove(buf)` para JPEG (não funciona em PNG — PNG usa `tEXt`/`iTXt` chunks; aí precisa do recriar acima). **Recomendo o caminho `Image.new + putdata`** porque é única função que cobre JPEG + PNG + cobre rotação EXIF (sem rotação, foto de iPhone vira de lado no certificado — UX ruim e o RBC vai reclamar).

**Teste a fortalecer** (`test_foto_exif_removido_no_upload`): não basta `assert "exif" not in Image.open(out).info`. Faça **byte-search** explícita: `assert b"Exif\x00\x00" not in clean_bytes and b"GPS" not in clean_bytes`. EXIF tem assinatura de bytes fixa; isso pega regressão direto.

### 3. ALTA — Porta `FotoStorageService`: a interface no plano é genérica demais; cravar contrato agora

**Problema:** T-EQP-063 cria a porta mas não define a interface. Sem isso, `LocalFotoStorageService` (dev) e `B2FotoStorageService` (Wave A+) divergem e a migração quebra. Pontos que precisam estar no plano antes de `/implement`:

```python
# src/domain/suporte_plataforma/equipamentos/ports/foto_storage_service.py
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

@dataclass(frozen=True)
class FotoArmazenada:
    storage_key: str        # ex: "tenant-<uuid>/recebimentos/<rid>/<sha256>.jpg" (NUNCA URL pública)
    sha256: str             # hash do conteúdo limpo pós-EXIF strip
    mime: str               # image/jpeg | image/png
    tamanho_bytes: int
    armazenada_em: datetime

class FotoStorageService(Protocol):
    def armazenar(
        self, tenant_id: UUID, conteudo_limpo: bytes, mime: str, prefixo_logico: str
    ) -> FotoArmazenada: ...

    def url_assinada_leitura(
        self, tenant_id: UUID, storage_key: str, ttl_segundos: int = 300
    ) -> str: ...
        # TTL default 5min; máximo 1h por segurança (logs WORM podem vazar URL)

    def deletar(self, tenant_id: UUID, storage_key: str) -> None: ...
        # Usado em crypto-shredding LGPD (US-CLI futura); NUNCA em fluxo de negócio
```

**Pontos não-óbvios que precisam ficar cravados:**

1. **A coluna `fotos_chegada` no banco guarda `storage_key`, NÃO URL.** URL assinada é construída no boundary (serializer) por demanda. Senão Wave A+ migra B2 e tem que reescrever todas as linhas. O modelo-de-dominio L91 diz `array<URL>` — **corrigir pra `array<storage_key>` em texto explicativo + manter o tipo como `array<text>`**. Esta é uma correção que vale subir pro modelo-de-dominio também.
2. **`tenant_id` é parâmetro explícito da porta**, não derivado do contexto (memória de hook `tenant-id-validator` cobra). Adapter B2 monta path `tenant-<id>/...` com KMS por tenant (já está no plano).
3. **Hash retornado pela porta = mesmo hash usado em `auditoria.payload_jsonb`** — único ponto de verdade. Não computar duas vezes.
4. **TTL da signed URL** precisa ser parâmetro da porta (não constante) — exports de certificado podem precisar TTL maior (até 1h); fluxo UI normal usa 5min.

### 4. ALTA — Trigger PG `validar_transicao_status_fluxo_lab`: cravar o SQL exato; tabela seed; espelhar padrão OS

**Problema:** T-EQP-061 menciona "rejeita UPDATE com transição inválida" mas não mostra: (a) onde fica a tabela de transições, (b) como o trigger consulta, (c) se a função `transicao_permitida(de, para)` em Python espelha a tabela PG (dois pontos de verdade = bug garantido em 6 meses).

**Cravar no plano (T-EQP-060/061 reescritas):**

**Lado Python (T-EQP-060):**

```python
# src/domain/suporte_plataforma/equipamentos/status_fluxo_lab.py
from enum import StrEnum

class StatusFluxoLab(StrEnum):
    AGUARDANDO_RECEBIMENTO = "aguardando_recebimento"
    RECEBIDO_PENDENTE_INSPECAO = "recebido_pendente_inspecao"
    EM_INSPECAO_VISUAL = "em_inspecao_visual"
    AGUARDANDO_CALIBRACAO = "aguardando_calibracao"
    EM_CALIBRACAO = "em_calibracao"
    AGUARDANDO_APROVACAO_TECNICA = "aguardando_aprovacao_tecnica"
    AGUARDANDO_DEVOLUCAO = "aguardando_devolucao"
    DEVOLVIDO = "devolvido"
    NAO_CONFORMIDADE_RECEBIMENTO = "nao_conformidade_recebimento"  # terminal
    NAO_CONFORMIDADE_CALIBRACAO = "nao_conformidade_calibracao"    # terminal

# Tabela explícita — NÃO derivar por índice
_TRANSICOES_PERMITIDAS: frozenset[tuple[StatusFluxoLab, StatusFluxoLab]] = frozenset({
    (StatusFluxoLab.AGUARDANDO_RECEBIMENTO,        StatusFluxoLab.RECEBIDO_PENDENTE_INSPECAO),
    (StatusFluxoLab.AGUARDANDO_RECEBIMENTO,        StatusFluxoLab.NAO_CONFORMIDADE_RECEBIMENTO),
    (StatusFluxoLab.RECEBIDO_PENDENTE_INSPECAO,    StatusFluxoLab.EM_INSPECAO_VISUAL),
    (StatusFluxoLab.RECEBIDO_PENDENTE_INSPECAO,    StatusFluxoLab.NAO_CONFORMIDADE_RECEBIMENTO),
    (StatusFluxoLab.EM_INSPECAO_VISUAL,            StatusFluxoLab.AGUARDANDO_CALIBRACAO),
    (StatusFluxoLab.EM_INSPECAO_VISUAL,            StatusFluxoLab.NAO_CONFORMIDADE_RECEBIMENTO),
    (StatusFluxoLab.AGUARDANDO_CALIBRACAO,         StatusFluxoLab.EM_CALIBRACAO),
    (StatusFluxoLab.EM_CALIBRACAO,                 StatusFluxoLab.AGUARDANDO_APROVACAO_TECNICA),
    (StatusFluxoLab.EM_CALIBRACAO,                 StatusFluxoLab.NAO_CONFORMIDADE_CALIBRACAO),
    (StatusFluxoLab.AGUARDANDO_APROVACAO_TECNICA,  StatusFluxoLab.AGUARDANDO_DEVOLUCAO),
    (StatusFluxoLab.AGUARDANDO_APROVACAO_TECNICA,  StatusFluxoLab.NAO_CONFORMIDADE_CALIBRACAO),
    (StatusFluxoLab.AGUARDANDO_DEVOLUCAO,          StatusFluxoLab.DEVOLVIDO),
})

def transicao_permitida(de: StatusFluxoLab, para: StatusFluxoLab) -> bool:
    if de == para:
        return True  # idempotência — UPDATE pra mesmo status não dispara
    return (de, para) in _TRANSICOES_PERMITIDAS
```

**Lado PG (T-EQP-061 — migration 0019):**

```sql
-- 1. Tabela seed (single source of truth no banco)
CREATE TABLE equipamentos_status_fluxo_lab_transicao (
    de   text NOT NULL,
    para text NOT NULL,
    PRIMARY KEY (de, para)
);

INSERT INTO equipamentos_status_fluxo_lab_transicao (de, para) VALUES
    ('aguardando_recebimento',        'recebido_pendente_inspecao'),
    ('aguardando_recebimento',        'nao_conformidade_recebimento'),
    ('recebido_pendente_inspecao',    'em_inspecao_visual'),
    -- ... (espelhar exatamente a tabela Python)
    ('aguardando_devolucao',          'devolvido');

-- 2. Função trigger
CREATE OR REPLACE FUNCTION equipamentos_validar_transicao_status_fluxo_lab()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status_fluxo_lab = NEW.status_fluxo_lab THEN
        RETURN NEW;  -- idempotência
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM equipamentos_status_fluxo_lab_transicao
        WHERE de = OLD.status_fluxo_lab AND para = NEW.status_fluxo_lab
    ) THEN
        RAISE EXCEPTION 'Transicao invalida: % -> %', OLD.status_fluxo_lab, NEW.status_fluxo_lab
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NEW;
END $$;

CREATE TRIGGER trg_equipamento_recebimento_transicao
BEFORE UPDATE OF status_fluxo_lab ON equipamento_recebimento
FOR EACH ROW EXECUTE FUNCTION equipamentos_validar_transicao_status_fluxo_lab();
```

**Garantir paridade:** adicionar **teste de paridade** (`test_paridade_tabela_python_e_pg_transicoes`) que carrega o frozenset Python + faz `SELECT (de, para) FROM equipamentos_status_fluxo_lab_transicao` e compara conjuntos. Se alguém mexer num lado e esquecer do outro, teste falha. Vale espelhar isso também em `status_os` (memória pendente — não obrigação deste plano, mas anotar).

**`# tests-coverage:` da migration 0019:** apontar happy (`test_transicao_recebido_para_em_inspecao_visual_ok`) + unhappy (`test_transicao_aguardando_recebimento_direto_para_devolvido_retorna_422`) + paridade (`test_paridade_tabela_python_e_pg_transicoes`). Hook `policy-test-coverage` vai cobrar.

### 5. MÉDIA — Audit `equipamento.recebido_no_lab` precisa de payload mínimo definido + sem PII

**Problema:** T-EQP-064 grava audit mas plano não cita schema do `payload_jsonb`. Espelhar padrão de US-CLI-001 (ressalva 3 da revisão clientes):

```json
{
  "recebimento_id": "<uuid>",
  "equipamento_id": "<uuid>",
  "condicao_visual_chegada": "<enum>",
  "fotos_count": 2,
  "fotos_sha256": ["<hex>", "<hex>"],
  "decisao_apos_anomalia": "<enum>|null"
}
```

**Proibido:** logar `numero_serie`, `tag`, `recebido_por_nome`, `cliente_id` em claro. Esses dados resolvem-se via JOIN quando consultar. Auditoria é WORM — vira depósito permanente de PII se descuidar. Para o `recebido_por` (usuario_id), referenciar pelo UUID; isso já é o padrão.

### 6. MÉDIA — `Equipamento.status = em_calibracao_lab` enquanto recebimento aberto: definir enum + reversão

**Problema:** T-EQP-064 atualiza `Equipamento.status = em_calibracao_lab`. Isso assume que o enum `Equipamento.status` tem esse valor — não vi no modelo-de-dominio §Equipamento. Se for novo, é AlterField com migration. Adicional: o que acontece se múltiplos recebimentos abertos co-existirem (cenário "cliente mandou 3 instrumentos no mesmo dia, 1 vira NC, 2 seguem")? `Equipamento.status` é por **equipamento** (1:1 com `Equipamento`), não por recebimento — então estado correto é "tem ≥1 recebimento aberto". Recomendo:

- **Não** introduzir `em_calibracao_lab` como status do `Equipamento`. Calcular **derivado** via `Equipamento.tem_recebimento_aberto: bool` (property que consulta `EquipamentoRecebimento` onde `status_fluxo_lab NOT IN (devolvido, nao_conformidade_*)`). UI mostra o status derivado.
- Se Roldão insistir em coluna materializada (perf — query em ficha 360°), criar campo `Equipamento.recebimento_aberto_id: UUID NULL` mantido por trigger ou signal. Não usar enum `status` pra isso — mistura conceitos.

**Cravar no plano qual caminho** antes de `/tasks`.

---

## Pontos fortes do plano

- Reaproveita 100% do padrão de status + trigger PG do módulo `os` (memória institucional preservada).
- Reconhece honestamente a dívida do EXIF strip em §Riscos §1 (mesmo que T-EQP-062 contradiga — ver ressalva 2).
- Non-goals corretos (blur facial V2, portal-cliente Wave B+, AWS B2 stub em Wave A).
- 17 testes cobrindo happy/unhappy em authz, perfil A vs B, transição, devolução, evento — bom recorte.
- Decisão de `EmptyNotificacaoClienteService` + audit-as-relay segue o padrão Marco 1 de clientes — correto.

---

## Sugestão de teste adicional

- `test_paridade_tabela_python_e_pg_transicoes` (ressalva 4) — bloqueia drift entre `_TRANSICOES_PERMITIDAS` e `equipamentos_status_fluxo_lab_transicao`.
- `test_foto_exif_byte_search_clean` (ressalva 2) — busca `b"Exif\x00\x00"` e `b"GPS"` nos bytes salvos.
- `test_foto_storage_armazena_storage_key_nao_url` (ressalva 3) — confere que coluna `fotos_chegada` no banco tem `tenant-<uuid>/...`, não `https://...`.
- `test_audit_payload_nao_contem_pii` (ressalva 5) — confere que nenhuma chave do `payload_jsonb` é `tag`, `numero_serie`, `cliente_nome`, `recebido_por_nome`.
- `test_dois_recebimentos_simultaneos_no_mesmo_equipamento` (ressalva 6) — define comportamento esperado: bloqueia (412) ou permite (cenário lab grande). Roldão decide.

---

## Limites de honestidade

- **Confiante:** ressalvas 1, 2, 4, 5 (li o modelo-de-dominio + US-EQP-001 + padrão de auditoria já implementado em clientes; checei comportamento da Pillow contra documentação oficial).
- **Suspeita não-provada:** ressalva 6 — pode existir convenção em outro módulo que eu não vi; se metrologista do RBC disser "1 equipamento = 1 recebimento aberto por vez é regra de chão de lab", coluna materializada faz sentido. Confirmar com `consultor-rbc-iso17025`.
- **Fora do meu alcance:** validação se "registrar `Equipamento.fluxo_lab_avancado` como audit avulso" é suficiente pra auditor CGCRE rastrear NC. RBC dá a palavra final no formato do trilho.
- **Não verifiquei runtime real** — todas as ressalvas vêm de leitura do plano + modelo + código existente (clientes/os). Suite final só fala depois do `/implement`.

---

## Recomendação operacional

1. Aplicar ressalvas 1, 2 e 4 no plano antes de abrir `/tasks` — bloqueantes.
2. Aplicar ressalvas 3, 5, 6 antes de `/implement` — não bloqueiam `/tasks`, mas geram retrabalho garantido se ficarem pra depois.
3. Subir a correção do "fotos_chegada guarda storage_key, não URL" pro `modelo-de-dominio.md` §EquipamentoRecebimento — é correção de doc canônica, não só do plano.
4. Re-invocar este parecer **não é necessário** se as 6 ressalvas forem aplicadas literalmente. Se houver divergência (especialmente na ressalva 1 — escolha A vs B), re-invocar.
5. Após `/implement`: auditor Segurança (foco em EXIF byte-search + signed URL TTL + audit sem PII) + auditor Qualidade (cobertura + paridade Py↔PG) + RBC (transições completas vs cl. 7.4.4/7.4.5/7.10).
