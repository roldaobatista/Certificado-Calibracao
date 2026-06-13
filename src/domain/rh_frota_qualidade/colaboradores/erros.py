"""Erros de domínio do módulo `colaboradores` (T-COL-015).

10 erros de regra de negócio. Mapeados a HTTP na camada REST (Fatia 2).
Molde: `precificacao/erros.py` (mesmo padrão de classe com `reason`).

Refs: spec §4 Erros; D-COL-3/4/9/11; INV-COL-*.
"""

from __future__ import annotations


class ColaboradorError(Exception):
    """Base dos erros de domínio de colaboradores."""


class DuplicateCpf(ColaboradorError):
    """INV-COL-CPF — CPF já cadastrado para colaborador ativo no tenant.

    UNIQUE parcial (tenant_id, cpf) WHERE deletado_em IS NULL no banco.
    Re-cadastro após soft-delete é permitido (CPF liberado com o soft-delete).
    → 409 DUPLICATE_CPF.
    """

    reason = "DUPLICATE_CPF"


class SignatarioSemUsuario(ColaboradorError):
    """INV-COL-SIGNATARIO-IDENTIDADE — colaborador sem usuario_id recebeu papel SIGNATARIO.

    SIGNATARIO exige usuario_id NOT NULL (D-COL-2 / D-COL-11).
    Sem usuario_id, não é possível casar com RTCompetencia vigente.
    → 422 SIGNATARIO_SEM_USUARIO.
    """

    reason = "SIGNATARIO_SEM_USUARIO"


class SignatarioRtNaoCasa(ColaboradorError):
    """INV-COL-SIGNATARIO-IDENTIDADE — RTCompetencia não casa com colaborador.usuario_id.

    A RTCompetencia vigente deve ter o MESMO usuario_id que o colaborador
    (D-COL-11 / TL-COL-01). Não basta "FK RT existe" — precisa casar a pessoa.
    A verdade probatória do signatário mora no RT (WORM), não no colaborador.
    → 422 SIGNATARIO_RT_NAO_CASA.
    """

    reason = "SIGNATARIO_RT_NAO_CASA"


class SignatarioSemEscopo(ColaboradorError):
    """INV-COL-SIGNATARIO-ESCOPO — escopo do RT não vigente na data de atribuição.

    RTCompetencia deve ter escopo vigente na data (INV-003 / D-COL-11).
    Bloqueio HARD em perfil A; configurável B/C/D (GATE-COL-PERFIL-MATRIZ).
    → 422 SIGNATARIO_SEM_ESCOPO.
    """

    reason = "SIGNATARIO_SEM_ESCOPO"


class CpfInvalido(ColaboradorError):
    """CPF inválido — formato, DV ou sequência trivial.

    Levantado pelo VO `CPF` (src/domain/shared/value_objects.py).
    Re-levantado aqui para uniformidade de tratamento na camada REST.
    → 422 CPF_INVALIDO.
    """

    reason = "CPF_INVALIDO"


class ColaboradorInativo(ColaboradorError):
    """Operação inválida em colaborador desligado ou soft-deletado (D-COL-3).

    Tentativa de editar, atribuir papel ou realizar operação de negócio
    em colaborador com data_desligamento ou deletado_em preenchidos.
    → 409 COLABORADOR_INATIVO.
    """

    reason = "COLABORADOR_INATIVO"


class DonoJaExiste(ColaboradorError):
    """INV-COL-DONO-UNICO — já existe papel DONO ativo no tenant (D-COL-4).

    Partial unique no banco: papel='DONO' AND data_fim IS NULL AND revogado_em IS NULL.
    Troca de DONO requer revogar o atual antes (advisory lock — ADR-0065 / TL-COL-11).
    → 409 DONO_JA_EXISTE.
    """

    reason = "DONO_JA_EXISTE"


class HardDeleteBloqueado(ColaboradorError):
    """INV-COL-INATIVO — hard-delete físico bloqueado por referência a jusante (D-COL-3).

    Colaborador referenciado em OS, certificado ou comissão não pode ser deletado
    fisicamente. Trigger PG defensivo BEFORE DELETE (Fatia 1b) e porta
    `ColaboradorReferenciadoPort` (fail-safe conservador — ADR-0066).
    → 409 HARD_DELETE_BLOQUEADO.
    """

    reason = "HARD_DELETE_BLOQUEADO"


class ComissaoForaDaFaixa(ColaboradorError):
    """comissao_default_pct fora do intervalo 0..100 (D-COL-9 / CHECK 0..100).

    Validação de domínio precede o CHECK do banco (Fatia 1b).
    → 422 COMISSAO_FORA_DA_FAIXA.
    """

    reason = "COMISSAO_FORA_DA_FAIXA"


class DocumentoIncompativelVinculo(ColaboradorError):
    """INV-COL-DOC-VINCULO — documento incompatível com vínculo empregatício.

    CTPS é incompatível com PJ e TERCEIRIZADO (minimização LGPD art. 6º III
    / ADV-COL-01). Use case registra aviso; 422 somente se o tenant configurar
    bloqueio (Wave B — por ora é alerta).
    → 422 DOCUMENTO_INCOMPATIVEL_VINCULO (quando bloqueio ativo).
    """

    reason = "DOCUMENTO_INCOMPATIVEL_VINCULO"
