# Ideia

## Descrição
_Descreva aqui a ideia._

## Objetivo
_O que se pretende alcançar._

## Próximos passos
- [ ]
- [ ]
- [ ]

## Referências
-
coloque nele
Sim. Mas um app desses não pode ser só um gerador de PDF. Para emissão séria de certificado de calibração de balanças, ele precisa funcionar como sistema metrológico + sistema da qualidade + sistema documental. A base é a ABNT NBR ISO/IEC 17025, que trata de competência, imparcialidade e operação consistente de laboratórios; no Brasil, a acreditação da Cgcre/Inmetro para laboratórios de calibração é feita com base nessa norma.
O primeiro bloco é o cadastro técnico e regulatório do instrumento. O app precisa registrar, no mínimo: cliente, CNPJ/CPF, local de instalação, identificação do instrumento, fabricante, modelo, número de série, capacidade máxima, divisão, classe, uso pretendido e vínculo com aprovação de modelo quando aplicável. Isso é importante porque o controle metrológico legal de instrumentos de pesagem não automáticos no Brasil está ligado ao RTM atualmente associado à Portaria Inmetro nº 157/2022, aplicada às finalidades de uso sujeitas ao controle legal.
O segundo bloco é a rastreabilidade metrológica. O app tem que controlar os pesos padrão, massas auxiliares, termohigrômetro, barômetro e demais padrões/equipamentos usados na calibração, com número de identificação, certificado, laboratório emissor, data da calibração, vencimento interno de uso, incerteza declarada e cadeia de rastreabilidade. Sem isso, você não sustenta o resultado em auditoria. A Cgcre mantém política específica de rastreabilidade metrológica e o Inmetro destaca a importância de materiais e referências rastreáveis ao SI para garantir resultados confiáveis.
O terceiro bloco é o motor técnico da calibração. O app deve permitir procedimentos por tipo de balança e por método adotado pelo laboratório, com coleta estruturada dos pontos de ensaio, condições ambientais, identificação dos padrões utilizados e cálculo automático dos resultados. Para balanças/IPNA, isso normalmente precisa cobrir os ensaios e cálculos previstos no procedimento adotado pelo laboratório; guias amplamente usados para NAWI, como a EURAMET cg-18, tratam de práticas de medição, métodos, resultados, incerteza e conteúdo do certificado.
O quarto bloco é o cálculo metrológico defensável. Aqui o app precisa ter: cálculo de erro/indicação por ponto, histerese quando aplicável, repetibilidade, excentricidade se o seu procedimento exigir, correções, arredondamentos controlados, cálculo de incerteza de medição com orçamento configurável, fator de abrangência, e comparação com a CMC do escopo quando o laboratório for acreditado. O próprio Inmetro publica escopos RBC em que a CMC é definida como a menor incerteza que o laboratório consegue obter; esses escopos também observam que a incerteza declarada no certificado pode ser maior que a CMC por contribuições do instrumento ou padrão calibrado.
O quinto bloco é o controle de declaração de conformidade. Isso é crítico. Se o app permitir emitir “aprovado/reprovado”, ele precisa exigir a regra de decisão usada e preservar os resultados e a incerteza associada. A Cgcre já esclareceu que, em certificado de calibração com declaração de conformidade, não se pode omitir resultados e incerteza e ainda usar símbolo/referência à acreditação. Então o sistema precisa bloquear atalhos do tipo “conforme” sem base metrológica documentada.
O sexto bloco é a emissão correta do certificado. O certificado deve sair com numeração única, revisão/template controlado, identificação completa do cliente e do instrumento, local da calibração, datas relevantes, método/procedimento aplicado, resultados, incerteza, unidade de medida, identificação dos padrões usados, responsáveis técnicos, assinaturas/autorização de emissão, anexos quando necessário, QR code ou código de verificação e histórico de reemissão. E um detalhe importante: o Inmetro informa que não existe um “prazo de validade” fixo do certificado de calibração; a periodicidade é definida pelo proprietário dentro de seu programa de calibração. Então o app deve separar claramente data do certificado de próxima calibração recomendada.
O sétimo bloco é o sistema da qualidade embutido. Para ficar alinhado à lógica da ISO/IEC 17025, o app precisa ter controle de usuários e perfis, segregação de funções, aprovação por responsável autorizado, trilha de auditoria imutável, versionamento de procedimentos e modelos de certificado, bloqueio de padrões vencidos, bloqueio de técnico não qualificado para determinado escopo, registro de não conformidades, ações corretivas e evidências de revisão. A estrutura da ISO/IEC 17025 cobre requisitos gerais, estruturais, de recursos, de processo e de sistema de gestão; e a participação em ensaios de proficiência é tratada pelo Inmetro como indicação de competência do laboratório.
O oitavo bloco é o controle da acreditação e do uso de símbolo. Se o laboratório for RBC, o app precisa saber: em qual faixa/campo o serviço está dentro do escopo, se a calibração foi feita em instalação permanente ou nas instalações do cliente, qual CMC se aplica, e quando o símbolo/referência à acreditação pode ou não aparecer. A própria Cgcre mantém regras específicas para uso de símbolo e referências à acreditação, e ainda recomenda conferir a situação do escopo porque o certificado de acreditação pode ter validade indeterminada enquanto o escopo pode ser cancelado a qualquer tempo.
No Android, operacionalmente, eu colocaria ainda estes requisitos práticos: funcionamento offline-first em campo, sincronização posterior, captura de fotos e anexos, geolocalização opcional do atendimento, coleta de assinatura, exportação de dados brutos, PDF com proteção contra alteração indevida, backup, criptografia local e na transmissão, e logs completos de quem mediu, quem revisou e quem liberou. Isso não “substitui” a norma, mas é o tipo de controle de integridade e rastreabilidade que um laboratório precisa para demonstrar operação consistente e resultado válido.
Em resumo, o app ideal precisa ter 4 camadas ao mesmo tempo:
Metrológica: cálculos, incerteza, CMC, regra de decisão.
Regulatória: RTM/Portarias, escopo, símbolo, uso legal.
Qualidade: trilha de auditoria, competência, documentos, bloqueios.
Documental: certificado robusto, verificável, reemitível e rastreável.
E o ponto mais importante: nenhum app, sozinho, “garante ISO 17025”. Ele só sustenta a conformidade se o laboratório tiver procedimento válido, pessoal competente, padrões rastreáveis, cálculo de incerteza correto, gestão documental e, quando aplicável, escopo de acreditação compatível.
Perfeito. Abaixo está a estrutura que eu faria para esse app em nível de PRD funcional, já pensada para emissão de certificado de calibração de balanças com foco em ISO/IEC 17025, rastreabilidade metrológica, regra de decisão, relato de resultados e aderência ao ambiente regulatório do Inmetro/Cgcre. A ISO/IEC 17025 continua sendo a base de competência, imparcialidade e operação consistente de laboratórios, e o RTM consolidado para instrumentos de pesagem não automáticos segue ligado à Portaria Inmetro nº 157/2022.
Objetivo do aplicativo
O aplicativo não deve ser tratado como “app de PDF”, mas como plataforma metrológica móvel para:
executar calibrações em campo ou laboratório;
registrar evidências técnicas e rastreabilidade;
calcular resultados e incerteza;
aplicar regra de decisão quando cabível;
emitir certificado tecnicamente defensável;
manter trilha de auditoria completa;
sincronizar com backend/ERP/laboratório central.
Premissas normativas do produto
O app deve nascer com estas premissas:
Resultado bruto e incerteza não podem ser escondidos quando houver declaração de conformidade; a regra de decisão precisa ser documentada e, quando aplicável, acordada com o cliente.
Rastreabilidade metrológica dos padrões e instrumentos auxiliares precisa ser controlada. A ILAC mantém política específica para rastreabilidade metrológica e a Cgcre/Inmetro opera a acreditação no Brasil.
Certificado de calibração não deve virar agenda de vencimento. O próprio Inmetro informa que a periodicidade é definida pelo proprietário dentro do programa de calibração; além disso, a orientação de 7.8 aponta que recomendação de intervalo não deve constar no certificado/etiqueta, salvo condição específica.
Se o laboratório for acreditado, o sistema deve respeitar escopo, CMC e uso correto de referência à acreditação, e a verificação do escopo deve ser feita contra a base RBC/Cgcre.
Para balanças não automáticas, o app deve permitir configuração de procedimento técnico alinhado ao método do laboratório; guias como a EURAMET cg-18 são úteis como referência de boa prática, embora não sejam obrigatórios por si só.
Módulos obrigatórios
3.1. Módulo de autenticação, perfis e rastreabilidade humana
Função: controlar quem pode fazer o quê.
Perfis mínimos:
técnico executor;
revisor técnico;
signatário autorizado;
gestor da qualidade;
administrador;
auditor somente leitura;
cliente externo, se houver portal.
Recursos:
login forte;
autenticação offline com cache seguro;
assinatura eletrônica interna por credencial;
trilha: quem criou, alterou, revisou, aprovou, cancelou, reemitiu;
bloqueio por competência técnica.
Regra crítica:
técnico executa;
revisor não pode revisar o próprio serviço;
signatário só assina se requisitos estiverem íntegros.
3.2. Módulo de cadastro de clientes e locais
Campos:
razão social / nome;
CNPJ/CPF;
endereço;
contatos;
unidades/filiais;
local exato da balança;
responsável pelo acompanhamento;
condições especiais do local.
Também deve permitir:
histórico de serviços;
anexos contratuais;
regra comercial para emissão com ou sem referência RBC;
preferências documentais.
3.3. Módulo de instrumentos de pesagem
Cadastro técnico mínimo:
código interno;
tipo de instrumento;
fabricante;
modelo;
número de série;
capacidade máxima;
divisão/ resolução;
classe;
tara;
localização;
uso pretendido;
faixa efetiva de uso;
status regulatório;
fotos da placa e lacres;
aprovação de modelo, quando aplicável ao caso regulatório. A aderência ao RTM consolidado de IPNA é um ponto central do produto.
Subfunções:
histórico por instrumento;
histórico de reparos;
troca de célula/indicador;
lacres;
ocorrências;
vínculo com certificados anteriores.
3.4. Módulo de padrões e instrumentos auxiliares
Esse é um dos mais críticos.
Deve controlar:
pesos padrão;
jogo de massas;
carrinhos/apoios/acessórios;
termohigrômetro;
barômetro, quando aplicável;
inclinômetro ou acessórios específicos;
instrumentos auxiliares do procedimento.
Campos:
ID do padrão;
descrição;
fabricante/modelo;
faixa;
valor nominal;
incerteza;
certificado do padrão;
laboratório emissor;
data da calibração;
vencimento interno;
status: apto / restrito / vencido / bloqueado;
fatores de correção;
localização atual;
fotos;
anexos PDF.
Regras:
padrão vencido bloqueia uso;
padrão fora da faixa bloqueia ensaio;
padrão sem cadeia documental válida impede aprovação final.
3.5. Módulo de procedimentos e métodos
O app precisa ter um “motor de procedimento”.
Deve permitir cadastrar:
procedimento interno;
revisão;
data de vigência;
campo de aplicação;
tipo de balança;
sequência de ensaios;
critérios de aceitação;
fórmula de cálculo;
orçamento de incerteza aplicável;
regra de decisão;
modelo de certificado associado.
Também deve versionar:
método antigo;
método atual;
motivo da revisão;
aprovação da revisão.
3.6. Módulo de ordem de serviço metrológica
É o container operacional da calibração.
Status sugeridos:
aberta;
em deslocamento;
em execução;
aguardando evidência;
aguardando revisão;
aguardando assinatura;
concluída;
cancelada;
reemitida.
Campos:
cliente;
local;
instrumento;
técnico;
padrões previstos;
procedimento previsto;
data/hora de início/fim;
condições ambientais;
observações de campo;
fotos;
assinatura do acompanhante.
3.7. Módulo de execução da calibração
Telas orientadas por wizard.
Passos:
conferir instrumento;
registrar ambiente;
validar padrões disponíveis;
confirmar procedimento;
lançar pontos de carga;
registrar leituras;
registrar repetições;
registrar excentricidade, linearidade, histerese etc., conforme método;
registrar ocorrências;
fechar coleta.
O app deve funcionar offline e impedir “pular etapa crítica” sem justificativa.
3.8. Módulo de cálculos metrológicos
Esse módulo faz o trabalho pesado.
Deve calcular:
erro de indicação;
correções;
médias;
repetibilidade;
histerese;
excentricidade;
linearidade;
erro máximo observado;
incerteza expandida;
fator de abrangência;
contribuição dos padrões;
contribuição do ambiente;
contribuição da resolução;
contribuição do operador/método, quando aplicável;
comparação com limites internos;
comparação com especificação do cliente;
comparação com critério regulatório, quando aplicável.
Para laboratórios acreditados, a lógica de CMC e a declaração da incerteza precisam ser coerentes com a prática de acreditação; a Cgcre mantém orientação para expressão da incerteza e CMC, e a ILAC mantém políticas de rastreabilidade e incerteza para calibração.
3.9. Módulo de declaração de conformidade
Não pode ser um simples botão “aprovado”.
Deve exigir:
especificação/requisito de referência;
regra de decisão;
modo de aplicação;
guarda da banda de proteção, quando usada;
registro de quem definiu a regra;
indicação se a regra foi acordada com o cliente.
Saídas possíveis:
conforme;
não conforme;
sem declaração de conformidade;
resultado inconclusivo / não aplicável.
A necessidade de documentar a regra de decisão e não omitir resultados/incer­teza em certificados com declaração de conformidade é explicitamente tratada pela Cgcre e por guias da ILAC.
3.10. Módulo de certificado
Esse módulo deve gerar o certificado e o espelho de dados.
Campos mínimos do certificado:
número único;
revisão do certificado;
identificação do laboratório;
identificação do cliente;
identificação completa do instrumento;
local da calibração;
data da calibração;
data da emissão;
procedimento/método;
padrões principais utilizados;
condições ambientais relevantes;
resultados;
incerteza;
unidade;
regra de decisão, quando aplicável;
declaração de conformidade, quando aplicável;
observações/limitações;
signatário;
mecanismo de verificação.
Muito importante:
“próxima calibração” deve ficar fora do certificado por padrão, indo para plano interno do cliente ou documento administrativo, salvo política específica muito bem controlada. Isso reduz conflito com a orientação de relato de resultados.
3.11. Módulo de documentos e evidências
Armazena:
fotos;
vídeos curtos;
assinatura;
laudos anexos;
certificados dos padrões;
croquis;
prints de leituras;
comprovantes do local.
Recursos:
carimbo de data/hora;
hash do arquivo;
versão;
bloqueio de exclusão após conclusão.
3.12. Módulo da qualidade
Sem isso o app fica fraco para auditoria.
Itens:
não conformidades;
ações corretivas;
desvios de procedimento;
uso de padrão vencido tentado;
registros de treinamento/competência;
aprovação de modelos de certificado;
revisão de procedimento;
eventos auditáveis;
painel de pendências da qualidade.
3.13. Módulo de escopo e acreditação
Necessário se o laboratório for RBC ou quiser ficar pronto para isso.
Funções:
cadastro do escopo acreditado;
faixas acreditadas;
CMC por serviço/faixa;
checagem se o serviço executado está “dentro” ou “fora” do escopo;
definição de uso ou não de referência à acreditação no certificado;
vínculo com consulta do escopo RBC/Cgcre. A consulta pública de escopos de laboratórios acreditados existe e deve ser considerada como referência de validação externa.
3.14. Módulo de sincronização e integridade
Como é Android e campo, isso é obrigatório.
Recursos:
banco local criptografado;
fila de sincronização;
resolução de conflito;
envio diferido de anexos;
assinatura de payload;
logs de sincronização;
backup local e nuvem;
modo somente leitura quando houver inconsistência crítica.
3.15. Módulo de portal/verificação externa
Opcional, mas muito útil.
Funções:
QR code no certificado;
validação pública por código;
visualização do PDF emitido;
status: original / reemitido / cancelado / substituído.
3.16. Módulo de futuro digital
Eu deixaria uma camada preparada para DCC — Digital Calibration Certificate, porque o próprio planejamento estratégico do Inmetro 2024–2027 menciona a implementação do certificado digital de calibração. Hoje isso é visão de evolução e não justificativa para pular o PDF tradicional, mas vale preparar a arquitetura desde o início.
Telas principais do aplicativo Android
4.1. Tela inicial / dashboard
Mostra:
OS do dia;
calibrações pendentes;
certificados aguardando revisão;
padrões prestes a vencer;
alertas críticos;
sincronização pendente.
4.2. Tela de login e troca de perfil
login;
biometria opcional;
seleção de unidade/laboratório;
modo offline.
4.3. Tela “Minhas ordens de serviço”
lista;
filtro por cliente/data/status;
botão iniciar execução;
indicação offline/sincronizado.
4.4. Tela de abertura da calibração
cliente;
instrumento;
procedimento;
padrões previstos;
checklist pré-execução.
4.5. Tela de identificação do instrumento
dados cadastrais;
foto da placa;
foto do conjunto;
foto dos lacres;
observações.
4.6. Tela de condições ambientais
temperatura;
umidade;
pressão, se usada;
estabilidade;
instrumento auxiliar utilizado;
hora da leitura.
4.7. Tela de seleção e conferência de padrões
lista de padrões;
status;
validade;
certificado vinculado;
bloqueio automático se inválido.
4.8. Tela de lançamento dos ensaios
grade de pontos;
carga aplicada;
indicação;
erro;
repetição;
observações;
captura por digitação ou integração futura.
4.9. Tela de ensaios complementares
excentricidade;
repetibilidade;
linearidade;
histerese;
retorno ao zero;
outras rotinas conforme procedimento.
4.10. Tela de cálculo preliminar
resumo técnico;
erros;
incerteza provisória;
pendências;
inconsistências detectadas.
4.11. Tela de ocorrências e desvios
irregularidade no instrumento;
lacre rompido;
interferência mecânica;
instabilidade elétrica;
impossibilidade de concluir;
recomendação interna.
4.12. Tela de evidências
fotos;
anexos;
assinatura do acompanhante;
áudio de observação opcional.
4.13. Tela de revisão técnica
conferência dos dados;
divergências;
aceite ou devolução para correção;
comentário obrigatório quando rejeitar.
4.14. Tela de assinatura/autorização
signatário;
resumo final;
assinatura eletrônica;
emissão do certificado.
4.15. Tela do certificado
pré-visualização;
compartilhar PDF;
gerar QR;
histórico de revisões;
status do documento.
4.16. Tela de padrões
cadastro;
validade;
uso recente;
bloqueios;
certificados anexos.
4.17. Tela de procedimentos
lista de procedimentos;
revisão atual;
comparar revisões;
aprovar nova revisão.
4.18. Tela de escopo/CMC
faixas;
serviços;
CMC;
status dentro/fora do escopo.
4.19. Tela de auditoria
logs;
quem alterou o quê;
trilha completa por OS ou certificado.
4.20. Tela de sincronização
pendências;
erros;
reenvio;
conflito de dados.
Fluxo operacional ideal
Fluxo A — calibração comum
abrir OS;
identificar balança;
registrar ambiente;
selecionar padrões;
executar ensaios;
calcular;
revisar;
assinar;
emitir certificado;
sincronizar.
Fluxo B — instrumento com problema
abrir OS;
identificar falha impeditiva;
registrar evidências;
emitir relatório de não execução ou execução parcial;
bloquear certificado de calibração final.
Fluxo C — declaração de conformidade
executar ensaio;
calcular resultado e incerteza;
selecionar especificação;
aplicar regra de decisão;
gerar certificado com resultado + incerteza + declaração.
Fluxo D — serviço fora do escopo acreditado
executar normalmente;
sistema detecta “fora do escopo”;
bloqueia símbolo/referência RBC;
emite certificado sem menção indevida à acreditação.
Regras de bloqueio que o sistema precisa ter
Essas regras fazem muita diferença.
O sistema deve impedir emissão quando houver:
padrão vencido;
padrão sem certificado anexado;
procedimento sem revisão aprovada;
instrumento sem identificação mínima;
ensaio obrigatório faltando;
incerteza não calculada;
regra de decisão ausente quando houver conformidade;
revisor igual ao executor, se a política impedir;
signatário sem autorização;
serviço marcado como acreditado fora do escopo/CMC;
certificado com campos obrigatórios vazios.
Campos mínimos do banco de dados
Entidades mínimas:
usuários;
perfis;
competências;
clientes;
locais;
instrumentos;
componentes do instrumento;
padrões;
certificados de padrões;
procedimentos;
revisões de procedimento;
ordens de serviço;
ensaios;
leituras;
cálculos;
incertezas;
regras de decisão;
certificados emitidos;
anexos;
logs;
não conformidades;
ações corretivas;
escopo acreditado;
CMC;
sincronizações.
Integrações que valem a pena
Para fase seguinte, eu preveria:
backend web administrativo;
ERP/financeiro;
portal do cliente;
consulta de escopo acreditado;
assinatura digital externa;
armazenamento em nuvem;
exportação CSV/Excel;
API para certificado verificável;
futuro suporte a DCC. O movimento do Inmetro para certificado digital sugere que deixar isso preparado é uma decisão boa de arquitetura.
O que entra no MVP e o que fica para fase 2
MVP sério
Tem que ter:
login e perfis;
clientes;
instrumentos;
padrões;
procedimentos;
OS;
execução de ensaios;
cálculos;
incerteza;
revisão;
assinatura;
certificado PDF;
QR de verificação;
logs;
sincronização offline.
Fase 2
módulo completo da qualidade;
escopo/CMC avançado;
portal do cliente;
assinatura ICP;
DCC;
integrações automáticas;
analytics e dashboards gerenciais.
Minha recomendação direta
Se você quiser fazer isso profissionalmente, eu dividiria o app em 3 camadas de produto:
Camada 1 — campo
Execução, coleta, evidência, offline, assinatura.
Camada 2 — metrologia
Procedimentos, cálculo, incerteza, regra de decisão, escopo.
Camada 3 — qualidade e certificado
Revisão, emissão, auditoria, controle documental, verificação externa.
Essa separação reduz erro, facilita auditoria e deixa o sistema evolutivo.
Ponto de atenção crítico
O maior erro em software desse tipo é este:
misturar “serviço executado” com “certificado emitido” e misturar “resultado metrológico” com “decisão comercial”.
O app precisa preservar a lógica técnica:
primeiro mede;
depois calcula;
depois avalia;
depois decide;
depois emite.
Não pode inverter.
Se você quiser, no próximo passo eu monto isso como um PRD completo, com:
nome de cada módulo,
histórias de usuário,
regras de negócio,
campos de cada tela,
permissões,
fluxos de exceção,
e backlog MVP/Fase 2.
acrescente 
Perfeito. Abaixo está a continuação em formato de PRD funcional condensado, já estruturado para virar backlog, especificação de telas e regra de negócio. A base normativa do produto é: ISO/IEC 17025:2017 para competência, imparcialidade e operação consistente de laboratório; Portaria Inmetro nº 157/2022 para o RTM de instrumentos de pesagem não automáticos; orientações e comunicados da Cgcre/Inmetro para incerteza, relato de resultados, declaração de conformidade, controle de dados e consulta de escopo acreditado. 

