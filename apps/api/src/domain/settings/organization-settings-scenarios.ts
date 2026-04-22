import type {
  OrganizationSettingsCatalog,
  OrganizationSettingsDetail,
  OrganizationSettingsScenario,
  OrganizationSettingsScenarioId,
  OrganizationSettingsSection,
  OrganizationSettingsSectionKey,
} from "@afere/contracts";

type ScenarioSectionState = OrganizationSettingsSection & {
  summary: string;
  evidenceLabel: string;
  lastReviewedLabel: string;
  reviewModeLabel: string;
  checklistItems: string[];
  blockers: string[];
  warnings: string[];
  links: OrganizationSettingsDetail["links"];
};

type ScenarioDefinition = {
  label: string;
  description: string;
  organizationName: string;
  organizationCode: string;
  profileLabel: string;
  accreditationLabel: string;
  planLabel: string;
  recommendedAction: string;
  defaultSectionKey: OrganizationSettingsSectionKey;
  sections: ScenarioSectionState[];
};

const SCENARIOS: Record<OrganizationSettingsScenarioId, ScenarioDefinition> = {
  "operational-ready": {
    label: "Configuracao operacional controlada",
    description:
      "A organizacao ativa sustenta perfil regulatorio, numeracao, seguranca e LGPD sem bloqueios abertos.",
    organizationName: "Lab. Acme",
    organizationCode: "ACME",
    profileLabel: "Tipo A - RBC acreditado",
    accreditationLabel: "Cgcre CAL-1234 valida ate 30/09/2027",
    planLabel: "Enterprise",
    recommendedAction:
      "Manter o calendario de renovacoes e registrar qualquer mudanca por fluxo controlado com trilha auditavel.",
    defaultSectionKey: "regulatory_profile",
    sections: [
      {
        key: "identity",
        title: "Identidade",
        status: "ready",
        detail: "Razao social, CNPJ e contatos primarios consistentes com o template atual.",
        ownerLabel: "Administracao",
        lastUpdatedLabel: "22/04/2026 09:10 UTC",
        actionLabel: "Revisar identidade",
        summary: "A identidade da organizacao esta coerente com os metadados usados no certificado e no portal.",
        evidenceLabel: "Cadastro conferido no onboarding e refletido no template operacional.",
        lastReviewedLabel: "22/04/2026 09:10 UTC",
        reviewModeLabel: "Mudancas simples com trilha imediata na auditoria.",
        checklistItems: [
          "Razao social e CNPJ conferidos.",
          "Codigo da organizacao alinhado a numeracao do certificado.",
          "Contato principal publicado no back-office.",
        ],
        blockers: [],
        warnings: [],
        links: {
          onboardingScenarioId: "ready",
          workspaceScenarioId: "baseline-ready",
        },
      },
      {
        key: "branding",
        title: "Branding",
        status: "ready",
        detail: "Logo, rodape e identidade visual prontos para o template vigente.",
        ownerLabel: "Marketing interno",
        lastUpdatedLabel: "22/04/2026 09:15 UTC",
        actionLabel: "Revisar branding",
        summary: "O branding aplicado ao certificado e ao portal esta homologado para o perfil atual.",
        evidenceLabel: "Template PDF e portal publico usam a mesma identidade aprovada.",
        lastReviewedLabel: "22/04/2026 09:15 UTC",
        reviewModeLabel: "Mudancas controladas com revisao visual antes da publicacao.",
        checklistItems: [
          "Logo institucional aprovada.",
          "Rodape com endereco e contato operacional revisado.",
          "Cores do certificado alinhadas ao perfil vigente.",
        ],
        blockers: [],
        warnings: [],
        links: {
          onboardingScenarioId: "ready",
          workspaceScenarioId: "baseline-ready",
        },
      },
      {
        key: "regulatory_profile",
        title: "Perfil regulatorio",
        status: "ready",
        detail: "Perfil Tipo A ativo com acreditacao valida e change management controlado.",
        ownerLabel: "Gestao da qualidade",
        lastUpdatedLabel: "22/04/2026 08:50 UTC",
        actionLabel: "Revisar perfil",
        summary:
          "O perfil regulatorio esta consistente com a acreditacao vigente, as regras de simbolo e a trilha de auditoria.",
        evidenceLabel: "Registro de perfil ativo com CAL-1234 e historico consistente na trilha canonica.",
        lastReviewedLabel: "22/04/2026 08:50 UTC",
        reviewModeLabel: "Qualquer alteracao exige dupla aprovacao e registro append-only.",
        checklistItems: [
          "Perfil Tipo A confirmado para a organizacao ativa.",
          "Acreditacao CAL-1234 vigente ate 30/09/2027.",
          "Mudanca de perfil permanece sob fluxo controlado na auditoria.",
        ],
        blockers: [],
        warnings: [],
        links: {
          workspaceScenarioId: "baseline-ready",
          auditTrailScenarioId: "recent-emission",
          standardScenarioId: "operational-ready",
        },
      },
      {
        key: "numbering",
        title: "Numeracao",
        status: "ready",
        detail: "Serie acreditada e prefixo da organizacao consistentes para novas emissoes.",
        ownerLabel: "Administracao",
        lastUpdatedLabel: "22/04/2026 08:40 UTC",
        actionLabel: "Revisar numeracao",
        summary: "A numeracao sequencial por organizacao esta pronta para seguir sem colisao ou drift de prefixo.",
        evidenceLabel: "Prefixo ACME e serie acreditada validados no onboarding e no dry-run de emissao.",
        lastReviewedLabel: "22/04/2026 08:40 UTC",
        reviewModeLabel: "Alteracoes exigem revisao de impacto nos certificados futuros.",
        checklistItems: [
          "Prefixo da organizacao validado.",
          "Serie vigente consistente com o perfil regulatorio.",
          "Proxima emissao segue sem bloqueio de numeracao.",
        ],
        blockers: [],
        warnings: [],
        links: {
          onboardingScenarioId: "ready",
          workspaceScenarioId: "baseline-ready",
        },
      },
      {
        key: "plan",
        title: "Plano",
        status: "ready",
        detail: "Plano Enterprise ativo com capacidade para operacao atual.",
        ownerLabel: "Financeiro",
        lastUpdatedLabel: "21/04/2026 18:10 UTC",
        actionLabel: "Revisar plano",
        summary: "O plano contratado cobre equipe, qualidade, integracoes e governanca do recorte atual.",
        evidenceLabel: "Plano operacional ativo com recursos necessarios para os modulos canonicamente expostos.",
        lastReviewedLabel: "21/04/2026 18:10 UTC",
        reviewModeLabel: "Mudancas seguem workflow comercial sem impacto imediato na emissao atual.",
        checklistItems: [
          "Plano compativel com o uso de qualidade e SSO corporativo.",
          "Capacidade de usuarios e OS atende o recorte atual.",
          "Ativacao comercial sem pendencias abertas.",
        ],
        blockers: [],
        warnings: [],
        links: {
          workspaceScenarioId: "baseline-ready",
        },
      },
      {
        key: "integrations",
        title: "Integracoes",
        status: "ready",
        detail: "Integracoes operacionais mapeadas sem dependencias bloqueantes para V1.",
        ownerLabel: "Operacoes",
        lastUpdatedLabel: "22/04/2026 07:55 UTC",
        actionLabel: "Revisar integracoes",
        summary: "As integracoes em uso nao criam dependencia critica para a emissao controlada do recorte atual.",
        evidenceLabel: "Fluxo V1 opera com backend canonico e sem integracao externa obrigatoria pendente.",
        lastReviewedLabel: "22/04/2026 07:55 UTC",
        reviewModeLabel: "Mudancas sao registradas por secao sem reconfigurar a emissao atual.",
        checklistItems: [
          "Dependencias externas documentadas.",
          "Nao ha bloqueio de integracao para V1.",
          "Escopo atual continua sustentado pelo backend canonico.",
        ],
        blockers: [],
        warnings: [],
        links: {
          workspaceScenarioId: "baseline-ready",
          procedureScenarioId: "operational-ready",
        },
      },
      {
        key: "security",
        title: "Seguranca",
        status: "ready",
        detail: "MFA e politicas de acesso coerentes com os perfis operacionais ativos.",
        ownerLabel: "Gestao da qualidade",
        lastUpdatedLabel: "22/04/2026 08:05 UTC",
        actionLabel: "Revisar seguranca",
        summary: "Os atores criticos mantem MFA e memberships coerentes para operar revisao e assinatura.",
        evidenceLabel: "Diretorio de usuarios e workflow de assinatura sem pendencias criticas.",
        lastReviewedLabel: "22/04/2026 08:05 UTC",
        reviewModeLabel: "Mudancas de acesso exigem rastreio nominal e revisao por papel.",
        checklistItems: [
          "Administradores e signatarios com MFA habilitado.",
          "Memberships ativos por organizacao revisados.",
          "Nao ha usuario suspenso em papel critico.",
        ],
        blockers: [],
        warnings: [],
        links: {
          selfSignupScenarioId: "signatory-ready",
          userDirectoryScenarioId: "operational-team",
          workspaceScenarioId: "baseline-ready",
        },
      },
      {
        key: "sso_saml",
        title: "SSO / SAML",
        status: "ready",
        detail: "SSO social e corporativo alinhados ao perfil do tenant ativo.",
        ownerLabel: "TI",
        lastUpdatedLabel: "22/04/2026 08:00 UTC",
        actionLabel: "Revisar SSO",
        summary: "Os provedores habilitados cobrem o recorte de V1 e o tenant atual sem dependencias abertas.",
        evidenceLabel: "Providers obrigatorios de auth estao expostos e sem drift com o resumo canonicamente publicado.",
        lastReviewedLabel: "22/04/2026 08:00 UTC",
        reviewModeLabel: "Mudancas seguem validacao de auth e auditoria de acesso.",
        checklistItems: [
          "Google, Microsoft e Apple habilitados.",
          "SSO corporativo disponivel para o plano atual.",
          "Fluxos de cadastro e convite permanecem coerentes.",
        ],
        blockers: [],
        warnings: [],
        links: {
          selfSignupScenarioId: "signatory-ready",
          userDirectoryScenarioId: "operational-team",
        },
      },
      {
        key: "notifications",
        title: "Notificacoes",
        status: "ready",
        detail: "Mensagens operacionais configuradas para onboarding, emissao e qualidade.",
        ownerLabel: "Operacoes",
        lastUpdatedLabel: "21/04/2026 17:45 UTC",
        actionLabel: "Revisar notificacoes",
        summary: "As notificacoes obrigatorias para o recorte atual estao mapeadas e sem pendencia de envio.",
        evidenceLabel: "Fluxos transacionais previstos em emissao e qualidade estao documentados nesta organizacao.",
        lastReviewedLabel: "21/04/2026 17:45 UTC",
        reviewModeLabel: "Mudancas de canal nao alteram a logica regulatoria da emissao.",
        checklistItems: [
          "Fluxos transacionais mapeados.",
          "Alertas operacionais habilitados para o time interno.",
          "Nao ha dependencia bloqueante de notificacao para emitir.",
        ],
        blockers: [],
        warnings: [],
        links: {
          workspaceScenarioId: "baseline-ready",
        },
      },
      {
        key: "lgpd_dpo",
        title: "LGPD / DPO",
        status: "ready",
        detail: "Contato de DPO e recorte minimo de dados coerentes com o tenant ativo.",
        ownerLabel: "Privacidade",
        lastUpdatedLabel: "22/04/2026 08:20 UTC",
        actionLabel: "Revisar LGPD",
        summary: "A organizacao mantem contato de DPO e recorte minimo de dados sem pendencias abertas.",
        evidenceLabel: "Rodape, portal e configuracao interna usam o mesmo contato de DPO aprovado.",
        lastReviewedLabel: "22/04/2026 08:20 UTC",
        reviewModeLabel: "Mudancas seguem governanca de privacidade com rastreio auditavel.",
        checklistItems: [
          "Contato do DPO publicado.",
          "Retencao e minimizacao alinhadas ao perfil atual.",
          "Fluxo de direitos do titular permanece documentado.",
        ],
        blockers: [],
        warnings: [],
        links: {
          auditTrailScenarioId: "recent-emission",
          workspaceScenarioId: "baseline-ready",
        },
      },
    ],
  },
  "renewal-attention": {
    label: "Renovacao e governanca em atencao",
    description:
      "A organizacao continua operando, mas vencimentos e governanca secundaria precisam de acao antes do proximo ciclo.",
    organizationName: "Lab. Acme",
    organizationCode: "ACME",
    profileLabel: "Tipo A - RBC acreditado",
    accreditationLabel: "Cgcre CAL-1234 em renovacao ate 30/06/2026",
    planLabel: "Enterprise",
    recommendedAction:
      "Concluir renovacao da acreditacao, revisar notificacoes e atualizar os contatos de privacidade antes do proximo lote.",
    defaultSectionKey: "regulatory_profile",
    sections: [
      {
        key: "identity",
        title: "Identidade",
        status: "ready",
        detail: "Identidade principal permanece consistente para o tenant ativo.",
        ownerLabel: "Administracao",
        lastUpdatedLabel: "22/04/2026 09:10 UTC",
        actionLabel: "Revisar identidade",
        summary: "A identidade da organizacao continua coerente com o certificado e com o portal.",
        evidenceLabel: "Dados basicos sem divergencia estrutural neste recorte.",
        lastReviewedLabel: "22/04/2026 09:10 UTC",
        reviewModeLabel: "Mudancas simples seguem trilha imediata.",
        checklistItems: [
          "Razao social e CNPJ conferidos.",
          "Codigo do tenant permanece consistente.",
          "Contato principal ainda publicado.",
        ],
        blockers: [],
        warnings: [],
        links: {
          onboardingScenarioId: "ready",
          workspaceScenarioId: "team-attention",
        },
      },
      {
        key: "branding",
        title: "Branding",
        status: "ready",
        detail: "Branding vigente segue homologado para o template atual.",
        ownerLabel: "Marketing interno",
        lastUpdatedLabel: "22/04/2026 09:15 UTC",
        actionLabel: "Revisar branding",
        summary: "Nao ha pendencia visual bloqueando o recorte atual.",
        evidenceLabel: "Template e portal seguem consistentes visualmente.",
        lastReviewedLabel: "22/04/2026 09:15 UTC",
        reviewModeLabel: "Revisao visual antes de nova publicacao.",
        checklistItems: [
          "Logo vigente aprovada.",
          "Rodape coerente com a identidade atual.",
          "Template PDF sem pendencia de branding.",
        ],
        blockers: [],
        warnings: [],
        links: {
          workspaceScenarioId: "team-attention",
        },
      },
      {
        key: "regulatory_profile",
        title: "Perfil regulatorio",
        status: "attention",
        detail: "A acreditacao vigente se aproxima do vencimento e o escopo precisa de revisao preventiva.",
        ownerLabel: "Gestao da qualidade",
        lastUpdatedLabel: "22/04/2026 08:35 UTC",
        actionLabel: "Renovar acreditacao",
        summary:
          "O perfil continua ativo, mas a renovacao da acreditacao e a revisao do escopo precisam ser concluidas antes do proximo ciclo.",
        evidenceLabel: "Calendario de renovacao aberto e historico sensivel registrado na trilha canonica.",
        lastReviewedLabel: "22/04/2026 08:35 UTC",
        reviewModeLabel: "Mudancas continuam controladas por governanca e auditoria append-only.",
        checklistItems: [
          "Renovacao da acreditacao iniciada.",
          "Escopo acreditado em revisao preventiva.",
          "Impacto em padroes e simbolos mapeado.",
        ],
        blockers: [],
        warnings: [
          "A acreditacao vence em menos de 90 dias.",
          "A revisao preventiva do escopo ainda nao foi encerrada.",
        ],
        links: {
          workspaceScenarioId: "team-attention",
          auditTrailScenarioId: "reissue-attention",
          standardScenarioId: "expiration-attention",
        },
      },
      {
        key: "numbering",
        title: "Numeracao",
        status: "ready",
        detail: "A serie atual permanece consistente para as emissoes do recorte.",
        ownerLabel: "Administracao",
        lastUpdatedLabel: "22/04/2026 08:40 UTC",
        actionLabel: "Revisar numeracao",
        summary: "A numeracao atual segue operacional, sem colisao ou troca de prefixo pendente.",
        evidenceLabel: "Serie vigente validada nos cenarios canonicamente expostos.",
        lastReviewedLabel: "22/04/2026 08:40 UTC",
        reviewModeLabel: "Mudancas continuam condicionadas a revisao de impacto.",
        checklistItems: [
          "Prefixo vigente consistente.",
          "Serie atual segue sem colisao.",
          "Nao ha bloqueio imediato de numeracao.",
        ],
        blockers: [],
        warnings: [],
        links: {
          workspaceScenarioId: "team-attention",
          onboardingScenarioId: "ready",
        },
      },
      {
        key: "plan",
        title: "Plano",
        status: "ready",
        detail: "Plano atual continua cobrindo o recorte de operacao e governanca.",
        ownerLabel: "Financeiro",
        lastUpdatedLabel: "21/04/2026 18:10 UTC",
        actionLabel: "Revisar plano",
        summary: "Nao ha restricao comercial imediata impactando a operacao atual.",
        evidenceLabel: "Capacidade contratada segue compativel com o tenant ativo.",
        lastReviewedLabel: "21/04/2026 18:10 UTC",
        reviewModeLabel: "Ajustes comerciais sem impacto regulatorio imediato.",
        checklistItems: [
          "Plano cobre modulos operacionais ativos.",
          "Capacidade contratada permanece suficiente.",
          "Sem pendencia comercial aberta.",
        ],
        blockers: [],
        warnings: [],
        links: {
          workspaceScenarioId: "team-attention",
        },
      },
      {
        key: "integrations",
        title: "Integracoes",
        status: "attention",
        detail: "O mapeamento existe, mas uma revisao de procedimento ainda nao foi formalmente concluida.",
        ownerLabel: "Operacoes",
        lastUpdatedLabel: "22/04/2026 07:55 UTC",
        actionLabel: "Revisar integracoes",
        summary: "A operacao segue, mas um procedimento de interface documental continua em atencao.",
        evidenceLabel: "Procedimento em revisao preventiva para manter o recorte integrado sem drift.",
        lastReviewedLabel: "22/04/2026 07:55 UTC",
        reviewModeLabel: "Mudancas exigem alinhamento documental antes de promover novo fluxo.",
        checklistItems: [
          "Mapeamento de integracoes mantido.",
          "Revisao documental aberta para interface operacional.",
          "Recorte atual continua sem dependencia bloqueante.",
        ],
        blockers: [],
        warnings: ["Procedimento de interface ainda em revisao preventiva."],
        links: {
          workspaceScenarioId: "team-attention",
          procedureScenarioId: "revision-attention",
        },
      },
      {
        key: "security",
        title: "Seguranca",
        status: "attention",
        detail: "A equipe segue apta, mas um fator de endurecimento operacional ainda precisa de reforco.",
        ownerLabel: "Gestao da qualidade",
        lastUpdatedLabel: "22/04/2026 08:05 UTC",
        actionLabel: "Revisar seguranca",
        summary: "O tenant continua operando, mas ha competencias e sinais preventivos pedindo revisao do acesso.",
        evidenceLabel: "Diretorio mostra competencia expirando antes do proximo ciclo.",
        lastReviewedLabel: "22/04/2026 08:05 UTC",
        reviewModeLabel: "Ajustes de acesso precisam preservar segregacao de funcoes.",
        checklistItems: [
          "MFA segue ativo para papeis criticos.",
          "Competencias com vencimento proximo identificadas.",
          "Memberships do tenant continuam integrais.",
        ],
        blockers: [],
        warnings: ["Competencia critica expira em menos de 30 dias."],
        links: {
          selfSignupScenarioId: "admin-guided",
          userDirectoryScenarioId: "expiring-competencies",
          workspaceScenarioId: "team-attention",
        },
      },
      {
        key: "sso_saml",
        title: "SSO / SAML",
        status: "ready",
        detail: "Providers seguem funcionais para o recorte atual.",
        ownerLabel: "TI",
        lastUpdatedLabel: "22/04/2026 08:00 UTC",
        actionLabel: "Revisar SSO",
        summary: "Nao ha drift entre provedores habilitados e a leitura canonica atual de auth.",
        evidenceLabel: "Fluxo de auto-cadastro continua consistente com os providers publicados.",
        lastReviewedLabel: "22/04/2026 08:00 UTC",
        reviewModeLabel: "Mudancas continuam condicionadas a validacao de auth.",
        checklistItems: [
          "Providers obrigatorios permanecem ativos.",
          "Tenant continua apto para convites e auto-cadastro.",
          "Nao ha falha estrutural de SSO neste recorte.",
        ],
        blockers: [],
        warnings: [],
        links: {
          selfSignupScenarioId: "admin-guided",
          userDirectoryScenarioId: "expiring-competencies",
        },
      },
      {
        key: "notifications",
        title: "Notificacoes",
        status: "attention",
        detail: "Alguns avisos preventivos ainda nao foram revisados para o novo ciclo de renovacao.",
        ownerLabel: "Operacoes",
        lastUpdatedLabel: "21/04/2026 17:45 UTC",
        actionLabel: "Revisar notificacoes",
        summary: "Os canais existem, mas a cadencia de mensagens preventivas precisa ser ajustada antes do proximo ciclo.",
        evidenceLabel: "Plano de avisos preventivos ainda depende de revisao final do gestor.",
        lastReviewedLabel: "21/04/2026 17:45 UTC",
        reviewModeLabel: "Ajustes de notificacao nao podem introduzir drift operacional.",
        checklistItems: [
          "Mensagens transacionais principais mantidas.",
          "Cadencia de avisos preventivos em revisao.",
          "Sem bloqueio de emissao por notificacao.",
        ],
        blockers: [],
        warnings: ["Resumo preventivo de renovacao ainda nao foi revalidado."],
        links: {
          workspaceScenarioId: "team-attention",
        },
      },
      {
        key: "lgpd_dpo",
        title: "LGPD / DPO",
        status: "attention",
        detail: "Contato de privacidade existe, mas o dossie operacional precisa de atualizacao complementar.",
        ownerLabel: "Privacidade",
        lastUpdatedLabel: "22/04/2026 08:20 UTC",
        actionLabel: "Atualizar DPO",
        summary: "A governanca de privacidade permanece ativa, mas o contato e a ultima revisao precisam de atualizacao preventiva.",
        evidenceLabel: "Contato de DPO publicado, com revisao complementar ainda pendente no dossie operacional.",
        lastReviewedLabel: "22/04/2026 08:20 UTC",
        reviewModeLabel: "Mudancas seguem governanca de privacidade com rastreio auditavel.",
        checklistItems: [
          "Contato do DPO publicado.",
          "Revisao periodica de privacidade agendada.",
          "Fluxo de direitos do titular permanece mapeado.",
        ],
        blockers: [],
        warnings: ["Revisao anual de privacidade ainda nao foi encerrada."],
        links: {
          auditTrailScenarioId: "reissue-attention",
          workspaceScenarioId: "team-attention",
        },
      },
    ],
  },
  "profile-change-blocked": {
    label: "Mudanca de perfil bloqueada",
    description:
      "A organizacao tenta promover um novo perfil regulatorio, mas a governanca ainda nao liberou a alteracao de forma fail-closed.",
    organizationName: "Metrologia Campo Sul",
    organizationCode: "MCS",
    profileLabel: "Mudanca Tipo B -> Tipo A pendente",
    accreditationLabel: "Sem aprovacao final de perfil e sem CAL ativo",
    planLabel: "Pro",
    recommendedAction:
      "Nao promover o perfil nem emitir como Tipo A ate concluir dupla aprovacao, revisar escopo/CMC e ajustar a serie acreditada.",
    defaultSectionKey: "regulatory_profile",
    sections: [
      {
        key: "identity",
        title: "Identidade",
        status: "ready",
        detail: "Identidade basica da organizacao permanece consistente.",
        ownerLabel: "Administracao",
        lastUpdatedLabel: "22/04/2026 10:10 UTC",
        actionLabel: "Revisar identidade",
        summary: "A identidade do tenant esta correta, mas isso nao autoriza a mudanca de perfil por si so.",
        evidenceLabel: "Dados cadastrais sem divergencia estrutural.",
        lastReviewedLabel: "22/04/2026 10:10 UTC",
        reviewModeLabel: "Mudancas simples seguem trilha imediata.",
        checklistItems: [
          "Razao social consistente.",
          "Codigo do tenant sem conflito.",
          "Contato principal publicado.",
        ],
        blockers: [],
        warnings: [],
        links: {
          onboardingScenarioId: "blocked",
          workspaceScenarioId: "release-blocked",
        },
      },
      {
        key: "branding",
        title: "Branding",
        status: "ready",
        detail: "Branding basico existe, mas nao libera uso de selo nem template acreditado.",
        ownerLabel: "Marketing interno",
        lastUpdatedLabel: "22/04/2026 10:05 UTC",
        actionLabel: "Revisar branding",
        summary: "A identidade visual continua neutra enquanto a mudanca regulatoria segue bloqueada.",
        evidenceLabel: "Nao ha branding acreditado publicado antes da aprovacao formal.",
        lastReviewedLabel: "22/04/2026 10:05 UTC",
        reviewModeLabel: "Liberacao visual depende da decisao regulatoria.",
        checklistItems: [
          "Template acreditado ainda nao foi promovido.",
          "Rodape atual segue perfil nao acreditado.",
          "Nao ha selo publicado antes da aprovacao.",
        ],
        blockers: [],
        warnings: [],
        links: {
          workspaceScenarioId: "release-blocked",
        },
      },
      {
        key: "regulatory_profile",
        title: "Perfil regulatorio",
        status: "blocked",
        detail: "A mudanca para Tipo A foi solicitada sem dupla aprovacao valida e sem escopo/CMC homologados.",
        ownerLabel: "Gestao da qualidade",
        lastUpdatedLabel: "22/04/2026 10:00 UTC",
        actionLabel: "Concluir dupla aprovacao",
        summary:
          "A organizacao nao pode mudar para Tipo A nem habilitar simbolo acreditado enquanto faltarem aprovadores e evidencias do escopo.",
        evidenceLabel: "Solicitacao aberta sem segundo aprovador e sem pacote formal de escopo/CMC homologado.",
        lastReviewedLabel: "22/04/2026 10:00 UTC",
        reviewModeLabel: "Mudanca de perfil segue fail-closed ate existir dupla aprovacao auditavel.",
        checklistItems: [
          "Primeiro aprovador registrado.",
          "Segundo aprovador ainda ausente.",
          "Escopo e CMC ainda nao homologados.",
        ],
        blockers: [
          "Mudanca de perfil sem dupla aprovacao concluida.",
          "Escopo acreditado e CMC ainda nao foram homologados.",
        ],
        warnings: ["A organizacao segue no perfil anterior ate o encerramento formal da mudanca."],
        links: {
          onboardingScenarioId: "blocked",
          workspaceScenarioId: "release-blocked",
          auditTrailScenarioId: "reissue-attention",
          standardScenarioId: "expired-blocked",
        },
      },
      {
        key: "numbering",
        title: "Numeracao",
        status: "blocked",
        detail: "A serie acreditada ainda nao foi configurada para o perfil solicitado.",
        ownerLabel: "Administracao",
        lastUpdatedLabel: "22/04/2026 09:52 UTC",
        actionLabel: "Configurar serie acreditada",
        summary: "Nao ha serie valida para emitir como Tipo A enquanto o tenant continua sem prefixo e governanca homologados.",
        evidenceLabel: "A numeracao atual permanece interna e nao pode ser promovida para serie acreditada automaticamente.",
        lastReviewedLabel: "22/04/2026 09:52 UTC",
        reviewModeLabel: "A serie so muda apos liberacao formal do novo perfil.",
        checklistItems: [
          "Serie interna atual identificada.",
          "Serie acreditada ainda nao configurada.",
          "Historico anterior preservado para o perfil vigente.",
        ],
        blockers: ["Serie acreditada ausente para o perfil solicitado."],
        warnings: ["Nao migrar numeracao antes da aprovacao formal do perfil."],
        links: {
          onboardingScenarioId: "blocked",
          workspaceScenarioId: "release-blocked",
        },
      },
      {
        key: "plan",
        title: "Plano",
        status: "attention",
        detail: "O plano atual sustenta V1, mas nao inclui a governanca completa esperada para a transicao de perfil.",
        ownerLabel: "Financeiro",
        lastUpdatedLabel: "21/04/2026 18:10 UTC",
        actionLabel: "Revisar plano",
        summary: "O tenant continua operando, mas a transicao regulatoria exige revisao comercial e de capacidade.",
        evidenceLabel: "Plano Pro ativo, sem liberar automaticamente governanca adicional do perfil solicitado.",
        lastReviewedLabel: "21/04/2026 18:10 UTC",
        reviewModeLabel: "Ajustes comerciais nao substituem aprovacao regulatoria.",
        checklistItems: [
          "Plano atual identificado.",
          "Capacidade para o recorte atual preservada.",
          "Transicao de perfil exige revisao comercial complementar.",
        ],
        blockers: [],
        warnings: ["A mudanca de perfil pode exigir revisao contratual."],
        links: {
          workspaceScenarioId: "release-blocked",
        },
      },
      {
        key: "integrations",
        title: "Integracoes",
        status: "attention",
        detail: "A documentacao de interface para o novo perfil ainda nao foi revisada.",
        ownerLabel: "Operacoes",
        lastUpdatedLabel: "22/04/2026 09:40 UTC",
        actionLabel: "Revisar integracoes",
        summary: "O tenant opera no perfil atual, mas a documentacao de integracoes nao cobre a mudanca solicitada.",
        evidenceLabel: "Procedimento vigente nao contempla a transicao regulatoria pretendida.",
        lastReviewedLabel: "22/04/2026 09:40 UTC",
        reviewModeLabel: "Mudancas devem ser aprovadas documentalmente antes da promocao.",
        checklistItems: [
          "Integracoes atuais mapeadas.",
          "Procedimento de transicao ainda nao revisado.",
          "Nao ha dependencia externa liberando a mudanca.",
        ],
        blockers: [],
        warnings: ["Procedimento da transicao ainda obsoleto para o perfil pretendido."],
        links: {
          procedureScenarioId: "obsolete-visible",
          workspaceScenarioId: "release-blocked",
        },
      },
      {
        key: "security",
        title: "Seguranca",
        status: "attention",
        detail: "A mudanca controlada depende de um segundo aprovador com papel e MFA validos.",
        ownerLabel: "Gestao da qualidade",
        lastUpdatedLabel: "22/04/2026 09:45 UTC",
        actionLabel: "Qualificar aprovadores",
        summary: "A governanca de acesso ainda nao suporta a dupla aprovacao exigida para a transicao.",
        evidenceLabel: "Diretorio operacional indica falta de combinacao valida para aprovar a mudanca.",
        lastReviewedLabel: "22/04/2026 09:45 UTC",
        reviewModeLabel: "Ajustes de acesso devem preservar segregacao de funcoes e MFA.",
        checklistItems: [
          "Primeiro aprovador elegivel identificado.",
          "Segundo aprovador ainda nao elegivel.",
          "MFA continua obrigatorio para liberacao formal.",
        ],
        blockers: [],
        warnings: ["Nao ha dupla combinacao de aprovadores liberada neste momento."],
        links: {
          selfSignupScenarioId: "technician-blocked",
          userDirectoryScenarioId: "suspended-access",
          workspaceScenarioId: "release-blocked",
        },
      },
      {
        key: "sso_saml",
        title: "SSO / SAML",
        status: "attention",
        detail: "O recorte de auth segue funcional, mas ainda nao apoia a governanca expandida da transicao.",
        ownerLabel: "TI",
        lastUpdatedLabel: "22/04/2026 09:30 UTC",
        actionLabel: "Revisar auth",
        summary: "Os providers basicos seguem ativos, mas a combinacao atual ainda nao sustenta a governanca desejada para o novo perfil.",
        evidenceLabel: "Auth permanece operacional, sem liberar por si so a mudanca regulatoria.",
        lastReviewedLabel: "22/04/2026 09:30 UTC",
        reviewModeLabel: "Mudancas de auth seguem validacao separada do perfil regulatorio.",
        checklistItems: [
          "Providers basicos ativos.",
          "Fluxo de cadastro permanece funcional.",
          "Transicao regulatoria nao depende apenas de auth.",
        ],
        blockers: [],
        warnings: ["Nao assumir que auth pronto libera mudanca regulatoria."],
        links: {
          selfSignupScenarioId: "technician-blocked",
          userDirectoryScenarioId: "suspended-access",
        },
      },
      {
        key: "notifications",
        title: "Notificacoes",
        status: "attention",
        detail: "A comunicacao da mudanca ainda nao foi revisada para o novo fluxo controlado.",
        ownerLabel: "Operacoes",
        lastUpdatedLabel: "21/04/2026 17:45 UTC",
        actionLabel: "Revisar notificacoes",
        summary: "As notificacoes existem, mas nao devem anunciar alteracao de perfil antes do encerramento formal.",
        evidenceLabel: "Nao ha publicacao automatica da mudanca pendente.",
        lastReviewedLabel: "21/04/2026 17:45 UTC",
        reviewModeLabel: "Comunicacao depende da aprovacao final do perfil.",
        checklistItems: [
          "Canais existentes mapeados.",
          "Sem anuncio de mudanca antes da aprovacao.",
          "Fluxos transacionais atuais preservados.",
        ],
        blockers: [],
        warnings: ["Nao comunicar o novo perfil antes do encerramento formal."],
        links: {
          workspaceScenarioId: "release-blocked",
        },
      },
      {
        key: "lgpd_dpo",
        title: "LGPD / DPO",
        status: "ready",
        detail: "Privacidade continua controlada, sem relacao direta com o bloqueio regulatorio atual.",
        ownerLabel: "Privacidade",
        lastUpdatedLabel: "22/04/2026 08:20 UTC",
        actionLabel: "Revisar LGPD",
        summary: "A governanca de privacidade segue integra mesmo com a transicao regulatoria bloqueada.",
        evidenceLabel: "Contato de DPO e trilha de privacidade continuam consistentes.",
        lastReviewedLabel: "22/04/2026 08:20 UTC",
        reviewModeLabel: "Mudancas seguem governanca de privacidade separada.",
        checklistItems: [
          "Contato do DPO publicado.",
          "Fluxo de direitos do titular mapeado.",
          "Sem bloqueio de privacidade adicional neste recorte.",
        ],
        blockers: [],
        warnings: [],
        links: {
          auditTrailScenarioId: "recent-emission",
          workspaceScenarioId: "release-blocked",
        },
      },
    ],
  },
};

