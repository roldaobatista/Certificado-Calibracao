#!/usr/bin/env bash
# =============================================================
# padrao-incertezas-so-via-recal.sh  (INV-PAD-006 / decisao C-10)
# Garante que incertezas_certificado / validade_certificado_rastreabilidade /
# proximo_recal de PadraoMetrologico so mudam dentro do fluxo de recal externo
# aprovado pelo RT (use case aprovar_recal_rt -> repo.aplicar_recal_aprovado,
# que faz `SET LOCAL app.padrao_recal_em_curso = '1'` liberando o trigger PG
# padrao_incertezas_so_via_recal_trg). UPDATE direto reescreveria a cadeia
# metrologica ex-post sem audit = fraude regulatoria (ISO 17025 cl. 6.5).
#
# Bloqueia (exit 2) escrita .py/.sql que contenha:
#   - DROP TRIGGER padrao_incertezas_so_via_recal_trg
#   - DROP FUNCTION padrao_incertezas_so_via_recal
#   - UPDATE padrao_metrologico SET ...(um dos 3 campos)...
#   - .update(...<um dos 3 campos>=...)  (ORM)
#   - obj.<um dos 3 campos> = ...  +  .save()  no mesmo conteudo
#
# Auto-allow (PASS):
#   - .md / docs (nao executa)
#   - tests / fixtures
#   - src/infrastructure/metrologia/padroes/repositories.py (home canonico do
#     aplicar_recal_aprovado + salvar_novo)
#   - conteudo com o marcador da via sancionada: app.padrao_recal_em_curso
#   - migration que TAMBEM recria o trigger/funcao (CREATE ... padrao_incertezas_so_via_recal)
#   - override: '# inv-pad-006: skip -- <razao com >=10 chars>'
#
# Camada A (pre-commit). A defesa dura e o trigger PG (so libera com o GUC);
# este hook e fail-fast no autor (defesa em profundidade).
#
# Como testar:
#   echo '{"tool_input":{"file_path":"x.py","content":"PadraoMetrologico.objects.filter(id=p).update(proximo_recal=d)"}}' | bash .claude/hooks/padrao-incertezas-so-via-recal.sh
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

# So .py e .sql (codigo executavel — markdown nao aciona)
case "$norm_path" in
    *.py|*.sql) ;;
    *) exit 0 ;;
esac

# Pula testes / fixtures
case "$norm_path" in
    */tests/*|*/test_*|*_test.py|*/fixtures/*) exit 0 ;;
esac

# AUTO-ALLOW: home canonico onde a mutacao sancionada vive (aplicar_recal_aprovado).
case "$norm_path" in
    */metrologia/padroes/repositories.py) exit 0 ;;
esac

# AUTO-ALLOW: marcador da via sancionada (SET LOCAL app.padrao_recal_em_curso).
if printf '%s' "$content" | grep -qiE 'app\.padrao_recal_em_curso'; then
    exit 0
fi

# AUTO-ALLOW: migration que recria o trigger/funcao (REVERSE_SQL convive com CREATE).
if printf '%s' "$content" | grep -qiE 'CREATE[[:space:]]+TRIGGER[[:space:]]+padrao_incertezas_so_via_recal'; then
    exit 0
fi
if printf '%s' "$content" | grep -qiE 'CREATE[[:space:]]+(OR[[:space:]]+REPLACE[[:space:]]+)?FUNCTION[[:space:]]+padrao_incertezas_so_via_recal'; then
    exit 0
fi

# Override com justificativa explicita (>= 10 chars uteis apos --)
if printf '%s' "$content" | grep -qE '#[[:space:]]*inv-pad-006:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

_campos='incertezas_certificado|validade_certificado_rastreabilidade|proximo_recal'
violacao=""

if printf '%s' "$content" | grep -qiE "DROP[[:space:]]+TRIGGER[[:space:]]+(IF[[:space:]]+EXISTS[[:space:]]+)?padrao_incertezas_so_via_recal"; then
    violacao="DROP TRIGGER padrao_incertezas_so_via_recal_trg"
elif printf '%s' "$content" | grep -qiE "DROP[[:space:]]+FUNCTION[[:space:]]+(IF[[:space:]]+EXISTS[[:space:]]+)?padrao_incertezas_so_via_recal"; then
    violacao="DROP FUNCTION padrao_incertezas_so_via_recal"
elif printf '%s' "$content" | grep -qiE "UPDATE[[:space:]]+padrao_metrologico[[:space:]]+SET[^;]*($_campos)[[:space:]]*="; then
    violacao="UPDATE padrao_metrologico SET <campo de recal> ="
elif printf '%s' "$content" | grep -qE "\.update\([^)]*($_campos)[[:space:]]*="; then
    violacao=".update(<campo de recal>=...) fora do recal sancionado"
elif printf '%s' "$content" | grep -qE "\.($_campos)[[:space:]]*=[[:space:]]*[^=]" \
     && printf '%s' "$content" | grep -qE '\.save\('; then
    violacao="atribuicao a <campo de recal> seguida de .save() fora do recal sancionado"
fi

if [ -n "$violacao" ]; then
    echo "padrao-incertezas-so-via-recal: mutacao de incertezas/validade/proximo_recal fora do recal sancionado em $file_path" >&2
    echo "Padrao detectado: $violacao" >&2
    echo "ISO 17025 cl. 6.5 + C-10: esses 3 campos so mudam via aprovar_recal_rt -> repo.aplicar_recal_aprovado," >&2
    echo "que executa 'SET LOCAL app.padrao_recal_em_curso = 1' liberando o trigger PG padrao_incertezas_so_via_recal_trg." >&2
    echo "Override (raro, exige aprovacao Roldao): adicione '# inv-pad-006: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
