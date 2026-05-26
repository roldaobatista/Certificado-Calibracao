#!/usr/bin/env bash
# =============================================================
# hmac-versao-formato-check.sh — Marco 4 P9 INV-HMAC-001 / ADR-0064
#
# Defende o formato canonico de hash HMAC persistido em entidades
# WORM metrologicas: v<NN>$<base64>.
#
# Por que existir:
#   ISO 17025 cl. 8.4 exige retencao 25a. Em 25 anos a chave HMAC
#   rotaciona pelo menos 25 vezes. Sem prefixo de versao na propria
#   string persistida, eh impossivel saber QUAL chave foi usada pra
#   gerar o hash — auditor CGCRE em 2050 nao consegue verificar.
#
#   ADR-0064 cravou formato `v<NN>$<base64>`:
#     v01$abc...   <- v01 = versao da chave KMS; $ = separador; base64.
#
#   INV-HMAC-001: hash persistido em entidade WORM (EventoDeCalibracao,
#   EventoDeOS, Leitura, MedicaoControle, PadraoUsado.padrao_id_hash,
#   QR cert, QR equipamento, ...) DEVE usar esse formato.
#
# Bloqueios em codigo Python (Write/Edit):
#
# 1. (LITERAL_INVALIDO) String LITERAL persistida via padroes de
#    atribuicao a campos `*_hash`, `evento_hash`, `descricao_hash`,
#    `relato_hash`, `replay_determinismo_hash`, etc — quando o LITERAL
#    nao bate `v<NN>$<base64>` ou nao usa helper.
#    Ex: `hash="abc123"` em Python -> BLOCK
#    Ex: `hash="v01$abc"` em Python -> OK
#
# 2. (HMAC_SEM_FORMATAR) `hmac.new(...).hexdigest()` ou `.digest()`
#    usado em codigo aplicacao FORA do helper unico
#    `src/domain/metrologia/calibracao/hash_versionado.py` (formatar_*)
#    e fora de `src/infrastructure/equipamentos/services_qr.py` (QR helper).
#    Indica geracao de hash sem prefixo de versao.
#
# 3. (SQL_HASH_FIELDS_SEM_FORMATO) UPDATE/INSERT SQL com strings
#    literais sem prefixo v<NN>$ em campos *_hash (defesa em profundidade
#    para data migrations que poderiam burlar o validador Python).
#
# Auto-allow (exit 0):
#   - tests/**                        (testam o helper)
#   - **/migrations/**                (data migrations one-off — exigem
#                                      review humano; nao escalam pra prod)
#   - docs/**                         (exemplos em docs)
#   - src/domain/metrologia/calibracao/hash_versionado.py
#   - src/infrastructure/equipamentos/services_qr.py
#   - src/infrastructure/crypto/**    (helpers centralizados)
#
# Override em arquivo fora da allowlist:
#   # hmac-versao: skip -- <razao com >=10 chars>
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/foo.py","content":"snapshot.evento_hash = \"abc123\""}}' | bash .claude/hooks/hmac-versao-formato-check.sh
#   echo $?  # 2
#
#   echo '{"tool_input":{"file_path":"src/foo.py","content":"snapshot.evento_hash = \"v01$abc=\""}}' | bash .claude/hooks/hmac-versao-formato-check.sh
#   echo $?  # 0
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

# Tipos cobertos: Python (.py) e SQL (.sql)
case "$norm_path" in
    *.py|*.sql) ;;
    *) exit 0 ;;
esac