PRD — App Android de Calibração de Balanças

1. Visão do produto

Aplicativo Android para execução de calibração de balanças em campo e em laboratório, com operação offline, rastreabilidade metrológica, cálculo técnico, trilha de auditoria e emissão de certificado. O sistema deve apoiar conformidade com a ISO/IEC 17025 e com os requisitos regulatórios e orientativos do ecossistema Inmetro/Cgcre, mas não “garante” conformidade sozinho, porque a conformidade também depende de competência de pessoal, procedimentos válidos, padrões rastreáveis e sistema de gestão efetivo. 

2. Objetivo de negócio

Reduzir erro operacional, eliminar emissão manual frágil, padronizar a execução das calibrações, preservar evidências para auditoria e gerar certificados tecnicamente defensáveis. O produto também deve impedir práticas incompatíveis com o relato metrológico, como omitir resultados e incerteza quando houver declaração de conformidade, e deve respeitar o fato de que o Inmetro não fixa “validade padrão” para certificados de calibração; a periodicidade é definida pelo proprietário dentro do seu programa de calibração. 

3. Escopo do MVP

O MVP deve cobrir o ciclo completo:

1. cadastro do cliente, local e instrumento;


2. cadastro e controle de padrões;


3. abertura da ordem de serviço;


4. execução guiada do procedimento;


