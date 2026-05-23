#!/usr/bin/env bash
# =============================================================
# seed-anti-pii-real.sh
# Onda 0 plano-v2 (2026-05-23) — auditor LGPD apontou que agente IA
# pode colar PII real em fixture/seed. Hook bloqueia commit que
# adicione padrao de CPF/CNPJ/email/telefone/RG/CEP real em paths
# de teste/fixture/seed.
#
# Lista canonica de valores sinteticos: docs/conformidade/comum/dados-sinteticos.md
#
# Aplica a:
#   - tests/fixtures/**
#   - tests/factories/**
#   - tests/conftest*.py
#   - **/seeds/**
#   - tests/**/*.json, *.csv, *.yaml
#
# Allow via:
#   - Comentario inline: # fixture-cpf-canonico (etc.)
#   - Arquivo inteiro: # seed-anti-pii: skip -- <razao ≥10 chars>
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

# Aplica somente a paths de teste/fixture/seed
# Aceita com ou sem prefixo (tests/... ou foo/tests/...)
case "$file_path_norm" in
    tests/fixtures/*|*/tests/fixtures/*) ;;
    tests/factories/*|*/tests/factories/*) ;;
    tests/conftest*.py|*/tests/conftest*.py) ;;
    seeds/*|*/seeds/*) ;;
    tests/*.json|*/tests/*.json|tests/*.csv|*/tests/*.csv) ;;
    tests/*.yaml|*/tests/*.yaml|tests/*.yml|*/tests/*.yml) ;;
    tests/*/*.json|*/tests/*/*.json|tests/*/*.csv|*/tests/*/*.csv) ;;
    tests/*/*.yaml|*/tests/*/*.yaml|tests/*/*.yml|*/tests/*/*.yml) ;;
    *) exit 0 ;;
esac

# Skip arquivo inteiro
if printf '%s' "$content" | grep -qE 'seed-anti-pii:\s*skip\s*--\s*.{10,}'; then
    exit 0
fi

violations=()

# ---------- CPF ----------
# Padrao real: NNN.NNN.NNN-NN ou NNNNNNNNNNN (11 digitos)
# Allowlist: sequencias repetidas (000..., 111..., etc) sao reconhecidas pela lista canonica
# Linha permitida tem o comentario "# fixture-cpf-canonico"
cpf_lines=$(printf '%s' "$content" | grep -nE '[^0-9]([0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2})[^0-9]' || true)
if [ -n "$cpf_lines" ]; then
    # Para cada match, verifica se eh sintetico (sequencia repetida) OU tem allowlist inline
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        # Extrai o CPF
        cpf=$(printf '%s' "$line" | grep -oE '[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}' | head -1)
        # Sintetico: todos digitos iguais (000.000.000-00 .. 999.999.999-99)
        if printf '%s' "$cpf" | grep -qE '^([0-9])\1{2}\.\1{3}\.\1{3}-\1{2}$'; then
            continue
        fi
        # Allowlist inline
        if printf '%s' "$line" | grep -qE 'fixture-cpf-canonico'; then
            continue
        fi
        violations+=("CPF nao-canonico em $file_path: $cpf (linha: ${line:0:80}...)")
    done <<< "$cpf_lines"
fi

# ---------- CNPJ ----------
# Padrao: NN.NNN.NNN/NNNN-NN
cnpj_lines=$(printf '%s' "$content" | grep -nE '[^0-9]([0-9]{2}\.[0-9]{3}\.[0-9]{3}/[0-9]{4}-[0-9]{2})[^0-9]' || true)
if [ -n "$cnpj_lines" ]; then
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        cnpj=$(printf '%s' "$line" | grep -oE '[0-9]{2}\.[0-9]{3}\.[0-9]{3}/[0-9]{4}-[0-9]{2}' | head -1)
        # Sintetico: digitos repetidos
        if printf '%s' "$cnpj" | grep -qE '^([0-9])\1\.\1{3}\.\1{3}/\1{4}-\1{2}$'; then
            continue
        fi
        # Allowlist inline
        if printf '%s' "$line" | grep -qE 'fixture-cnpj-canonico'; then
            continue
        fi
        violations+=("CNPJ nao-canonico em $file_path: $cnpj (linha: ${line:0:80}...)")
    done <<< "$cnpj_lines"
fi

# ---------- E-mail ----------
# Allowlist de dominios: example.com, example.org, example.net, test, afere.local, invalid
# Bloqueia: gmail/outlook/hotmail/yahoo/protonmail/icloud
email_lines=$(printf '%s' "$content" | grep -inE '@(gmail|outlook|hotmail|yahoo|protonmail|icloud)\.com' || true)
if [ -n "$email_lines" ]; then
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        if printf '%s' "$line" | grep -qE 'fixture-email-real'; then
            continue
        fi
        addr=$(printf '%s' "$line" | grep -oE '[a-zA-Z0-9._-]+@(gmail|outlook|hotmail|yahoo|protonmail|icloud)\.com' | head -1)
        violations+=("E-mail com dominio real proibido em $file_path: $addr")
    done <<< "$email_lines"
fi

# ---------- Telefone BR celular ----------
# Padrao: (NN) 9NNNN-NNNN com DDD valido (11..99) e 9 inicial
# Allowlist sintetica: (NN) 90000-0000 e (NN) 91111-1111 (digitos repetidos)
tel_lines=$(printf '%s' "$content" | grep -nE '\([0-9]{2}\)\s?9[0-9]{4}-[0-9]{4}' || true)
if [ -n "$tel_lines" ]; then
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        tel=$(printf '%s' "$line" | grep -oE '\([0-9]{2}\)\s?9[0-9]{4}-[0-9]{4}' | head -1)
        # Sintetico: depois do 9 inicial, todos digitos iguais
        if printf '%s' "$tel" | grep -qE '\([0-9]{2}\)\s?9([0-9])\1{3}-\1{4}$'; then
            continue
        fi
        if printf '%s' "$line" | grep -qE 'fixture-telefone-canonico'; then
            continue
        fi
        violations+=("Telefone celular nao-canonico em $file_path: $tel")
    done <<< "$tel_lines"
fi

# ---------- CEP ----------
# Padrao: NNNNN-NNN
# Allowlist sintetica: 00000-000, 99999-999 (digitos repetidos), 01310-100 (canonico)
cep_lines=$(printf '%s' "$content" | grep -nE '[^0-9]([0-9]{5}-[0-9]{3})[^0-9]' || true)
if [ -n "$cep_lines" ]; then
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        cep=$(printf '%s' "$line" | grep -oE '[0-9]{5}-[0-9]{3}' | head -1)
        case "$cep" in
            00000-000|99999-999|01310-100) continue ;;
        esac
        if printf '%s' "$line" | grep -qE 'fixture-cep-canonico'; then
            continue
        fi
        violations+=("CEP nao-canonico em $file_path: $cep")
    done <<< "$cep_lines"
fi

# ---------- Reporte ----------
if [ ${#violations[@]} -gt 0 ]; then
    echo "seed-anti-pii-real: PII real ou nao-canonica em fixture/seed/factory" >&2
    echo "" >&2
    for v in "${violations[@]}"; do
        echo "  - $v" >&2
    done
    echo "" >&2
    echo "Lista canonica permitida: docs/conformidade/comum/dados-sinteticos.md" >&2
    echo "Allow inline (linha): # fixture-cpf-canonico | # fixture-cnpj-canonico | # fixture-email-real | # fixture-telefone-canonico | # fixture-cep-canonico" >&2
    echo "Allow arquivo: # seed-anti-pii: skip -- <razao com ≥10 chars>" >&2
    exit 2
fi

exit 0
