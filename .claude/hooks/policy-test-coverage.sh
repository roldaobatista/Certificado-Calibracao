#!/usr/bin/env bash
# =============================================================
# policy-test-coverage.sh
# Quando migration cria CREATE POLICY (RLS), exige comentario apontando
# arquivos de teste com happy-path E unhappy-path.
#
# Pega gap do drill F-A 2026-05-18: bug GRAVE #5 (RLS fail-soft) so foi
# pego porque alguem rodou o teste unhappy-path. Mas o teste so existia
# por acaso. Agora forcamos o agente IA pensar nisso.
#
# Como funciona:
#   - Le tool_input.content / new_string + file_path
#   - So aciona em arquivos */migrations/*.py
#   - Se tem CREATE POLICY mas nao tem comentario
#     "# tests-coverage: tests/<arquivo>.py" -> bloqueia
#   - O agente IA tem que apontar onde estao os testes happy/unhappy
#     da policy
#
# Allow override: comentario '# policy-test-coverage: skip -- <razao>'
# com pelo menos 10 chars de justificativa.
#
# Como testar:
#   echo '{"tool_input":{"file_path":"app/migrations/0042_policy.py","content":"CREATE POLICY p1 ON t USING (true);"}}' | bash .claude/hooks/policy-test-coverage.sh
#   echo $?  # esperar 2 (sem comentario tests-coverage)
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

# So aciona em migrations Python
case "$norm_path" in
    */migrations/*.py) ;;
    *) exit 0 ;;
esac

# Pula __init__.py
case "$norm_path" in
    */migrations/__init__.py) exit 0 ;;
esac

# Detecta CREATE POLICY (RLS)
if ! printf '%s' "$content" | grep -qiE 'CREATE[[:space:]]+POLICY'; then
    exit 0  # migration sem policy = nao se aplica
fi

# Override por comentario justificado (>= 10 chars apos --)
if printf '%s' "$content" | grep -qE '#[[:space:]]*policy-test-coverage:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# Exige comentario tests-coverage apontando arquivos
# Formato aceito:
#   # tests-coverage: tests/test_isolamento.py
#   # tests-coverage: tests/test_x.py, tests/test_y.py
if ! printf '%s' "$content" | grep -qE '#[[:space:]]*tests-coverage:[[:space:]]*tests/'; then
    echo "policy-test-coverage: migration com CREATE POLICY sem comentario apontando testes em $file_path" >&2
    echo "Drill F-A 2026-05-18 descobriu bug GRAVE em policy RLS (#5 fail-soft) — toda policy precisa" >&2
    echo "ter teste UNHAPPY-PATH explicito (rejeicao de uso ilegitimo), nao so happy-path." >&2
    echo "" >&2
    echo "Adicione comentario na migration apontando o arquivo de teste:" >&2
    echo "    # tests-coverage: tests/test_isolamento_cross_tenant.py" >&2
    echo "" >&2
    echo "O arquivo apontado DEVE conter assert pra cenario legitimo (happy) E" >&2
    echo "pytest.raises pra cenario ilegitimo (unhappy)." >&2
    echo "" >&2
    echo "Override raro: '# policy-test-coverage: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

# Bonus: valida formato basico — tests-coverage deve apontar pra tests/
caminho_apontado=$(printf '%s' "$content" | grep -E '#[[:space:]]*tests-coverage:' | head -1 | sed -E 's/.*tests-coverage:[[:space:]]*//' | tr ',' '\n' | head -1 | tr -d '[:space:]')
case "$caminho_apontado" in
    tests/*.py|tests/*/*.py) ;;
    *)
        echo "policy-test-coverage: tests-coverage deve apontar 'tests/...' (achou: '$caminho_apontado')" >&2
        exit 2
        ;;
esac

exit 0