5. cálculo de resultados e incerteza;


6. revisão técnica;


7. assinatura/autorização;


8. emissão do certificado;


9. verificação por QR/code;


10. trilha de auditoria e sincronização.



O MVP já precisa nascer com controle de dados e gestão da informação, porque a ISO/IEC 17025 trata explicitamente do controle de dados e da gestão da informação no requisito 7.11. 

4. Perfis de usuário

Perfis mínimos do sistema:

Técnico executor: realiza a calibração e registra evidências.

Revisor técnico: confere coerência técnica, cálculos e completude.

Signatário autorizado: aprova a emissão do certificado.

Gestor da qualidade: administra procedimentos, não conformidades e auditoria.

Administrador: gerencia usuários, perfis, integrações e parâmetros.

Auditor somente leitura: consulta trilhas, certificados, revisões e evidências.

Cliente/portal: consulta certificados e autenticidade.


A segregação de papéis é coerente com a lógica da ISO/IEC 17025 sobre imparcialidade, competência e sistema de gestão. 

5. Requisitos funcionais por módulo

5.1. Autenticação e autorização

O sistema deve ter login seguro, perfis por função, trilha de sessão, assinatura eletrônica interna por credencial e bloqueio por competência. O técnico não deve conseguir aprovar o próprio certificado quando a regra de segregação estiver ativa. Toda ação crítica deve registrar usuário, data, hora, dispositivo e alteração realizada. Isso se conecta diretamente aos requisitos de controle de dados e gestão da informação. 

