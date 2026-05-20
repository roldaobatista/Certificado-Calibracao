"""Use case: importar clientes em lote a partir de CSV (US-CLI-003).

Camada APPLICATION. Recebe Repository (Protocol do domain) via DI. NUNCA
importa Django nem PG. Adapter concreto em
`src/infrastructure/clientes/repositories.py:DjangoClienteRepository.bulk_upsert`.

Fluxo:
1. Pre-processamento (em memoria) — separa validas/invalidas:
   - Resolve mapeamento `header_arquivo -> campo_destino`.
   - Para cada linha:
     a. Sanitiza celulas contra CSV/formula injection.
     b. Valida documento (CPF/CNPJ via VOs).
     c. Detecta dados sensiveis (descarta colunas marcadas).
     d. Classifica PF/PJ:
        - PJ sem PF associada: dispensa `pj_sem_pf_associada`.
        - PJ com PF e tenant declarou aceite: dispensa `pj_com_pf_aceite_declarado_pelo_tenant`.
        - PJ com PF sem declaracao: `pj_com_pf_pendente_aceite` + flag.
        - PF sem `pf_aceite_origem`: rejeita (motivo `pf_sem_aceite`).
        - PF com `pf_aceite_origem`: cria com base legal explicita + evidencia.
   - Calcula hash da linha (HMAC com chave de servidor) pra referencia sem PII.
   - Dedup intra-arquivo: ultima linha vence; reporta `linhas_colapsadas`.
2. skip_invalid=False + qualquer invalida -> levanta ErroImportacao(400).
   skip_invalid=True -> validas seguem; invalidas viram rejeitados[].
3. Repository.bulk_upsert (SERIALIZABLE + advisory lock por tenant).
4. Empacota resultado pra view publicar audit + responder relatorio.

Sem efeito colateral fora do Repository. View envolve em try/finally pra
garantir delete do tempfile (R3 advogado).
"""

from __future__ import annotations

import hashlib
import hmac
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from src.domain.comercial.clientes.repository import (
    ClienteImportacaoInput,
    ClienteRepository,
    LinhaRejeitada,
)

# Heuristica em runtime; reproduz csv_io mas evita import cruzado app->infra.
_REGEX_EMAIL_CORPORATIVO = re.compile(
    r"^(contato|comercial|vendas|suporte|atendimento|sac|financeiro|fiscal|adm|admin|"
    r"diretoria|presidencia|rh|operacoes|info|noreply|no-reply|loja|"
    r"compras|cobranca|cobranças)@",
    re.IGNORECASE,
)


