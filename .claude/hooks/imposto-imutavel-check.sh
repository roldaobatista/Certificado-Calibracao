#!/usr/bin/env bash
# =============================================================
# imposto-imutavel-check.sh — configuracoes-sistema Fatia 3 / INV-CFG-IMPOSTO-IMUTAVEL (T-CFG-041)
#
# TL-04: linha de `Imposto` e versionada e IMUTAVEL — aliquota nova = NOVA linha
# com nova vigencia, nunca UPDATE; DELETE fisico bloqueado (retencao fiscal 5a,
# CTN art. 195). A barreira REAL e o trigger PG (`imposto_worm_check` +
# `imposto_block_delete`, migration 0003); este hook e a camada A (pre-commit)
# que pega:
#   a) codigo de producao mutando campo probatorio via ORM
#      (`Imposto.objects...update(aliquota=/tipo=/vigencia_inicio=)` ou
#      `.delete()` em queryset de Imposto);
#   b) migration derrubando os triggers da barreira (DROP TRIGGER
#      imposto_worm_check_trg / imposto_block_delete_trg) sem justificativa.
#
# Auto-allow (exit 0):
#   - tests/** ; docs/** ; nao-.py
#   - encerrar vigencia legitimo: `update(vigencia_fim=...)` SEM campo probatorio
#   - revogacao legitima: `update(revogado_em=..., motivo_revogacao=...)`
#
# Override: '# imposto-imutavel: skip -- <razao com >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/infrastructure/configuracoes_sistema/repositories.py","content":"Imposto.objects.filter(id=x).update(aliquota=v)"}}' | bash .claude/hooks/imposto-imutavel-check.sh; echo $?  # 2
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

case "$norm_path" in
    *.py) ;;
    *) exit 0 ;;
esac

case "$norm_path" in
    tests/*|*/tests/*|*/test_*|*_test.py|*conftest.py) exit 0 ;;
    docs/*|*/docs/*) exit 0 ;;
esac

if printf '%s' "$content" | grep -qE '#[[:space:]]*imposto-imutavel:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

codigo=$(printf '%s' "$content" | grep -vE '^[[:space:]]*#')

# b) migration derrubando a barreira (qualquer path .py)
if printf '%s' "$codigo" | grep -qiE 'DROP[[:space:]]+TRIGGER[[:space:]]+(IF[[:space:]]+EXISTS[[:space:]]+)?(imposto_worm_check_trg|imposto_block_delete_trg)'; then
    case "$norm_path" in
        */migrations/*)
            # reverse_sql legitimo da PROPRIA 0003 ja existe; qualquer NOVA migration
            # que derrube a barreira precisa de justificativa explicita.
            case "$norm_path" in
                *configuracoes_sistema/migrations/0003_triggers_worm.py) ;;
                *)
                    echo "imposto-imutavel (INV-CFG-IMPOSTO-IMUTAVEL): migration derruba trigger da barreira em $file_path" >&2
                    echo "Aliquota e versionada por linha (TL-04); remover o trigger reabre reescrita fiscal ex-post." >&2
                    echo "Override: '# imposto-imutavel: skip -- <razao com >=10 chars>'" >&2
                    exit 2
                    ;;
            esac
            ;;
    esac
fi

case "$norm_path" in
    */migrations/*) exit 0 ;;
esac

# a) mutacao de campo probatorio via ORM em codigo de producao
if printf '%s' "$codigo" | grep -qE 'Imposto(Model)?\.objects[^;]*\.update\([^)]*(aliquota|tipo|vigencia_inicio|filial_id|iss_retido_fonte|tem_st|simples_excedeu_sublimite|cfop_padrao|ncm_padrao)[[:space:]]*='; then
    echo "imposto-imutavel (INV-CFG-IMPOSTO-IMUTAVEL): UPDATE de campo probatorio de Imposto em $file_path" >&2
    echo "Aliquota nova = NOVA linha com nova vigencia (use cadastrar_imposto); nunca UPDATE (TL-04)." >&2
    echo "Mutaveis legitimos: vigencia_fim (encerrar, one-shot) e revogado_em+motivo (linha errada)." >&2
    echo "Override: '# imposto-imutavel: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

if printf '%s' "$codigo" | grep -qE 'Imposto(Model)?\.objects[^;]*\.delete\(\)'; then
    echo "imposto-imutavel (INV-CFG-IMPOSTO-IMUTAVEL): DELETE fisico de Imposto em $file_path" >&2
    echo "Retencao fiscal 5a (CTN art. 195) — linha errada usa revogado_em, nunca DELETE." >&2
    echo "Override: '# imposto-imutavel: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