5.2. Cadastro de clientes e locais

Campos obrigatórios:

razão social/nome;

CNPJ/CPF;

contatos;

unidade/filial;

endereço completo;

coordenadas opcionais;

responsável local;

condições especiais de acesso e operação.


O sistema deve manter histórico de atendimentos por local e por instrumento.

5.3. Cadastro do instrumento de pesagem

Campos obrigatórios:

código interno;

fabricante;

modelo;

número de série;

capacidade máxima;

menor divisão/resolução;

classe;

uso pretendido;

localização;

identificação de aprovação de modelo, quando aplicável;

fotos da placa, da instalação e dos lacres.


O produto deve suportar o contexto regulatório do RTM de IPNA consolidado pela Portaria 157/2022 e permitir distinguir serviços meramente de calibração de situações submetidas ao controle metrológico legal. 

5.4. Cadastro e controle de padrões

O sistema deve controlar:

pesos padrão;

massas auxiliares;

termohigrômetro;

barômetro, quando aplicável;

outros instrumentos auxiliares usados no método.


Cada padrão precisa ter:

identificação única;

valor nominal;

faixa;

incerteza;

certificado vinculado;

laboratório emissor;

data da calibração;

vencimento interno;

fatores de correção;

status de uso.


O sistema deve bloquear uso de padrão vencido, sem certificado ou fora da faixa definida. A rastreabilidade metrológica e o uso de resultados confiáveis são centrais na ISO/IEC 17025 e nas orientações da Cgcre. 

