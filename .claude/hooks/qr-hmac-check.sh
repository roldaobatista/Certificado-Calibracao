#!/usr/bin/env bash
# =============================================================
# qr-hmac-check.sh — Marco 2 SEC-QR-001 / INV-EQP-QR-NUNCA-RECOMPUTA
#
# Defende a chave HMAC do QR Code de equipamento. 3 bloqueios:
#
# 1. (HARDCODE) Hardcode de chave em codigo aplicacao
#    `QR_HMAC_KEY = "..."` literal em qualquer arquivo Python fora
#    de `config/settings/**`.
#
# 2. (DERIVADA) Derivacao de QR_HMAC_KEY a partir de SECRET_KEY em
#    `config/settings/prod.py` (P-EQP-T1 BLOQUEANTE: rotacao de
#    SECRET_KEY nao pode invalidar etiquetas fisicas).
#
# 3. (RECOMPUTA) `hmac.new(...QR_HMAC_KEY_REGISTRO...)` chamado FORA
#    de `src/infrastructure/equipamentos/services_qr.py` — helper
#    UNICO. Inclui consulta direta a `settings.QR_HMAC_KEY_REGISTRO`
#    via `hmac.new`. INV-EQP-QR-NUNCA-RECOMPUTA: validacao de scan
#    SEMPRE consulta a tabela `equipamentos_qrcode`.
#
# Auto-allow (exit 0):
#   - config/settings/**          (registry vive aqui)
#   - tests/**                    (testam o helper)
#   - **/migrations/**            (data migrations one-off)
#   - src/infrastructure/equipamentos/services_qr.py (helper unico)
#
# Override em arquivo fora da allowlist:
#   # qr-hmac: skip -- <razao com >=10 chars>
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/foo.py","content":"QR_HMAC_KEY = \"abc123\""}}' | bash .claude/hooks/qr-hmac-check.sh
#   echo $?  # 2
# =============================================================

set -u

input=$(cat)

content=$(printf '%s' "$input" | perl -MJSON::PP -e '
    local $/;
    my $raw = <STDIN>;
    my $j;
    eval { $j = JSON::PP->new->decode($raw); 1 } or exit 0;
    my $ti = $j->{tool_input} // {};
    my $c = $ti->{content} // $ti->{new_string} // "";
    print $c;
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

# So .py (SQL puro nao trafega chave de aplicacao)
case "$norm_path" in
    *.py) ;;
    *) exit 0 ;;
esac

# AUTO-ALLOW pelo caminho. Settings tem regras especiais (vide bloco 2 abaixo).
auto_allow=0
case "$norm_path" in
    tests/*|*/tests/*|*/test_*|*_test.py) auto_allow=1 ;;
    */migrations/*) auto_allow=1 ;;
    src/infrastructure/equipamentos/services_qr.py|*src/infrastructure/equipamentos/services_qr.py) auto_allow=1 ;;
esac

# Override com justificativa
if printf '%s' "$content" | grep -qE '#[[:space:]]*qr-hmac:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# =============================================================
# 1. HARDCODE: QR_HMAC_KEY = "..." ou QR_HMAC_KEY_ID com literal de
#    chave (>=8 chars de segredo) FORA de settings.
# =============================================================
case "$norm_path" in
    config/settings/*|*/config/settings/*) ;;  # settings: literal proibido tambem (vide bloco 2)
    *)
        if [ "$auto_allow" -eq 0 ]; then
            if printf '%s' "$content" | grep -qE '\bQR_HMAC_KEY[[:space:]]*=[[:space:]]*['\''"][^'\''"]{4,}['\''"]'; then
                echo "qr-hmac-check (HARDCODE): chave QR_HMAC_KEY literal em $file_path" >&2
                echo "Use env var QR_HMAC_KEY + settings.QR_HMAC_KEY_REGISTRO (vide config/settings/base.py)." >&2
                exit 2
            fi
        fi
        ;;
esac

# =============================================================
# 2. DERIVADA: em prod.py NAO pode existir derivacao de QR_HMAC_KEY a
#    partir de SECRET_KEY (P-EQP-T1). Padrao detectado: linha que
#    casa simultaneamente "QR_HMAC" e "SECRET_KEY" em prod.py.
#    base.py PODE ter fallback dev (derivacao); prod.py nao.
# =============================================================
case "$norm_path" in
    config/settings/prod.py|*/config/settings/prod.py)
        if printf '%s' "$content" | grep -E '.*' | grep -qE 'QR_HMAC.*SECRET_KEY|SECRET_KEY.*QR_HMAC'; then
            echo "qr-hmac-check (DERIVADA): prod.py deriva QR_HMAC_KEY de SECRET_KEY em $file_path" >&2
            echo "Em prod a chave de QR DEVE ser dedicada (env var QR_HMAC_KEY)." >&2
            echo "Rotacao de SECRET_KEY nao pode invalidar etiquetas fisicas (P-EQP-T1)." >&2
            exit 2
        fi
        ;;
esac

# =============================================================
# 3. RECOMPUTA: hmac.new(...QR_HMAC_KEY_REGISTRO...) fora do helper
#    unico services_qr.py. Tambem detecta acesso direto a
#    `.chave_ativa()` ou `.chave(` do QR_HMAC_KEY_REGISTRO fora do
#    helper unico — qualquer codigo que pretenda recomputar e
#    suspeito (INV-EQP-QR-NUNCA-RECOMPUTA).
# =============================================================
if [ "$auto_allow" -eq 0 ]; then
    # Patterns que indicam uso direto do registry pra recomputar
    if printf '%s' "$content" | grep -qE 'QR_HMAC_KEY_REGISTRO\.(chave_ativa|chave[[:space:]]*\()'; then
        echo "qr-hmac-check (RECOMPUTA): acesso direto a QR_HMAC_KEY_REGISTRO.chave* em $file_path" >&2
        echo "Use src.infrastructure.equipamentos.services_qr.gerar_qr_hash_versionado()" >&2
        echo "ou verificar_qr_hash_em_tabela() — INV-EQP-QR-NUNCA-RECOMPUTA centraliza acesso a chave." >&2
        exit 2
    fi
    # hmac.new com QR_HMAC literal proximo
    if printf '%s' "$content" | grep -qE 'hmac\.new[[:space:]]*\([^)]*QR_HMAC'; then
        echo "qr-hmac-check (RECOMPUTA): hmac.new com QR_HMAC* em $file_path" >&2
        echo "Use src.infrastructure.equipamentos.services_qr (helper unico)." >&2
        echo "Validacao SEMPRE consulta tabela equipamentos_qrcode (INV-EQP-QR-NUNCA-RECOMPUTA)." >&2
        exit 2
    fi
fi

exit 0