class ErroImportacao(Exception):
    """Erro de regra de negocio na importacao."""

    def __init__(self, code: str, message: str, detalhes: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.detalhes = detalhes or {}


@dataclass(frozen=True)
class ContextoImportacao:
    """Tudo que o use case precisa pra processar a importacao.

    `arquivo_bytes` so vem aqui pra calcular hash; conteudo ja foi
    parseado pela view via `csv_io.ler_csv_normalizado` + entregue em
    `linhas`. O use case nao toca disco.
    """

    tenant_id: UUID
    usuario_id: UUID | None
    headers: tuple[str, ...]
    linhas: tuple[tuple[str, ...], ...]
    mapeamento: dict[str, str]  # campo_destino -> header_arquivo
    declaracao_tem_base_legal: bool
    declaracao_compromisso_comunicar: bool
    declaracao_sem_sensiveis: bool
    procedencia_declarada: str
    pf_aceite_origem: str  # vazio = rejeita PF
    cpf_responsavel_destino: str  # `atributo_pj` | `contato_pf_separado` | `descartar`
    colunas_sensiveis: tuple[str, ...]
    colunas_cpf_responsavel: tuple[str, ...]
    skip_invalid: bool
    update_existing: bool
    arquivo_hash: str
    arquivo_tamanho_bytes: int
    arquivo_nome_hash: str
    delimitador: str
    encoding: str
    linha_hash_key: str
    aceite_lgpd_versao: str
    aceite_lgpd_ip_hash: str
    agora: datetime


@dataclass(frozen=True)
class ResultadoExecucao:
    """Empacota relatorio + dados pro audit."""

    importacao_id: UUID
    totais: dict[str, int]
    rejeitados_motivos_agregados: dict[str, int]
    rejeitados: tuple[LinhaRejeitada, ...]
    declaracao_hash: str
    linhas_colapsadas_intra_arquivo: int
    dados_sensiveis_filtrados: int
    pj_dispensa_aceite: int
    pj_com_pf_pendente_aceite: int
    pf_rejeitadas_por_falta_aceite: int


def _hash_linha(linha: tuple[str, ...], hash_key: str) -> str:
    # SANEA-02: HMAC com chave de servidor (derivada de PII_HASH_KEY na
    # camada infra e injetada aqui). Antes era sha256(payload + salt) com
    # salt = sha256("afere-salt:{tenant_id}") — reconstruivel por quem
    # soubesse o tenant_id (publico), entao a linha com CPF era atacavel.
    payload = ("|".join(linha)).encode("utf-8")
    return hmac.new(hash_key.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def _normalizar_documento(doc_bruto: str) -> str:
    """Remove tudo que nao for [A-Za-z0-9]; UPPER pra CNPJ alfanumerico."""
    limpo = re.sub(r"[^A-Za-z0-9]", "", doc_bruto)
    return limpo.upper()


def _inferir_tipo_pessoa(documento_normalizado: str) -> str:
    """11 chars = PF, 14 chars = PJ; outro = invalido."""
    if len(documento_normalizado) == 11 and documento_normalizado.isdigit():
        return "PF"
    if len(documento_normalizado) == 14:
        return "PJ"
    return ""


def _email_e_pessoal(email: str, nome: str) -> bool:
    """Heuristica R1 advogado: email corporativo generico vs pessoal.

    `contato@empresa.com.br` = corporativo (PJ pode dispensar).
    `joao.silva@empresa.com.br` = pessoal (PF associada).
    """
    if not email:
        return False
    if _REGEX_EMAIL_CORPORATIVO.match(email):
        return False
    return True


def importar_clientes(
    *,
    repository: ClienteRepository,
    contexto: ContextoImportacao,
) -> ResultadoExecucao:
    """Executa o pre-processamento + bulk_upsert + empacota relatorio.

    Levanta ErroImportacao em:
    - `declaracao_incompleta` (3 checkboxes obrigatorios) — corresponde a 400.
    - `skip_invalid_false_com_linhas_invalidas` — 400 com lista.
    """
    from src.domain.shared.value_objects import CNPJ, CPF

    # --- Validacao da declaracao (R6 advogado) ---
    if not (
        contexto.declaracao_tem_base_legal
        and contexto.declaracao_compromisso_comunicar
        and contexto.declaracao_sem_sensiveis
    ):
        raise ErroImportacao(
            "declaracao_incompleta",
            "As 3 declaracoes de procedencia sao obrigatorias.",
            {
                "tem_base_legal": contexto.declaracao_tem_base_legal,
                "compromisso_comunicar_titulares": contexto.declaracao_compromisso_comunicar,
                "declara_sem_dados_sensiveis": contexto.declaracao_sem_sensiveis,
            },
        )
    if not contexto.procedencia_declarada.strip():
        raise ErroImportacao(
            "procedencia_declarada_obrigatoria",
            "Informe a origem do dado (ex: 'Bling v3 export').",
        )

    # --- Resolve mapeamento header_arquivo -> indice da coluna ---
    headers_lower = [h.lower().strip() for h in contexto.headers]
    indices: dict[str, int | None] = {}
    for campo, header_alvo in contexto.mapeamento.items():
        if not header_alvo:
            indices[campo] = None
            continue
        try:
            indices[campo] = headers_lower.index(header_alvo.lower().strip())
        except ValueError:
            indices[campo] = None

    # Indices das colunas CPF-responsavel (R8 advogado).
    indices_cpf_resp = [
        headers_lower.index(h.lower().strip())
        for h in contexto.colunas_cpf_responsavel
        if h.lower().strip() in headers_lower
    ]
    # Set de indices sensiveis (sao descartados — R9 advogado).
    indices_sensiveis = {
        headers_lower.index(h.lower().strip())
        for h in contexto.colunas_sensiveis
        if h.lower().strip() in headers_lower
    }

    # --- Pre-processamento linha a linha ---
    validas: list[ClienteImportacaoInput] = []
    invalidas: list[LinhaRejeitada] = []
    contadores = {
        "pj_dispensa_aceite": 0,
        "pj_com_pf_pendente_aceite": 0,
        "pf_rejeitadas_por_falta_aceite": 0,
        "pj_com_pf_aceite_declarado": 0,
        "pf_aceite_externo": 0,
    }
    dados_sensiveis_filtrados = 0
    motivos_agregados: dict[str, int] = {}

    # Dedup intra-arquivo: (tipo, documento) -> ultima ClienteImportacaoInput
    dedup_intra: dict[tuple[str, str], ClienteImportacaoInput] = {}
    linhas_colapsadas = 0

    def _coluna(linha: tuple[str, ...], campo: str) -> str:
        idx = indices.get(campo)
        if idx is None or idx >= len(linha):
            return ""
        # Descarte de colunas sensiveis (R9 advogado).
        if idx in indices_sensiveis:
            return ""
        return linha[idx].strip()

    for numero, linha in enumerate(contexto.linhas, start=2):  # linha 1 = header
        linha_hash = _hash_linha(linha, contexto.linha_hash_key)

        # Conta dados sensiveis descartados.
        for idx in indices_sensiveis:
            if idx < len(linha) and linha[idx].strip():
                dados_sensiveis_filtrados += 1

        doc_bruto = _coluna(linha, "documento")
        if not doc_bruto:
            invalidas.append(
                LinhaRejeitada(
                    linha_numero=numero,
                    linha_hash=linha_hash,
                    motivo="documento_ausente",
                    motivo_descricao_curta="Coluna de documento vazia.",
                )
            )
            motivos_agregados["documento_ausente"] = (
                motivos_agregados.get("documento_ausente", 0) + 1
            )
            continue

        doc_normalizado = _normalizar_documento(doc_bruto)
        tipo = _inferir_tipo_pessoa(doc_normalizado)
        if not tipo:
            invalidas.append(
                LinhaRejeitada(
                    linha_numero=numero,
                    linha_hash=linha_hash,
                    motivo="documento_tamanho_invalido",
                    motivo_descricao_curta=("Documento nao tem 11 (CPF) nem 14 (CNPJ) caracteres."),
                )
            )
            motivos_agregados["documento_tamanho_invalido"] = (
                motivos_agregados.get("documento_tamanho_invalido", 0) + 1
            )
            continue

        # Valida com VOs do domain.
        try:
            if tipo == "PF":
                doc_validado = CPF(doc_normalizado).value
            else:
                doc_validado = CNPJ(doc_normalizado).value
        except ValueError:
            motivo = "cpf_invalido" if tipo == "PF" else "cnpj_invalido"
            invalidas.append(
                LinhaRejeitada(
                    linha_numero=numero,
                    linha_hash=linha_hash,
                    motivo=motivo,
                    motivo_descricao_curta="Documento nao bate com DV/formato.",
                )
            )
            motivos_agregados[motivo] = motivos_agregados.get(motivo, 0) + 1
            continue

        nome = _coluna(linha, "nome")
        if not nome:
            invalidas.append(
                LinhaRejeitada(
                    linha_numero=numero,
                    linha_hash=linha_hash,
                    motivo="nome_ausente",
                    motivo_descricao_curta="Coluna de nome vazia.",
                )
            )
            motivos_agregados["nome_ausente"] = motivos_agregados.get("nome_ausente", 0) + 1
            continue

        nome_fantasia = _coluna(linha, "nome_fantasia")
        email = _coluna(linha, "email")
        telefone = _coluna(linha, "telefone")

        # CPF de responsavel/socio (R8 advogado) — destinos possiveis.
        cpf_responsavel_legal = ""
        contato_pf_associado_via_cpf_resp = False
        if tipo == "PJ" and indices_cpf_resp:
            for idx in indices_cpf_resp:
                if idx < len(linha) and linha[idx].strip():
                    if contexto.cpf_responsavel_destino == "atributo_pj":
                        cpf_norm = _normalizar_documento(linha[idx])
                        if len(cpf_norm) == 11 and cpf_norm.isdigit():
                            cpf_responsavel_legal = cpf_norm
                    elif contexto.cpf_responsavel_destino == "contato_pf_separado":
                        contato_pf_associado_via_cpf_resp = True
                    # 'descartar' -> nao guarda
                    break

        # Classificacao LGPD (R1, R2, R8 advogado)
        aceite_lgpd_em: datetime | None = None
        aceite_lgpd_origem = ""
        aceite_lgpd_dispensa_motivo = ""
        aceite_lgpd_base_legal = ""
        aceite_lgpd_evidencia_externa = ""
        aceite_lgpd_pendente = False

        if tipo == "PJ":
            tem_pf_associada = _email_e_pessoal(email, nome) or bool(
                contato_pf_associado_via_cpf_resp
            )
            if not tem_pf_associada:
                aceite_lgpd_dispensa_motivo = "pj_sem_pf_associada"
                contadores["pj_dispensa_aceite"] += 1
            elif contexto.pf_aceite_origem:
                # tenant declarou aceite externo (R6 + R1 advogado caminho 2)
                aceite_lgpd_dispensa_motivo = "pj_com_pf_aceite_declarado_pelo_tenant"
                aceite_lgpd_base_legal = _base_legal_do_origem(contexto.pf_aceite_origem)
                aceite_lgpd_evidencia_externa = hashlib.sha256(
                    contexto.procedencia_declarada.encode("utf-8")
                ).hexdigest()
                contadores["pj_com_pf_aceite_declarado"] += 1
            else:
                # PJ com PF e sem declaracao -> pendente (R1 advogado caminho 3)
                aceite_lgpd_dispensa_motivo = "pj_com_pf_pendente_aceite"
                aceite_lgpd_pendente = True
                contadores["pj_com_pf_pendente_aceite"] += 1
        else:  # PF
            if not contexto.pf_aceite_origem:
                # Default seguro (R2 advogado): rejeita.
                invalidas.append(
                    LinhaRejeitada(
                        linha_numero=numero,
                        linha_hash=linha_hash,
                        motivo="pf_sem_aceite",
                        motivo_descricao_curta=(
                            "PF nao pode ser importada sem declarar pf_aceite_origem "
                            "(LGPD art. 7 I/V)."
                        ),
                    )
                )
                motivos_agregados["pf_sem_aceite"] = motivos_agregados.get("pf_sem_aceite", 0) + 1
                contadores["pf_rejeitadas_por_falta_aceite"] += 1
                continue
            aceite_lgpd_em = contexto.agora
            aceite_lgpd_origem = "IMPORTACAO_LEGADA"
            aceite_lgpd_base_legal = _base_legal_do_origem(contexto.pf_aceite_origem)
            aceite_lgpd_evidencia_externa = hashlib.sha256(
                contexto.procedencia_declarada.encode("utf-8")
            ).hexdigest()
            contadores["pf_aceite_externo"] += 1

        entrada = ClienteImportacaoInput(
            linha_numero=numero,
            linha_hash=linha_hash,
            tipo_pessoa=tipo,
            documento=doc_validado,
            nome=nome,
            nome_fantasia=nome_fantasia,
            email=email,
            telefone=telefone,
            aceite_lgpd_em=aceite_lgpd_em,
            aceite_lgpd_versao=contexto.aceite_lgpd_versao if aceite_lgpd_em else "",
            aceite_lgpd_origem=aceite_lgpd_origem,
            aceite_lgpd_dispensa_motivo=aceite_lgpd_dispensa_motivo,
            aceite_lgpd_base_legal=aceite_lgpd_base_legal,
            aceite_lgpd_evidencia_externa=aceite_lgpd_evidencia_externa,
            aceite_lgpd_pendente=aceite_lgpd_pendente,
            cpf_responsavel_legal=cpf_responsavel_legal,
            aceite_lgpd_ip_hash=contexto.aceite_lgpd_ip_hash if aceite_lgpd_em else "",
        )

        chave = (tipo, doc_validado)
        if chave in dedup_intra:
            linhas_colapsadas += 1
        dedup_intra[chave] = entrada

    validas = list(dedup_intra.values())

    # --- skip_invalid=False bloqueia o lote inteiro (R9 tech-lead) ---
    if not contexto.skip_invalid and invalidas:
        raise ErroImportacao(
            "linhas_invalidas_e_skip_invalid_false",
            (
                f"{len(invalidas)} linha(s) invalida(s). Defina skip_invalid=true "
                f"pra importar apenas as validas."
            ),
            {
                "invalidas": [
                    {
                        "linha_numero": r.linha_numero,
                        "motivo": r.motivo,
                        "motivo_descricao_curta": r.motivo_descricao_curta,
                    }
                    for r in invalidas[:50]
                ]
            },
        )

    # --- Bulk upsert ---
    resultado_bulk = repository.bulk_upsert(
        tenant_id=contexto.tenant_id,
        linhas=validas,
        update_existing=contexto.update_existing,
        agora=contexto.agora,
    )

    # Junta rejeitados do pre-processamento + integridade.
    todos_rejeitados = tuple(invalidas) + resultado_bulk.rejeitados
    for r in resultado_bulk.rejeitados:
        motivos_agregados[r.motivo] = motivos_agregados.get(r.motivo, 0) + 1

    totais = {
        "linhas_lidas": len(contexto.linhas),
        "linhas_colapsadas_intra_arquivo": linhas_colapsadas,
        "criados": resultado_bulk.criados,
        "atualizados": resultado_bulk.atualizados,
        "sem_mudanca": resultado_bulk.sem_mudanca,
        "rejeitados": len(todos_rejeitados),
    }

    # Declaracao_hash — junta os 3 booleanos + procedencia em um payload
    # canonicalizado (chaves ordenadas) e SHA-256.
    import json

    decl_payload = json.dumps(
        {
            "tem_base_legal": contexto.declaracao_tem_base_legal,
            "compromisso_comunicar_titulares": contexto.declaracao_compromisso_comunicar,
            "declara_sem_dados_sensiveis": contexto.declaracao_sem_sensiveis,
            "procedencia_declarada": contexto.procedencia_declarada,
            "pf_aceite_origem": contexto.pf_aceite_origem,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    declaracao_hash = hashlib.sha256(decl_payload.encode("utf-8")).hexdigest()

    from uuid import uuid4

    return ResultadoExecucao(
        importacao_id=uuid4(),
        totais=totais,
        rejeitados_motivos_agregados=motivos_agregados,
        rejeitados=todos_rejeitados,
        declaracao_hash=declaracao_hash,
        linhas_colapsadas_intra_arquivo=linhas_colapsadas,
        dados_sensiveis_filtrados=dados_sensiveis_filtrados,
        pj_dispensa_aceite=contadores["pj_dispensa_aceite"],
        pj_com_pf_pendente_aceite=contadores["pj_com_pf_pendente_aceite"],
        pf_rejeitadas_por_falta_aceite=contadores["pf_rejeitadas_por_falta_aceite"],
    )


def _base_legal_do_origem(origem: str) -> str:
    # T-CLI-101: enum LGPD alinhado com spec FORWARD (5 bases). Mapeamento
    # canonico mora em lgpd.PF_ORIGEM_PARA_BASE_LEGAL; aqui apenas delegacao
    # pra manter funcao pura sem import circular do use case.
    from src.infrastructure.clientes.lgpd import PF_ORIGEM_PARA_BASE_LEGAL

    return PF_ORIGEM_PARA_BASE_LEGAL.get(origem, "")