5.5. Procedimentos e métodos

O produto deve ter cadastro versionado de procedimentos internos, com:

código;

revisão;

data de vigência;

escopo de aplicação;

tipo de instrumento;

sequência de ensaios;

fórmula de cálculo;

orçamento de incerteza;

regra de decisão aplicável;

modelo de certificado associado.


O sistema deve impedir execução com procedimento obsoleto ou não aprovado. A ISO/IEC 17025 cobre métodos, validação/verificação, relato de resultados e sistema de gestão; o app precisa refletir isso em software. 

5.6. Ordem de serviço metrológica

A OS deve conter:

cliente;

local;

instrumento;

técnico;

procedimento;

padrões previstos;

data/hora;

checklist pré-execução;

condições ambientais;

anexos e observações.


Status mínimos:

aberta;

em execução;

pendente de evidência;

pendente de revisão;

pendente de assinatura;

concluída;

cancelada;

reemitida.


5.7. Execução guiada da calibração

A execução deve ser em wizard:

1. identificação do instrumento;


2. registro ambiental;


3. conferência de padrões;


4. lançamento dos pontos;


5. repetições;


6. ensaios complementares;


7. ocorrências;


8. fechamento da coleta.



O sistema deve operar offline e registrar carimbo de tempo. Quando o método exigir ajuste, ele deve permitir guardar os resultados antes e depois do ajuste, porque a orientação da Cgcre para calibração contempla esse tipo de relato. 

5.8. Cálculos metrológicos

O motor de cálculo deve suportar:

erro de indicação;

correção;

repetibilidade;

histerese;

excentricidade;

linearidade;

erro máximo;

incerteza padrão e expandida;

fator de abrangência;

orçamento por contribuições;

arredondamento parametrizado.


O resultado da medição no certificado deve incluir a estimativa do mensurando, a incerteza expandida e o fator de abrangência, conforme a orientação da Cgcre sobre expressão da incerteza em certificados de calibração. 

5.9. Declaração de conformidade

O sistema não pode ter um botão simples de “aprovado/reprovado”. Ele deve exigir:

especificação de referência;

regra de decisão;

tipo de comparação;

banda de proteção, quando usada;

registro de quem definiu a regra;

indicação se houve acordo prévio com o cliente.


Também deve impedir emissão de certificado com declaração de conformidade omitindo resultado e incerteza, porque a Cgcre expressamente não permite isso. 

5.10. Emissão do certificado

O certificado deve conter, no mínimo:

número único;

revisão;

identificação do laboratório;

identificação do cliente;

identificação do instrumento;

local da calibração;

datas da calibração e emissão;

procedimento utilizado;

resultados;

incerteza;

fator k;

unidade;

condições ambientais relevantes;

padrões principais utilizados;

observações e limitações;

regra de decisão, quando houver;

responsável técnico/signatário;

QR code/código de verificação.


O sistema deve separar data de emissão de qualquer recomendação interna de próxima calibração, porque o Inmetro informa que a periodicidade é definida pelo proprietário, e o relato técnico do certificado não deve ser confundido com agenda administrativa. 

5.11. Evidências e anexos

O sistema deve aceitar:

fotos;

PDFs;

assinatura do acompanhante;

observações de campo;

documentos de suporte;

certificados dos padrões.


Cada arquivo deve guardar hash, autoria, data/hora e vínculo com OS, instrumento e certificado, para sustentar integridade e auditoria. Isso se alinha ao requisito de controle de dados e gestão da informação. 

5.12. Qualidade e trabalho não conforme

O sistema deve registrar:

desvio de procedimento;

tentativa de uso de padrão vencido;