const DEFAULT_SCENARIO: OrganizationSettingsScenarioId = "operational-ready";
const SECTION_KEYS: OrganizationSettingsSectionKey[] = SCENARIOS[DEFAULT_SCENARIO].sections.map(
  (section) => section.key,
);

export function listOrganizationSettingsScenarios(): OrganizationSettingsScenario[] {
  return (Object.keys(SCENARIOS) as OrganizationSettingsScenarioId[]).map((scenarioId) =>
    resolveOrganizationSettingsScenario(scenarioId),
  );
}

export function resolveOrganizationSettingsScenario(
  scenarioId?: string,
  sectionKey?: string,
): OrganizationSettingsScenario {
  const definition = resolveDefinition(scenarioId);
  const selectedSection = resolveSectionState(definition, sectionKey);

  return {
    id: resolveScenarioId(scenarioId),
    label: definition.label,
    description: definition.description,
    summary: buildSummary(definition),
    selectedSectionKey: selectedSection.key,
    sections: definition.sections.map(toSection),
    detail: toDetail(selectedSection),
  };
}

export function buildOrganizationSettingsCatalog(
  scenarioId?: string,
  sectionKey?: string,
): OrganizationSettingsCatalog {
  const selectedScenario = resolveOrganizationSettingsScenario(scenarioId, sectionKey);

  return {
    selectedScenarioId: selectedScenario.id,
    scenarios: listOrganizationSettingsScenarios().map((scenario) =>
      scenario.id === selectedScenario.id ? selectedScenario : scenario,
    ),
  };
}

