#!/usr/bin/env bash
# =============================================================
# lic-anexo-obrigatorio-check.sh — M9 Fatia 4 / INV-LIC-ANEXO-001 (T-LIC-062)
#
# Todo documento regulatorio (licenca/acreditacao/ART/RRT/certidao) exige anexo
# probatorio com sha256 server-side no cadastro/revisao (formaliza INV-046 para a
# entidade). Sem anexo o cadastro deve falhar 422 ANEXO_OBRIGATORIO.
#
# Heuristica (so use cases de licencas — camada que monta a RevisaoDocumento):
#   BLOCK quando um arquivo de `src/application/**/licencas_acreditacoes/**.py` CRIA
#   a entidade `RevisaoDocumento(` SEM chamar `validar_anexo(` no mesmo conteudo.
#   A validacao e responsabilidade do use case (o repositorio so persiste).
#
# Auto-allow (exit 0):
#   - fora de src/application/.../licencas_acreditacoes/ ; tests/** ; migrations/** ; nao-.py
#   - conteudo que chama `validar_anexo(` (gate presente)
#
# Override: '# lic-anexo-obrigatorio: skip -- <razao com >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/application/metrologia/licencas_acreditacoes/x.py","content":"RevisaoDocumento(\n  id=uuid4(),\n)"}}' | bash .claude/hooks/lic-anexo-obrigatorio-check.sh; echo $?  # 2
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
esac

# Escopo: so use cases de licencas (camada que monta a entidade de revisao).
case "$norm_path" in
    *src/application/*/licencas_acreditacoes/*) ;;
    *) exit 0 ;;
esac

if printf '%s' "$content" | grep -qE '#[[:space:]]*lic-anexo-obrigatorio:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# Gate presente no mesmo conteudo isenta.
if printf '%s' "$content" | grep -qE 'validar_anexo[[:space:]]*\('; then
    exit 0
fi

if printf '%s' "$content" | grep -qE 'RevisaoDocumento[[:space:]]*\('; then
    echo "lic-anexo-obrigatorio (INV-LIC-ANEXO-001): use case monta RevisaoDocumento sem validar_anexo em $file_path" >&2
    echo "Todo documento regulatorio exige anexo probatorio (sha256 server-side) no cadastro/revisao." >&2
    echo "Chame antes de criar a revisao:" >&2
    echo "  from src.domain.metrologia.licencas_acreditacoes.transicoes import validar_anexo" >&2
    echo "  validar_anexo(anexo_sha256=inp.anexo_sha256)  # AnexoObrigatorioError -> 422" >&2
    echo "Override: '# lic-anexo-obrigatorio: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