erro de cadastro que impacte resultado;

necessidade de retrabalho;

não conformidade;

ação corretiva;

decisão sobre validade ou cancelamento de resultado.


A ISO/IEC 17025 e as orientações da Cgcre tratam explicitamente de trabalho não conforme e ação corretiva; por isso esse módulo não é opcional se o produto quiser ser realmente auditável. 

5.13. Escopo acreditado e CMC

Se o laboratório for acreditado ou quiser ficar pronto para isso, o sistema deve controlar:

serviço/faixa;

unidade;

CMC;

local de execução;

status dentro/fora do escopo;

regra de uso de símbolo/referência à acreditação.


Também deve permitir conferência contra a consulta pública da RBC, porque o Inmetro mantém sistema público de consulta de escopos dos laboratórios de calibração acreditados segundo a ABNT NBR ISO/IEC 17025:2017. 

5.14. Garantia da validade dos resultados

O sistema deve ter recursos para controles intermediários, verificações internas, cartas/indicadores de estabilidade e registros de checagens dos equipamentos e padrões. A Cgcre também trata de checagens intermediárias para manter confiança no desempenho de equipamentos, inclusive balanças, e de participação em atividades de ensaio de proficiência como parte do contexto de validade dos resultados. 

6. Regras críticas de bloqueio

O sistema deve bloquear emissão quando houver:

padrão vencido;

padrão sem certificado;

instrumento sem identificação mínima;

procedimento sem revisão aprovada;

ensaio obrigatório faltando;

cálculo de incerteza ausente;

regra de decisão ausente em caso de conformidade;

certificado sem resultado completo;

revisor igual ao executor, quando segregação for mandatória;

serviço marcado como acreditado fora do escopo/CMC.


Esses bloqueios são coerentes com os requisitos de competência, validade dos resultados, relato correto e controle de dados previstos na ISO/IEC 17025 e nos documentos orientativos da Cgcre. 

7. Requisitos não funcionais

O app deve ter:

funcionamento offline-first;

banco local criptografado;

sincronização assíncrona com fila;

controle de conflito;

trilha de auditoria imutável;

exportação de dados brutos;

PDF verificável;

desempenho aceitável em campo sem internet;

permissões e dados segregados por empresa/unidade;

backup e recuperação.


Como a ISO/IEC 17025 traz requisito específico de controle de dados e gestão da informação, esses itens não são apenas conveniência técnica; eles afetam diretamente a defensabilidade do sistema. 

8. Modelo mínimo de dados

Entidades mínimas:

usuário;

perfil;

competência;

cliente;

local;

instrumento;

componente do instrumento;

padrão;

certificado de padrão;

procedimento;

revisão de procedimento;

ordem de serviço;

leitura;

ensaio;

cálculo;

orçamento de incerteza;

regra de decisão;

certificado emitido;

anexo;

log de auditoria;

não conformidade;

ação corretiva;

escopo;

CMC;

sincronização.


9. Backlog por fase

Fase 1 — MVP operacional

login e perfis;

cadastro básico;

controle de padrões;

OS;

execução guiada;

cálculo;

incerteza;

revisão;

assinatura;

certificado;

QR/verificação;

logs;

sincronização.


Fase 2 — laboratório maduro

módulo completo da qualidade;

escopo e CMC avançados;

regras de conformidade sofisticadas;

painel gerencial;

portal do cliente;

reemissão controlada;

auditoria avançada.


Fase 3 — ecossistema

integração ERP/financeiro;

integração com portal;

API externa;

importação em massa;

relatórios estatísticos;

preparação para certificado digital estruturado.


10. Critérios de aceite do MVP

O MVP só deve ser considerado pronto quando:

1. uma calibração puder ser executada do início ao certificado pelo celular;


2. o sistema bloquear padrões vencidos;


3. o certificado sair com resultado, incerteza e fator k;


4. a revisão e a assinatura ficarem registradas;


5. o QR/code validar a autenticidade do certificado;


6. a operação funcionar offline e sincronizar depois;


7. o log mostrar quem alterou o quê;


8. a emissão com declaração de conformidade exigir regra de decisão;


9. o sistema distinguir serviço acreditado de serviço fora do escopo;


10. o certificado não depender de edição manual externa.



11. Decisões de produto que eu recomendo

Eu tomaria estas decisões desde o começo:

Android como app de campo, mas com backend web obrigatório;

cálculo no backend e no app, com reconciliação;

PDFs gerados de forma padronizada no servidor;

modelo de permissões por função e por competência;

configuração de procedimento por revisão, não por código fixo;

todo evento relevante gerando trilha de auditoria;

certificado como saída do sistema, nunca documento editável manualmente.


12. Risco principal do projeto

O maior risco não é técnico; é conceitual: tentar transformar o app em “emissor rápido de certificado” e não em “sistema metrológico com controle de qualidade e dados”. Se isso acontecer, o produto até gera PDF, mas falha em auditoria, falha em revisão técnica e falha quando houver questionamento de resultado, incerteza, rastreabilidade ou conformidade. Esse risco é exatamente o tipo de problema que a ISO/IEC 17025 e os documentos da Cgcre tentam evitar. 

No próximo passo, eu monto isso como PRD completo em estrutura profissional, com:

histórias de usuário,

fluxos detalhados,

regras de negócio numeradas,

campos de cada tela,

e backlog técnico para frontend, backend e banco.


Perfeito. Abaixo está a versão já pronta para virar especificação de produto e backlog técnico.

A base regulatória do app deve ser tratada assim: a ISO/IEC 17025:2017 é a norma-base para competência, imparcialidade e operação consistente de laboratórios, e a própria ISO informa que essa edição segue vigente. No Brasil, o ecossistema Inmetro/Cgcre complementa isso com orientações sobre rastreabilidade, relato de resultados, trabalho não conforme, controle de dados e consulta de escopo acreditado; para instrumentos de pesagem não automáticos, a referência regulatória central é a Portaria Inmetro nº 157/2022. 

Há quatro premissas que o sistema deve impor desde o início: o certificado não deve ser tratado como “documento com validade automática”, porque o Inmetro informa que a periodicidade é definida pelo proprietário dentro do programa de calibração; declaração de conformidade exige regra de decisão; certificado com declaração de conformidade não deve omitir resultados e incerteza; e, para laboratório acreditado, a incerteza declarada no certificado não pode ser menor que a CMC do escopo aplicável. 