# AUTO-ALLOW pelo caminho
auto_allow=0
case "$norm_path" in
    tests/*|*/tests/*|*/test_*|*_test.py) auto_allow=1 ;;
    */migrations/*) auto_allow=1 ;;
    docs/*|*/docs/*) auto_allow=1 ;;
    src/domain/metrologia/calibracao/hash_versionado.py|*src/domain/metrologia/calibracao/hash_versionado.py) auto_allow=1 ;;
    src/infrastructure/equipamentos/services_qr.py|*src/infrastructure/equipamentos/services_qr.py) auto_allow=1 ;;
    src/infrastructure/crypto/*|*/src/infrastructure/crypto/*) auto_allow=1 ;;
esac

# Override com justificativa
if printf '%s' "$content" | grep -qE '#[[:space:]]*hmac-versao:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

[ "$auto_allow" -eq 1 ] && exit 0

# =============================================================
# 1. LITERAL_INVALIDO: campos `*_hash` (incluindo evento_hash,
#    descricao_hash, relato_hash, replay_determinismo_hash, etc)
#    atribuidos a string literal SEM prefixo v<NN>$.
#
#    Padrao Python detectado:
#      <identificador_hash> = "<literal_sem_prefixo>"
#      ou
#      <identificador_hash>=<literal_sem_prefixo>
#
#    Aceita: "" (literal vazio — campo default opcional em snapshot)
#    Aceita: "v<NN>$..." (formato canonico)
#    Aceita: f"v{...}$..." (f-string com formato canonico)
#    Bloqueia: "abc123", "hash-fake", etc.
# =============================================================

# Lista de sufixos canonicos de campo hash (INV-HMAC-001 explicito)
# Casa qualquer identificador que TERMINE com _hash, _hash_versionado,
# ou seja literalmente evento_hash / descricao_hash / etc.
HASH_FIELD_RE='[a-zA-Z_][a-zA-Z0-9_]*_hash[a-zA-Z0-9_]*'

# Procura atribuicao com literal NAO-canonico
# Estrategia: extrai todas linhas que casam atribuicao a *_hash e
# inspeciona cada uma.
viol_lines=$(printf '%s' "$content" | grep -nE "${HASH_FIELD_RE}[[:space:]]*=[[:space:]]*[\"'][^\"']{1,}[\"']" || true)

if [ -n "$viol_lines" ]; then
    # Filtra apenas linhas que TEM literal nao-canonico
    bad=$(printf '%s\n' "$viol_lines" | while IFS= read -r line; do
        # Extrai o valor literal entre aspas (primeira ocorrencia apos =)
        val=$(printf '%s' "$line" | perl -ne '
            if (/_hash[a-zA-Z0-9_]*\s*=\s*(["\x27])([^"\x27]*)\1/) {
                print "$2\n";
            }
        ')
        # Linha vazia = sem captura (formato complexo, deixa passar)
        [ -z "$val" ] && continue
        # Literal vazio "" => OK (campo default antes de definir)
        [ -z "${val}" ] && continue
        # Formato canonico v<NN>$<base64> => OK
        # NN = 2 digitos (01..99); base64 alfabeto [A-Za-z0-9+/=]
        if printf '%s' "$val" | grep -qE '^v[0-9]{2}\$[A-Za-z0-9+/=]+$'; then
            continue
        fi
        printf '%s\n' "$line"
    done)
    if [ -n "$bad" ]; then
        echo "hmac-versao-formato-check (LITERAL_INVALIDO): hash literal sem formato canonico v<NN>\$<base64> em $file_path" >&2
        printf '%s\n' "$bad" | head -5 >&2
        echo "Use src.domain.metrologia.calibracao.hash_versionado.formatar_hash_versionado() ou helper equivalente." >&2
        echo "Formato canonico ADR-0064 + INV-HMAC-001: v01\$<base64>, v02\$<base64>, ..." >&2
        echo "Override: comentario # hmac-versao: skip -- <razao>=10 chars>" >&2
        exit 2
    fi
fi

# =============================================================
# 2. HMAC_SEM_FORMATAR: hmac.new(...).hexdigest() ou .digest() em codigo
#    aplicacao FORA do helper unico. Indica que alguem esta gerando hash
#    mas pode estar persistindo SEM o prefixo de versao.
#
#    .py apenas (SQL nao chama hmac.new diretamente).
# =============================================================
case "$norm_path" in
    *.py)
        if printf '%s' "$content" | grep -qE 'hmac\.new[[:space:]]*\([^)]*\)[[:space:]]*\.(hexdigest|digest)[[:space:]]*\(\)'; then
            # Bloqueia apenas quando o codigo nao parece passar resultado
            # por formatar_hash_versionado em seguida. Heuristica conservadora:
            # se o conteudo NAO contem "formatar_hash_versionado" no mesmo arquivo,
            # presumimos uso direto -> BLOCK.
            if ! printf '%s' "$content" | grep -q "formatar_hash_versionado"; then
                echo "hmac-versao-formato-check (HMAC_SEM_FORMATAR): hmac.new().hexdigest()/digest() em $file_path" >&2
                echo "sem chamada visivel a formatar_hash_versionado." >&2
                echo "Risco: hash persistido sem prefixo v<NN>\$ — quebra auditoria 25a (INV-HMAC-001 + ADR-0064)." >&2
                echo "Use formatar_hash_versionado(VERSAO_HMAC_ATUAL, digest) do helper unico." >&2
                exit 2
            fi
        fi
        ;;
esac

# =============================================================
# 3. SQL_HASH_FIELDS_SEM_FORMATO: UPDATE/INSERT SQL com literal sem
#    prefixo v<NN>$ em campos *_hash. Defesa em profundidade para data
#    migrations que poderiam burlar o validador Python.
#
#    Bloqueia em .sql; em .py (data migrations) o auto_allow ja
#    isenta (migrations/ pasta) — mas se alguem inlinear SQL em
#    services.py com .raw() / cursor.execute(), pega aqui.
# =============================================================
# Padrao: nome_*_hash = 'literal_sem_prefixo' OU nome_*_hash, ... VALUES (..., 'literal', ...)
# Simplificado: encontra linhas com *_hash e literal sem prefixo
sql_bad=$(printf '%s\n' "$content" | grep -nE "${HASH_FIELD_RE}[[:space:]]*=[[:space:]]*'[^']{1,}'" | while IFS= read -r line; do
    val=$(printf '%s' "$line" | perl -ne "
        if (/_hash[a-zA-Z0-9_]*\\s*=\\s*'([^']*)'/) {
            print \"\$1\\n\";
        }
    ")
    [ -z "$val" ] && continue
    if printf '%s' "$val" | grep -qE '^v[0-9]{2}\$[A-Za-z0-9+/=]+$'; then
        continue
    fi
    printf '%s\n' "$line"
done)
if [ -n "$sql_bad" ]; then
    echo "hmac-versao-formato-check (SQL_HASH_FIELDS_SEM_FORMATO): UPDATE/INSERT em $file_path com hash literal sem formato canonico" >&2
    printf '%s\n' "$sql_bad" | head -5 >&2
    echo "Formato canonico ADR-0064: v01\$<base64>. Data migration deve usar helper Python ou literal canonico." >&2
    exit 2
fi

exit 0
