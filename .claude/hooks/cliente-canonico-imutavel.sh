#!/usr/bin/env bash
# =============================================================
# cliente-canonico-imutavel.sh — T-CLI-113 / AC-CLI-005-7 / INV-CLI-001
#
# Bloqueia (exit 2) qualquer escrita que tente burlar a invariante de
# identidade canônica `cliente.cliente_canonico_id`:
#   - DROP TRIGGER cliente_canonico_imutavel_trg
#   - DROP FUNCTION cliente_canonico_imutavel_check
#   - DROP TRIGGER cliente_canonico_default_trg
#   - DROP FUNCTION cliente_canonico_default_on_insert
#   - ALTER TABLE clientes DROP COLUMN cliente_canonico_id
#   - ALTER TABLE clientes ALTER COLUMN cliente_canonico_id ...
#   - UPDATE clientes SET cliente_canonico_id = ... (fora de mesclagem
#     legítima — caminho oficial é via use case de US-CLI-005)
#
# AUTO-ALLOW: a própria migration de criação do trigger/coluna tem
# REVERSE_SQL com DROP. Heurística: se o MESMO conteúdo também CRIA
# o trigger/função/coluna, é parte de uma migration válida.
#
# Override: linha contendo '# canonico-imutavel: skip -- <razão>=10 chars'
# (decisão consciente do Roldão pra migration de manutenção).
#
# Como testar:
#   echo '{"tool_input":{"file_path":"x.sql","content":"DROP TRIGGER cliente_canonico_imutavel_trg ON clientes;"}}' | bash .claude/hooks/cliente-canonico-imutavel.sh
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

# Só .py e .sql (código executável)
case "$norm_path" in
    *.py|*.sql) ;;
    *) exit 0 ;;
esac

# Pula testes
case "$norm_path" in
    */tests/*|*/test_*|*_test.py) exit 0 ;;
esac

# AUTO-ALLOW: a própria migration de criação do trigger/coluna tem
# REVERSE_SQL com DROP. Se o conteúdo também CRIA o trigger/função/coluna,
# é parte de uma migration legítima de criação+reverso.
if printf '%s' "$content" | grep -qiE 'CREATE[[:space:]]+TRIGGER[[:space:]]+cliente_canonico_'; then
    exit 0
fi
if printf '%s' "$content" | grep -qiE 'CREATE[[:space:]]+(OR[[:space:]]+REPLACE[[:space:]]+)?FUNCTION[[:space:]]+cliente_canonico_'; then
    exit 0
fi
if printf '%s' "$content" | grep -qiE 'ADD[[:space:]]+COLUMN[[:space:]]+cliente_canonico_id'; then
    exit 0
fi

# Override explícito com justificativa
if printf '%s' "$content" | grep -qE '#[[:space:]]*canonico-imutavel:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# AUTO-ALLOW para UPDATE legítimo dentro do módulo clientes (use case mesclagem
# + path compression em canonico.py). Heurística: arquivo é dentro de
# src/infrastructure/clientes/ ou src/application/comercial/clientes/ e o
# UPDATE acontece via ORM (não SQL cru aqui).
case "$norm_path" in
    *src/infrastructure/clientes/*|*src/application/comercial/clientes/*|*src/domain/comercial/clientes/*)
        # Só permite UPDATE via ORM (.update(cliente_canonico_id=...)),
        # bloqueia SQL cru "UPDATE clientes SET cliente_canonico_id ="
        if printf '%s' "$content" | grep -qiE 'UPDATE[[:space:]]+clientes[[:space:]]+SET[[:space:]]+cliente_canonico_id'; then
            echo "cliente-canonico-imutavel: UPDATE SQL cru em cliente_canonico_id detectado em $file_path" >&2
            echo "Use o ORM (.update(cliente_canonico_id=...)) que dispara a trigger PG de validação." >&2
            echo "Override: '# canonico-imutavel: skip -- <razão com >=10 chars>'" >&2
            exit 2
        fi
        exit 0
        ;;
esac

# Padrões que rasgam a defesa (fora do módulo)
violacao=""

if printf '%s' "$content" | grep -qiE 'DROP[[:space:]]+TRIGGER[[:space:]]+cliente_canonico_'; then
    violacao="DROP TRIGGER cliente_canonico_*"
elif printf '%s' "$content" | grep -qiE 'DROP[[:space:]]+FUNCTION[[:space:]]+cliente_canonico_'; then
    violacao="DROP FUNCTION cliente_canonico_*"
elif printf '%s' "$content" | grep -qiE 'ALTER[[:space:]]+TABLE[[:space:]]+clientes[[:space:]]+DROP[[:space:]]+COLUMN[[:space:]]+cliente_canonico_id'; then
    violacao="ALTER TABLE clientes DROP COLUMN cliente_canonico_id"
elif printf '%s' "$content" | grep -qiE 'ALTER[[:space:]]+TABLE[[:space:]]+clientes[[:space:]]+ALTER[[:space:]]+COLUMN[[:space:]]+cliente_canonico_id'; then
    violacao="ALTER TABLE clientes ALTER COLUMN cliente_canonico_id"
elif printf '%s' "$content" | grep -qiE 'UPDATE[[:space:]]+clientes[[:space:]]+SET[[:space:]]+cliente_canonico_id'; then
    violacao="UPDATE clientes SET cliente_canonico_id"
fi

if [ -n "$violacao" ]; then
    echo "cliente-canonico-imutavel: tentativa de burlar INV-CLI-001 em $file_path" >&2
    echo "Padrão detectado: $violacao" >&2
    echo "Identidade canônica é imutável runtime (trigger PG cliente_canonico_imutavel_trg)." >&2
    echo "Mesclagem usa use case US-CLI-005 + path compression em canonico.py — não SQL cru." >&2
    echo "Override (raro, exige aprovação Roldão): adicione '# canonico-imutavel: skip -- <razão >=10 chars>'" >&2
    exit 2
fi

exit 0
