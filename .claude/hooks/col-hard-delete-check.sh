#!/usr/bin/env bash
# =============================================================
# col-hard-delete-check.sh — colaboradores P7 / INV-COL-INATIVO (T-COL-052)
#
# Bloqueia views/repositories da frente `colaboradores` que realizem DELETE
# fisico de colaborador sem verificar a porta `ColaboradorReferenciadoPort`
# (stub conservador fail-safe — ADR-0066 / TL-COL-07).
#
# INV-COL-INATIVO: hard-delete fisico e bloqueado se ha OS/cert/comissao
# referenciando. O caminho legitimo e soft-delete (`deletado_em`).
# O trigger PG BEFORE DELETE (migration 0003) e a barreira definitiva, mas
# o hook protege a camada de codigo.
#
# Heuristica (so em views/repositories da frente colaboradores):
#   Atua em '*/colaboradores/*(views|repositories)*.py'.
#   BLOCK se o arquivo contiver `.delete()` em instancia de Colaborador OU
#   `ColaboradorModel.objects.filter(...)...delete()` SEM mencionar
#   `ColaboradorReferenciadoPort` ou `referenciado_port` ou
#   `hard_delete` em conjunto com uma verificacao.
#
# Excecao legitima (nao bloqueia):
#   - Linha contem override '# col-hard-delete: skip -- <razao >=10 chars>'.
#   - Arquivo de teste (tests/) — testes precisam testar o bloqueio.
#   - O proprio trigger PG (migration SQL) — nao e arquivo Python.
#   - `.delete()` em modelo filho (ColaboradorPapel, HabilidadeModel, etc.)
#     nao e delete de Colaborador — mas o hook e conservador: alerta se
#     qualquer `.delete()` existe no arquivo sem a porta declarada.
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/infrastructure/colaboradores/repositories.py","content":"class DjangoColaboradorRepository:\n    def remover(self, id):\n        ColaboradorModel.objects.filter(id=id).delete()\n"}}' | bash .claude/hooks/col-hard-delete-check.sh; echo $?  # 2
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

# Atua so em views/repositories da frente colaboradores (exceto testes).
case "$norm_path" in
    */tests/*) exit 0 ;;
    */colaboradores/views.py) ;;
    */colaboradores/repositories.py) ;;
    */colaboradores/*views*.py) ;;
    */colaboradores/*repositories*.py) ;;
    *) exit 0 ;;
esac

# Se nao tem chamada .delete(), nao ha risco de hard-delete.
if ! printf '%s' "$content" | grep -qE '\.delete\(\)'; then
    exit 0
fi

# Override global no arquivo
if printf '%s' "$content" | grep -qE '#[[:space:]]*col-hard-delete:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# Verifica se o arquivo menciona a porta de verificacao (presenca da porta
# significa que o delete esta guardado corretamente).
# Aceita: ColaboradorReferenciadoPort, referenciado_port, HardDeleteBloqueado
if printf '%s' "$content" | grep -qE 'ColaboradorReferenciadoPort|referenciado_port|HardDeleteBloqueado'; then
    exit 0
fi

# Arquivo tem .delete() mas nao menciona a porta de verificacao. BLOCK.
echo "col-hard-delete (INV-COL-INATIVO): $file_path contem .delete() sem referenciar" >&2
echo "  ColaboradorReferenciadoPort ou HardDeleteBloqueado." >&2
echo "" >&2
echo "Hard-delete fisico de colaborador exige verificar se ha OS/cert/comissao" >&2
echo "referenciando (INV-COL-INATIVO / TL-COL-07 / ADR-0066)." >&2
echo "O stub conservador ColaboradorReferenciadoPort bloqueia por default." >&2
echo "O trigger PG BEFORE DELETE (migration 0003) e a barreira definitiva." >&2
echo "Use soft-delete (deletado_em) para remover colaborador sem referencias." >&2
echo "Override (com justificativa >=10 chars):" >&2
echo "  # col-hard-delete: skip -- <razao com >=10 chars>" >&2
exit 2
