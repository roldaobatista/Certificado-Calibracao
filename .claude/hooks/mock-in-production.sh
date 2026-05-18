#!/usr/bin/env bash
# =============================================================
# mock-in-production.sh
# Bloqueia gravacao de dados/mocks/fixtures em ARQUIVO DE PRODUCAO.
# Plano anti-erros-ia.md Grupo 1: "Mock/dados falsos em arquivo de producao".
# Evento: PreToolUse(Write|Edit) em codigo de aplicacao
#
# Stack-agnostico — detecta padroes genericos validos em qualquer linguagem:
#   - Comentarios marcadores: // MOCK, # MOCK, // FAKE DATA, # DUMMY DATA
#   - Identificadores: variaveis/constantes com sufixo/prefixo _MOCK, _FAKE,
#     MOCK_, FAKE_, DUMMY_ (em caixa alta — convencao consistente cross-stack)
#   - Lorem ipsum em codigo (texto placeholder classico)
#
# Paths ignorados (mock e LEGITIMO):
#   - */tests/*, *_test.*, *.test.*, *.spec.*, *Test.<ext>
#   - */fixtures/*, */seeds/*, */factories/*, */mocks/*, */__mocks__/*
#   - */examples/*
#   - docs/*, *.md, *.rst, *.txt
#   - */migrations/* (seeds de migration sao aceitos)
#
# Exit 0 = permite | Exit 2 = bloqueia.
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/views/pedidos.py","content":"FAKE_USERS = [{\"id\":1}]"}}' | bash .claude/hooks/mock-in-production.sh
#   echo $?    # esperar 2
#
#   echo '{"tool_input":{"file_path":"tests/test_x.py","content":"FAKE_USERS = [{\"id\":1}]"}}' | bash .claude/hooks/mock-in-production.sh
#   echo $?    # esperar 0
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
[ -z "$file_path" ] && exit 0

# Normaliza separadores pra checagem cross-platform
fp_norm=$(printf '%s' "$file_path" | tr '\\' '/')

# So aplica a arquivos de codigo
case "$fp_norm" in
    *.py|*.js|*.ts|*.tsx|*.jsx|*.dart|*.rb|*.go|*.java|*.kt|*.swift|*.php|*.cs) ;;
    *) exit 0 ;;
esac

# Paths onde mock e legitimo — exit cedo
# Cobre diretorio na raiz (ex: "tests/x.py") e em subnivel (ex: "src/app/tests/x.py")
case "$fp_norm" in
    tests/*|*/tests/*|test/*|*/test/*) exit 0 ;;
    *_test.*|*.test.*|*.spec.*|spec/*|*/spec/*|*/specs/*|specs/*) exit 0 ;;
    test_*|*/test_*) exit 0 ;;
    *Test.py|*Test.ts|*Test.java|*Test.kt|*Test.cs) exit 0 ;;
    fixtures/*|*/fixtures/*|*/fixture/*|seeds/*|*/seeds/*|*/seed/*) exit 0 ;;
    factories/*|*/factories/*|*/factory/*|mocks/*|*/mocks/*|*/mock/*|*/__mocks__/*) exit 0 ;;
    examples/*|*/examples/*|*/example/*|samples/*|*/samples/*|*/sample/*) exit 0 ;;
    migrations/*|*/migrations/*|*/migrate/*) exit 0 ;;
    */conftest.py|*/setup.py|*/conftest.*|conftest.py) exit 0 ;;
esac

violations=()

# Padrao 1: comentarios marcadores explicitos
# Aceita variacoes de espacamento mas exige palavra-chave em caixa alta (convencao)
if printf '%s' "$content" | grep -qE '(//|#)[[:space:]]*(MOCK|FAKE[[:space:]]+DATA|DUMMY[[:space:]]+DATA|FAKE[[:space:]]+USER|HARDCODED|TODO[[:space:]]*:[[:space:]]*remove)' ; then
    violations+=("comentario marcador (MOCK/FAKE DATA/DUMMY DATA/HARDCODED)")
fi

# Padrao 2: identificadores em caixa alta com prefixo/sufixo de mock
# Ex: FAKE_USERS = [..], MOCK_RESPONSE = .., DUMMY_DATA = ..
# Restrito a caixa alta + underscore pra evitar falsos positivos em nomes
# genuinos tipo "fakeNews" (palavra de dominio) ou "mockingbird".
if printf '%s' "$content" | grep -qE '(^|[^A-Za-z0-9_])(FAKE|MOCK|DUMMY|STUB)_[A-Z][A-Z0-9_]*[[:space:]]*=' ; then
    violations+=("identificador FAKE_/MOCK_/DUMMY_/STUB_ em caixa alta")
fi

if printf '%s' "$content" | grep -qE '[A-Z][A-Z0-9_]*_(FAKE|MOCK|DUMMY|STUB)[[:space:]]*=' ; then
    violations+=("identificador *_FAKE/*_MOCK/*_DUMMY/*_STUB em caixa alta")
fi

# Padrao 3: lorem ipsum em codigo
if printf '%s' "$content" | grep -qiE 'lorem[[:space:]]+ipsum' ; then
    violations+=("texto placeholder 'lorem ipsum' em codigo de producao")
fi

if [ ${#violations[@]} -gt 0 ]; then
    echo "mock-in-production: dados falsos detectados em $file_path" >&2
    for v in "${violations[@]}"; do
        echo "  - $v" >&2
    done
    echo "Mocks/fixtures/seeds vao em tests/, fixtures/, seeds/, factories/." >&2
    echo "Plano anti-erros-ia.md (Grupo 1): mock em producao mascara bugs reais." >&2
    exit 2
fi

exit 0
