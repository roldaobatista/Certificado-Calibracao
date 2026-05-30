#!/usr/bin/env bash
# =============================================================
# escopo-extracao-nao-auto-persiste-check.sh — M6 P7 / INV-ECMC-007 (T-ECMC-062)
#
# Garante que a extracao do PDF da CGCRE NUNCA persista um escopo vigente sem
# conferencia humana. O caminho de importacao (`importar_escopo_pdf` /
# `parsear_tabela`) so pode criar `EscopoExtraido` em RASCUNHO_EXTRAIDO
# (staging, mutavel). A promocao para CONFIRMADO (WORM) e EXCLUSIVA do use case
# `confirmar_escopo_extraido` (acao authz `escopos_cmc.confirmar_extraido`).
#
# Por que existir:
#   Escopo regulatorio auto-extraido e persistido como vigente sem conferencia
#   = lab emite RBC sobre faixa/CMC que ninguem validou (INV-ECMC-007 /
#   decisao N Roldao 2026-05-29). A extracao e conveniencia; a barreira humana
#   e obrigatoria.
#
# Heuristica:
#   Gatilho = arquivo `importar_escopo_pdf.py` OU conteudo que chama
#   `parsear_tabela(` junto de marcador de staging (EscopoExtraido / RASCUNHO_
#   EXTRAIDO). Se ESSE conteudo tambem persiste vigente (EstadoEscopo.CONFIRMADO,
#   estado="CONFIRMADO", cadastrar_executar(/cadastrar_escopo.executar() => cria
#   linha CONFIRMADA) => BLOCK.
#
# Auto-allow (exit 0):
#   - confirmar_escopo_extraido.py (o promotor sancionado)
#   - tests/**, *_test.py, conftest.py
#   - **/migrations/**, .md / nao-.py
#
# Override: '# escopo-extracao-auto-persiste: skip -- <razao com >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/application/metrologia/escopos_cmc/importar_escopo_pdf.py","content":"linhas = parsear_tabela(x)\nEscopoExtraido(...)\ncadastrar_executar(linha, repo)"}}' | bash .claude/hooks/escopo-extracao-nao-auto-persiste-check.sh; echo $?  # 2
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
    */migrations/*) exit 0 ;;
    docs/*|*/docs/*) exit 0 ;;
    # Promotor sancionado: confirmar_escopo_extraido REUSA cadastrar de proposito.
    *confirmar_escopo_extraido.py) exit 0 ;;
esac

if printf '%s' "$content" | grep -qE '#[[:space:]]*escopo-extracao-auto-persiste:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# Gatilho: e o caminho de importacao/extracao?
is_extracao=0
case "$norm_path" in
    *importar_escopo_pdf.py) is_extracao=1 ;;
esac
if [ "$is_extracao" -eq 0 ]; then
    if printf '%s' "$content" | grep -qE 'parsear_tabela[[:space:]]*\(' \
        && printf '%s' "$content" | grep -qE 'EscopoExtraido[[:space:]]*\(|RASCUNHO_EXTRAIDO'; then
        is_extracao=1
    fi
fi
[ "$is_extracao" -eq 0 ] && exit 0

# Persiste vigente no mesmo conteudo?
persiste=""
if printf '%s' "$content" | grep -qE 'EstadoEscopo\.CONFIRMADO|estado["'"'"']?[[:space:]]*[:=][[:space:]]*["'"'"']CONFIRMADO'; then
    persiste='cria linha em estado CONFIRMADO direto'
elif printf '%s' "$content" | grep -qE 'cadastrar_executar[[:space:]]*\(|cadastrar_escopo\.executar[[:space:]]*\('; then
    persiste='chama cadastrar_escopo (gera CONFIRMADO) no caminho de extracao'
fi

if [ -n "$persiste" ]; then
    echo "escopo-extracao-nao-auto-persiste (INV-ECMC-007): extracao persistindo escopo vigente em $file_path" >&2
    echo "Padrao detectado: $persiste" >&2
    echo "" >&2
    echo "A extracao do PDF CGCRE so pode criar EscopoExtraido (RASCUNHO_EXTRAIDO," >&2
    echo "staging mutavel). A promocao para CONFIRMADO (WORM) e EXCLUSIVA do use" >&2
    echo "case confirmar_escopo_extraido (acao 'escopos_cmc.confirmar_extraido')," >&2
    echo "que registra QUEM/QUANDO conferiu (INV-ECMC-007 / decisao N)." >&2
    echo "Override: '# escopo-extracao-auto-persiste: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
