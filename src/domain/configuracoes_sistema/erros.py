"""Erros de domínio do módulo `configuracoes-sistema` (Fatia 1a — T-CFG-014).

Erros de regra de negócio (não de infra). Mapeados a HTTP na camada REST.
"""

from __future__ import annotations


class ConfiguracoesSistemaError(Exception):
    """Base dos erros de domínio do módulo."""


class NumeroNuncaDiminuiError(ConfiguracoesSistemaError):
    """INV-028 — `proximo_numero` de uma série nunca pode diminuir."""


class MatrizInvalidaError(ConfiguracoesSistemaError):
    """INV-037 — exatamente 1 filial matriz por empresa (nem 0 com filiais, nem >1)."""


class CnpjDuplicadoError(ConfiguracoesSistemaError):
    """INV-036 — CNPJ único por tenant (empresa/filial).

    Enforcement hoje é a UNIQUE do banco (view mapeia IntegrityError→409);
    classe reservada pra consumidor de domínio puro (sem caller ainda — nota
    consultiva da 2ª passada P9)."""


class ImpostoVigenciaSobrepostaError(ConfiguracoesSistemaError):
    """INV-CFG-IMPOSTO-SEM-SOBREPOSICAO — duas vigências do mesmo (tipo, filial) colidem."""


class ImpostoImutavelError(ConfiguracoesSistemaError):
    """INV-CFG-IMPOSTO-IMUTAVEL — alíquota/tipo/vigencia_inicio de linha existente não muda.

    Enforcement hoje é o trigger WORM (0003); classe reservada pra consumidor
    de domínio puro (sem caller ainda — nota consultiva da 2ª passada P9)."""


class TipoDocumentoNaoNumeravelError(ConfiguracoesSistemaError):
    """NFS-e/NF não são numeradas localmente (BaaS/município — ADR-0080).

    Enforcement hoje é o ChoiceField/enum `TipoDocumento` (nf/nfse nem existem
    como tipo de série); classe reservada pra consumidor de domínio puro."""
