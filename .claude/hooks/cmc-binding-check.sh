#!/usr/bin/env bash
# =============================================================
# cmc-binding-check.sh — Marco 4 P9 INV-CAL-CMC-001 / INV-002 / ADR cl. 6.4.10
#
# Defende a vinculacao CMC obrigatoria pra Calibracao acreditada RBC.
# Tenant RBC NAO pode configurar calibracao sem informar escopo_id
# (FK pro escopo de acreditacao que define grandeza+faixa cobertos
# pelo CMC declarado na CGCRE).
#
# Por que existir:
#   ISO 17025 cl. 6.4.10 + INV-CAL-CMC-001 — emitir certificado RBC
#   fora da Calibration & Measurement Capability declarada eh fraude
#   regulatoria. Risco direto: perda da acreditacao + multa CGCRE.
#
# Heuristica:
#   Em arquivos .py do src/, detectar construcoes que combinam:
#     A) tipo_acreditacao = TipoAcreditacao.RBC ou "RBC"
#     B) escopo_id = None
#   Quando A e B aparecem no MESMO conteudo (mesmo edit/write),
#   bloqueia. Indicio de payload/fixture/factory criando Calibracao
#   RBC sem CMC binding.
#
# Auto-allow (exit 0):
#   - tests/**, */tests/*, test_*, *_test.py
#   - **/migrations/**          (data migrations one-off)
#   - docs/**                   (exemplos)
#   - src/domain/metrologia/calibracao/value_objects.py
#     (regex+VO TipoAcreditacao vivem aqui)
#
# Override: comentario `# cmc-binding: skip -- <razao com >=10 chars>`
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/foo.py","content":"x = Calibracao(tipo_acreditacao=TipoAcreditacao.RBC, escopo_id=None)"}}' | bash .claude/hooks/cmc-binding-check.sh
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

# So .py
case "$norm_path" in
    *.py) ;;
    *) exit 0 ;;
esac

# AUTO-ALLOW pelo caminho
case "$norm_path" in
    tests/*|*/tests/*|*/test_*|*_test.py) exit 0 ;;
    */migrations/*) exit 0 ;;
    docs/*|*/docs/*) exit 0 ;;
    src/domain/metrologia/calibracao/value_objects.py|*src/domain/metrologia/calibracao/value_objects.py) exit 0 ;;
esac

# Override
if printf '%s' "$content" | grep -qE '#[[:space:]]*cmc-binding:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# =============================================================
# Detecta tipo_acreditacao=RBC + escopo_id=None no mesmo conteudo.
# Padroes A:
#   tipo_acreditacao=TipoAcreditacao.RBC
#   tipo_acreditacao="RBC"
#   tipo_acreditacao = "RBC"
#   "tipo_acreditacao": "RBC"
# Padroes B:
#   escopo_id=None
#   escopo_id = None
#   "escopo_id": None
# =============================================================

has_rbc=0
# Aceita: tipo_acreditacao=TipoAcreditacao.RBC | tipo_acreditacao="RBC"
#        | "tipo_acreditacao": "RBC" | 'tipo_acreditacao': 'RBC'
# Tolera aspas e dois-pontos JSON-like via opcionais.
if printf '%s' "$content" | grep -qE 'tipo_acreditacao["\x27]?[[:space:]]*[:=][[:space:]]*(TipoAcreditacao\.RBC|["\x27]RBC["\x27])'; then
    has_rbc=1
fi

has_escopo_none=0
if printf '%s' "$content" | grep -qE 'escopo_id["\x27]?[[:space:]]*[:=][[:space:]]*None'; then
    has_escopo_none=1
fi

if [ "$has_rbc" -eq 1 ] && [ "$has_escopo_none" -eq 1 ]; then
    echo "cmc-binding-check (RBC_SEM_ESCOPO): construcao com tipo_acreditacao=RBC + escopo_id=None em $file_path" >&2
    echo "Tenant RBC exige escopo_id NOT NULL (INV-CAL-CMC-001 + cl. 6.4.10)." >&2
    echo "Configurar calibracao RBC sem CMC vinculado = fraude regulatoria." >&2
    echo "Linhas relevantes:" >&2
    printf '%s\n' "$content" | grep -nE 'tipo_acreditacao["\x27]?[[:space:]]*[:=][[:space:]]*(TipoAcreditacao\.RBC|["\x27]RBC["\x27])|escopo_id["\x27]?[[:space:]]*[:=][[:space:]]*None' | head -10 >&2
    echo "Override: # cmc-binding: skip -- <razao com >=10 chars>" >&2
    exit 2
fi

exit 0