1. Arquitetura de produto

1.1 Componentes

O produto deve ter 3 blocos:

A. App Android de campo

execução da calibração

coleta de evidências

operação offline

assinatura local

sincronização posterior


B. Backend técnico

autenticação

regras de negócio

cálculo consolidado

revisão técnica

emissão do certificado

controle de auditoria

APIs


C. Portal web

consulta de certificados

QR code / código verificável

gestão administrativa

procedimentos

padrões

escopo/CMC

qualidade e auditoria


1.2 Estratégia de dados

banco local no Android criptografado

fila de sync

backend como fonte oficial

anexos armazenados com hash

trilha de auditoria imutável


1.3 Estratégia normativa

O sistema deve refletir explicitamente os temas de controle de dados e gestão da informação, registros técnicos, relato de resultados e trabalho não conforme, porque esses temas aparecem diretamente na estrutura de implementação da ISO/IEC 17025 usada pela Cgcre/Inmetro. 


---

2. Regras de negócio numeradas

RB-01 — emissão bloqueada sem rastreabilidade

Nenhum certificado pode ser emitido se qualquer padrão utilizado estiver vencido, sem certificado associado, sem identificação única ou fora da faixa aplicável.

RB-02 — emissão bloqueada sem dados técnicos mínimos

A OS não pode avançar para revisão sem:

identificação completa do instrumento

procedimento selecionado

técnico executor

data/hora

local

condições ambientais mínimas

resultados de ensaio exigidos


RB-03 — procedimento obrigatório e versionado

Toda calibração deve estar vinculada a um procedimento com:

código

revisão

vigência

aprovador

método de cálculo

orçamento de incerteza aplicável


RB-04 — revisão segregada

O revisor técnico não pode ser o mesmo usuário que executou a calibração, salvo política formal e exceção registrada pelo gestor.

RB-05 — assinatura segregada

O signatário autorizado não pode emitir certificado se:

houver pendência técnica

houver não conformidade aberta sem disposição

faltar evidência obrigatória

o serviço estiver marcado como acreditado fora do escopo


RB-06 — regra de decisão obrigatória

Se o certificado trouxer “conforme”, “não conforme”, “aprovado” ou “reprovado”, o sistema deve exigir:

especificação de referência

regra de decisão

forma de tratamento da incerteza

autor da regra

data de aplicação


Essa exigência decorre do comunicado da Cgcre sobre declaração de conformidade em certificados de calibração. 

RB-07 — resultado e incerteza obrigatórios

Não é permitido emitir certificado com declaração de conformidade omitindo resultado e incerteza. 

RB-08 — CMC respeitada

Quando o serviço estiver dentro de escopo acreditado, a incerteza declarada não pode ser menor que a CMC aplicável. 

RB-09 — serviço fora do escopo

Quando o sistema identificar que o serviço está fora do escopo acreditado:

bloquear uso de símbolo/referência RBC

registrar motivo

emitir documento sem menção indevida à acreditação


RB-10 — certificado sem “validade automática”

O campo “próxima calibração” não deve compor o núcleo técnico do certificado por padrão. Essa informação deve ficar em plano de calibração/gestão do cliente, porque a periodicidade é definida pelo proprietário. 

RB-11 — retenção de registros técnicos

Toda calibração deve manter dados brutos, cálculos, revisão, certificado emitido e anexos vinculados, para rastreabilidade técnica. 

RB-12 — trabalho não conforme

Se houver desvio crítico, o sistema deve abrir fluxo de “trabalho não conforme”, bloquear emissão final até disposição formal e manter histórico do caso. 

RB-13 — controle de alteração

Toda alteração em leitura, cálculo, procedimento, status da OS ou certificado deve gerar log com:

usuário

data/hora

valor anterior

valor novo

motivo


RB-14 — hash documental

Todo PDF e anexo crítico deve ter hash armazenado para validação de integridade.

RB-15 — QR code verificável

Todo certificado deve ter QR code ou código de verificação que consulte o backend oficial.

RB-16 — offline com reconciliação

O app pode operar offline, mas o certificado final só adquire status “oficial” após sincronização e validação do backend.

RB-17 — competência por usuário

Somente usuários habilitados para determinado tipo de serviço/faixa podem executar ou revisar aquela calibração.

RB-18 — checagens intermediárias

O sistema deve registrar checagens internas e intermediárias dos padrões/equipamentos relevantes, como parte da confiança contínua nos resultados. 

RB-19 — métodos no escopo

Quando aplicável ao ambiente acreditado, o sistema deve permitir associar método ao serviço/faixa do escopo, porque a estrutura de escopo da Cgcre passou a incluir informação de método. 

RB-20 — preparação para DCC

A arquitetura deve nascer preparada para certificado digital estruturado, porque o Plano Estratégico do Inmetro 2024–2027 inclui a iniciativa de implementar o Certificado de Calibração Digital (DCC). 


---

3. Telas do app e campos obrigatórios

3.1 Tela: Login

Campos:

e-mail/login

senha

biometria opcional

empresa/unidade

modo offline


Validações:

bloquear usuário inativo

registrar dispositivo

exigir reautenticação para assinatura


3.2 Tela: Dashboard

Blocos:

OS do dia

padrões vencendo

pendências de sync

certificados aguardando revisão

não conformidades abertas


3.3 Tela: Cliente

Campos:

razão social

nome fantasia

CNPJ/CPF

IE opcional

telefone

e-mail

endereço

cidade/UF

responsável local

observações operacionais


3.4 Tela: Local de instalação

Campos:

nome do local

endereço específico

coordenadas GPS

ponto de referência

ambiente interno/externo

observações de acesso


3.5 Tela: Instrumento

Campos:

código interno

fabricante

modelo

número de série

capacidade máxima

divisão

classe

tipo

uso pretendido

aprovação de modelo, se aplicável

fotos da placa

fotos dos lacres

status operacional


3.6 Tela: Padrão

Campos:

ID do padrão

tipo

valor nominal/faixa

unidade

incerteza

certificado vinculado

laboratório emissor

data da calibração

vencimento interno

correção

localização

status


Validações:

vencido = bloqueado

sem certificado = bloqueado

fora da faixa = alerta ou bloqueio


3.7 Tela: Procedimento

Campos:

código

título

revisão

vigência

