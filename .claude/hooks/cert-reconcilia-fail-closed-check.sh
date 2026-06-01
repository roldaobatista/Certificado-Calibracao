#!/usr/bin/env bash
# =============================================================
# cert-reconcilia-fail-closed-check.sh — M8 Fatia 3 / INV-CER-RECONCILIA-002/005 (T-CER-053)
#
# Protege o fail-closed do nucleo de reconciliacao da emissao. `reconciliar_pontos`
# (dominio) e `emitir_certificado` (use case) NAO podem regredir para fail-open:
# orcamento duplicado por ponto, ponto sem orcamento e faixa declarada ausente DEVEM
# abortar (raise), nunca "passar" silenciosamente — senao emite-se RBC com incerteza
# ambigua/ausente (cl. 7.8 / ILAC-P14, fraude metrologica).
#
# Por que existir:
#   A garantia de runtime sao os raises + TestINV_CER_RECONCILIA_002/005; este hook
#   (camada A) impede um edit silencioso de gutar o avaliador/use case para liberar
#   geral (ex.: trocar `raise OrcamentoPontoAmbiguoError` por um fallback).
#
# Heuristica (so nos 2 arquivos canonicos):
#   - */metrologia/certificados/reconciliacao.py que DEFINE `reconciliar_pontos`
#     mas PERDE `OrcamentoPontoAmbiguoError` ou `SemOrcamentoPontoError` -> BLOCK.
#   - */application/metrologia/certificados/emitir_certificado.py que DEFINE
#     `emitir_certificado` mas PERDE `FaixaDeclaradaAusenteError` -> BLOCK.
#
# Override: '# cert-reconcilia-fail-closed: skip -- <razao com >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/domain/metrologia/certificados/reconciliacao.py","content":"def reconciliar_pontos(): return None"}}' | bash .claude/hooks/cert-reconcilia-fail-closed-check.sh; echo $?  # 2
# =============================================================

set -u

input=$(cat)

content=$(printf '%s' "$input" | perl -MJSON::PP -e '
    local $/;
    my $raw = <STDIN>;
    my $j;
    eval { $j = JSON::PP->new->decode($raw); 1 } or exit 0;
    my $ti = $j->{tool_input} // {};
    print $ti->{content} // $ti->{new_string} // "";
' 2>/dev/null)

file_path=$(printf '%s' "$input" | perl -MJSON::PP -e '
    local $/;
    my $raw = <STDIN>;
    my $j;
    eval { $j = JSON::PP->new->decode($raw); 1 } or exit 0;
    print $j->{tool_input}{file_path} // "";
' 2>/dev/null)

[ -z "$content" ] && exit 0

norm_path="${file_path//\\//}"

if printf '%s' "$content" | grep -qE '#[[:space:]]*cert-reconcilia-fail-closed:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

faltou=""
case "$norm_path" in
    */metrologia/certificados/reconciliacao.py)
        if printf '%s' "$content" | grep -qE 'def[[:space:]]+reconciliar_pontos[[:space:]]*\('; then
            if ! printf '%s' "$content" | grep -qE 'OrcamentoPontoAmbiguoError'; then
                faltou="raise OrcamentoPontoAmbiguoError (orcamento duplicado por ponto — INV-CER-RECONCILIA-005)"
            elif ! printf '%s' "$content" | grep -qE 'SemOrcamentoPontoError'; then
                faltou="raise SemOrcamentoPontoError (ponto sem orcamento — pre-condicao da emissao)"
            fi
        fi
        ;;
    */application/metrologia/certificados/emitir_certificado.py)
        if printf '%s' "$content" | grep -qE 'def[[:space:]]+emitir_certificado[[:space:]]*\('; then
            if ! printf '%s' "$content" | grep -qE 'FaixaDeclaradaAusenteError'; then
                faltou="raise FaixaDeclaradaAusenteError (calibracao sem faixa declarada — ADR-0076)"
            fi
        fi
        ;;
    *) exit 0 ;;
esac

if [ -n "$faltou" ]; then
    echo "cert-reconcilia-fail-closed (INV-CER-RECONCILIA-002/005): fail-closed perdido em $file_path" >&2
    echo "Faltando: $faltou" >&2
    echo "" >&2
    echo "A reconciliacao da emissao e fail-closed: orcamento ambiguo/ausente e faixa" >&2
    echo "declarada ausente DEVEM abortar (raise), nunca emitir RBC com incerteza" >&2
    echo "ambigua/ausente (cl. 7.8 / ILAC-P14). Nao reintroduza fallback fail-open." >&2
    echo "Override: '# cert-reconcilia-fail-closed: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
