#!/usr/bin/env bash
# =============================================================
# biometria-key-validator.sh
# INV-OS-ACEITE-BIO-001 — biometria touch (AceiteAtividade.assinatura_base64)
# e dado sensivel LGPD art. 11.
#
# Bloqueia codigo que:
#   - descriptografa/decode assinatura_base64 SEM usar BIOMETRIA_KEY_<tenant>
#   - acessa assinatura_base64 SEM registrar audit em acessos_dados_cliente
#
# Allow via: `# biometria-key-validator: skip -- <razao>`
# =============================================================

set -u
input=$(cat)

content=$(printf '%s' "$input" | perl -MJSON::PP -e '
    local $/; my $raw = <STDIN>; my $j;
    eval { $j = JSON::PP->new->decode($raw); 1 } or exit 0;
    my $ti = $j->{tool_input} // {};
    print $ti->{content} // $ti->{new_string} // "";
' 2>/dev/null)

file_path=$(printf '%s' "$input" | perl -MJSON::PP -e '
    local $/; my $raw = <STDIN>; my $j;
    eval { $j = JSON::PP->new->decode($raw); 1 } or exit 0;
    print $j->{tool_input}{file_path} // "";
' 2>/dev/null)

[ -z "$content" ] && exit 0
file_path_norm=$(printf '%s' "$file_path" | tr '\\' '/')

# Pula testes
case "$file_path_norm" in
    *.py) ;;
    *) exit 0 ;;
esac
case "$file_path_norm" in
    */tests/*|*/test_*|*_test.py|*/migrations/*) exit 0 ;;
esac

# Allow via skip
if printf '%s' "$content" | grep -qE 'biometria-key-validator:\s*skip\s*--\s*.{5,}'; then
    exit 0
fi

# Detecta acesso a assinatura_base64
if printf '%s' "$content" | grep -qE 'assinatura_base64|AssinaturaTouch|aceite_biometrico'; then
    # Regra 1: descriptografia exige BIOMETRIA_KEY_*
    if printf '%s' "$content" | grep -qE '(decrypt|descriptografar|kms\.decrypt|base64\.b64decode.*assinatura)'; then
        if ! printf '%s' "$content" | grep -qE 'BIOMETRIA_KEY'; then
            echo "biometria-key-validator (INV-OS-ACEITE-BIO-001): descriptografia de assinatura touch sem BIOMETRIA_KEY_* em $file_path" >&2
            echo "Chave KMS dedicada por tenant — separada da chave PII geral (LGPD art. 11)." >&2
            echo "Allow via: # biometria-key-validator: skip -- <razao>" >&2
            exit 2
        fi
        # Regra 2: leitura exige audit AcessoDadosCliente
        if ! printf '%s' "$content" | grep -qE '(AcessoDadosCliente|registrar_acesso_pii|acesso_dados_cliente)'; then
            echo "biometria-key-validator (INV-OS-ACEITE-BIO-001 + INV-013): leitura de assinatura touch sem audit AcessoDadosCliente em $file_path" >&2
            echo "Toda leitura de biometria exige audit + finalidade=defesa_em_juizo." >&2
            exit 2
        fi
    fi
fi

exit 0