function buildSummary(definition: ScenarioDefinition): OrganizationSettingsScenario["summary"] {
  const configuredSections = definition.sections.filter((section) => section.status === "ready").length;
  const attentionSections = definition.sections.filter((section) => section.status === "attention").length;
  const blockedSections = definition.sections.filter((section) => section.status === "blocked").length;

  return {
    status: blockedSections > 0 ? "blocked" : attentionSections > 0 ? "attention" : "ready",
    organizationName: definition.organizationName,
    organizationCode: definition.organizationCode,
    profileLabel: definition.profileLabel,
    accreditationLabel: definition.accreditationLabel,
    planLabel: definition.planLabel,
    configuredSections,
    attentionSections,
    blockedSections,
    recommendedAction: definition.recommendedAction,
    blockers: unique(definition.sections.flatMap((section) => section.blockers)),
    warnings: unique(definition.sections.flatMap((section) => section.warnings)),
  };
}

function resolveSectionState(
  definition: ScenarioDefinition,
  sectionKey?: string,
): ScenarioSectionState {
  const selectedKey = isOrganizationSettingsSectionKey(sectionKey)
    ? sectionKey
    : definition.defaultSectionKey;
  const selected = definition.sections.find((section) => section.key === selectedKey);

  if (!selected) {
    throw new Error(`missing_settings_section:${selectedKey}`);
  }

  return selected;
}