faixa de aplicação

tipo de instrumento

ensaios obrigatórios

modelo de cálculo

regra de decisão padrão

template de certificado


3.8 Tela: Ordem de serviço

Campos:

número da OS

cliente

local

instrumento

técnico

data/hora

procedimento

padrões previstos

checklist inicial

observações


3.9 Tela: Condições ambientais

Campos:

temperatura

umidade

pressão, se aplicável

instrumento auxiliar usado

hora da medição

estabilidade ambiental

observações


3.10 Tela: Lançamento dos ensaios

Campos:

ponto de carga

carga aplicada

indicação

erro calculado

repetição

observação

foto opcional


3.11 Tela: Ensaios complementares

Subseções:

repetibilidade

excentricidade

linearidade

histerese

retorno ao zero

outros do método


3.12 Tela: Evidências

Campos:

fotos

assinatura do acompanhante

vídeo curto opcional

observação de campo

anexos PDF


3.13 Tela: Resultado preliminar

Campos:

resumo dos erros

incerteza expandida

fator k

status técnico preliminar

pendências

desvios identificados


3.14 Tela: Regra de decisão

Campos:

especificação de referência

regra de decisão

considerar incerteza: sim/não

banda de proteção

observações

aprovador da regra


3.15 Tela: Revisão técnica

Campos:

checklist técnico

parecer

itens rejeitados

comentário obrigatório em reprovação

decisão: aprovar / devolver


3.16 Tela: Assinatura e emissão

Campos:

signatário

credencial

resumo final

opção emitir

opção reter

opção cancelar


3.17 Tela: Certificado

Campos exibidos:

número

revisão

cliente

instrumento

resultados

incerteza

fator k

regra de decisão, se houver

observações

QR code

histórico de reemissão



---

4. Fluxos detalhados

4.1 Fluxo principal

1. abrir OS


2. validar cliente/local/instrumento


3. selecionar procedimento


4. validar padrões aptos


5. registrar ambiente


6. executar ensaios


7. calcular resultados


8. registrar evidências


9. fechar execução


10. revisão técnica


11. assinatura


12. emissão do certificado


13. sincronização


14. publicação do QR/code



4.2 Fluxo com impeditivo

1. abrir OS


2. identificar impeditivo


3. registrar fotos/ocorrência


4. marcar trabalho não conforme


5. bloquear emissão


6. emitir apenas relatório de impossibilidade ou atendimento parcial



4.3 Fluxo com ajuste

1. coletar dados iniciais


2. registrar ajuste


3. coletar dados pós-ajuste


4. manter ambos os conjuntos de dados


5. deixar o tipo de relatório configurável conforme política do laboratório



4.4 Fluxo acreditado

1. selecionar serviço/faixa


2. validar escopo


3. validar CMC


4. validar método


5. permitir referência à acreditação só quando estiver tudo consistente




---

5. Histórias de usuário

HU-01
Como técnico, quero executar a calibração offline para continuar trabalhando mesmo sem internet.

HU-02
Como técnico, quero que o app me impeça de usar padrão vencido para reduzir erro de campo.

HU-03
Como revisor, quero ver dados brutos, cálculos e evidências para aprovar apenas serviços consistentes.

HU-04
Como signatário, quero bloquear emissão quando faltar incerteza, evidência ou revisão.

HU-05
Como gestor da qualidade, quero rastrear desvios e trabalhos não conformes para sustentar auditoria.

HU-06
Como administrador, quero versionar procedimentos sem perder histórico.

HU-07
Como cliente, quero validar o certificado por QR code para confirmar autenticidade.

HU-08
Como laboratório acreditado, quero controlar escopo e CMC para evitar referência indevida à RBC.


---

6. Backlog técnico — MVP

6.1 Frontend Android

autenticação

armazenamento local criptografado

lista de OS

formulários de cliente/local/instrumento

cadastro e seleção de padrões

wizard de execução

captura de foto e assinatura

cálculo preliminar local

fila de sincronização

visualização do certificado

estado offline/online

logs locais básicos


6.2 Backend/API

auth + RBAC

API de clientes

API de instrumentos

API de padrões

API de procedimentos/versionamento

API de OS

engine de cálculo

engine de regra de decisão

engine de escopo/CMC

emissão PDF

QR/code verification

auditoria/logs

fila de anexos

workflow de revisão e assinatura


6.3 Banco de dados

Tabelas mínimas:

users

roles

user_competencies

customers

customer_sites

instruments

instrument_photos

standards

standard_certificates

procedures

procedure_revisions

work_orders

work_order_environment

work_order_tests

work_order_evidence

calculations

decision_rules

reviews

approvals

certificates

certificate_revisions

audit_logs

nonconforming_work

scope_items

cmc_items

sync_events


6.4 Infraestrutura

storage de anexos

geração de PDF

QR verification endpoint

job queue

observabilidade

backup

criptografia em repouso

retenção de logs



---

7. Backlog técnico — fase 2

portal do cliente

dashboard gerencial

relatórios de produtividade

módulo de ações corretivas

módulo de treinamento/competência

gestão completa de escopo acreditado

indicadores de estabilidade/checagens intermediárias

integração ERP

integração com assinatura digital avançada

reemissão controlada com trilha completa

exportação estruturada

base preparada para DCC/XML, alinhada à direção estratégica do Inmetro sobre certificado digital de calibração. 



---

8. Critérios de aceite do MVP

O MVP só deve ser aceito quando:

uma calibração completa puder ser feita no Android do início ao certificado;

o sistema bloquear padrões irregulares;

o certificado sair com resultado, incerteza e fator k;

a revisão e a assinatura ficarem rastreadas;

o QR/code validar autenticidade;

o fluxo offline sincronizar corretamente;

a emissão com conformidade exigir regra de decisão;

o serviço acreditado respeitar escopo e CMC;

toda alteração crítica ficar registrada;

o sistema suportar trabalho não conforme e retenção de registros técnicos. 


9. Decisão prática

Para esse tipo de produto, eu não começaria pela interface do certificado. Eu começaria por esta ordem:

1. modelo de dados


2. regras de negócio


3. workflow da OS


4. motor de cálculo


5. revisão/assinatura


6. emissão do certificado


7. portal/QR


8. qualidade/escopo avançado



Essa ordem reduz retrabalho e evita fazer um app “bonito” com base técnica fraca.