function toSection(state: ScenarioSectionState): OrganizationSettingsSection {
  return {
    key: state.key,
    title: state.title,
    status: state.status,
    detail: state.detail,
    ownerLabel: state.ownerLabel,
    lastUpdatedLabel: state.lastUpdatedLabel,
    actionLabel: state.actionLabel,
  };
}

function toDetail(state: ScenarioSectionState): OrganizationSettingsDetail {
  return {
    sectionKey: state.key,
    title: state.title,
    status: state.status,
    summary: state.summary,
    evidenceLabel: state.evidenceLabel,
    lastReviewedLabel: state.lastReviewedLabel,
    reviewModeLabel: state.reviewModeLabel,
    checklistItems: state.checklistItems,
    blockers: state.blockers,
    warnings: state.warnings,
    links: state.links,
  };
}

function resolveScenarioId(scenarioId?: string): OrganizationSettingsScenarioId {
  return isOrganizationSettingsScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO;
}

function resolveDefinition(scenarioId?: string): ScenarioDefinition {
  return SCENARIOS[resolveScenarioId(scenarioId)];
}

function isOrganizationSettingsScenarioId(value: string | undefined): value is OrganizationSettingsScenarioId {
  return typeof value === "string" && value in SCENARIOS;
}

function isOrganizationSettingsSectionKey(value: string | undefined): value is OrganizationSettingsSectionKey {
  return typeof value === "string" && SECTION_KEYS.includes(value as OrganizationSettingsSectionKey);
}

function unique(values: string[]): string[] {
  return [...new Set(values)];
}
