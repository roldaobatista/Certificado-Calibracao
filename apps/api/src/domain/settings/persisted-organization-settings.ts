import type { OrganizationSettingsCatalog } from "@afere/contracts";

import type { PersistedUserRecord, PersistedOnboardingRecord } from "../auth/core-persistence.js";
import type { PersistedServiceOrderRecord } from "../emission/service-order-persistence.js";
import type { PersistedComplianceProfileRecord } from "../quality/quality-persistence.js";

type SettingsStatus = "ready" | "attention" | "blocked";

type PersistedSectionState = {
  key:
    | "identity"
    | "branding"
    | "regulatory_profile"
    | "numbering"
    | "plan"
    | "integrations"
    | "security"
    | "sso_saml"
    | "notifications"
    | "lgpd_dpo";
  title: string;
  status: SettingsStatus;
  detail: string;
  ownerLabel: string;
  lastUpdatedLabel: string;
  actionLabel: string;
  summary: string;
  evidenceLabel: string;
  lastReviewedLabel: string;
  reviewModeLabel: string;
  checklistItems: string[];
  blockers: string[];
  warnings: string[];
  links: {
    onboardingScenarioId?: "ready" | "blocked";
    selfSignupScenarioId?: "signatory-ready" | "admin-guided" | "technician-blocked";
    userDirectoryScenarioId?: "operational-team" | "expiring-competencies" | "suspended-access";
    workspaceScenarioId?: "release-blocked" | "team-attention" | "baseline-ready";
    auditTrailScenarioId?: "reissue-attention" | "recent-emission" | "integrity-blocked";
    standardScenarioId?: "operational-ready" | "expiration-attention" | "expired-blocked";
    procedureScenarioId?: "operational-ready" | "revision-attention" | "obsolete-visible";
  };
};

export function buildPersistedOrganizationSettingsCatalog(input: {
  organizationName: string;
  organizationSlug: string;
  users: PersistedUserRecord[];
  onboarding?: PersistedOnboardingRecord | null;
  serviceOrders: PersistedServiceOrderRecord[];
  complianceProfile?: PersistedComplianceProfileRecord | null;
  selectedSectionKey?: string;
}): OrganizationSettingsCatalog {
  const profile = input.complianceProfile;
  const openServiceOrders = input.serviceOrders.filter((record) => record.workflowStatus !== "emitted").length;
  const emittedOrders = input.serviceOrders.filter((record) => record.workflowStatus === "emitted").length;
  const privilegedUsers = input.users.filter((user) =>
    user.roles.some((role) => role === "admin" || role === "quality_manager" || role === "signatory"),
  );
  const mfaCovered = privilegedUsers.every((user) => user.mfaEnrolled);
  const regulatoryStatus =
    !profile
      ? "blocked"
      : profile.regulatoryProfile === "type_a" &&
          (!profile.accreditationNumber || profile.scopeItemCount === 0 || profile.cmcItemCount === 0)
        ? "blocked"
        : profile.releaseNormStatus.toLowerCase().includes("pending")
          ? "attention"
          : "ready";

  const sections: PersistedSectionState[] = [
    {
      key: "identity",
      title: "Identidade",
      status: "ready" as const,
      detail: `Organizacao ${input.organizationName} com slug ${input.organizationSlug} persistidos no tenant.`,
      ownerLabel: "Administracao",
      lastUpdatedLabel: formatDate(profile?.lastReviewedAtUtc),
      actionLabel: "Revisar identidade",
      summary: "A identidade real do tenant sustenta o certificado, o portal e o dossie V5.",
      evidenceLabel: "Nome legal, slug e prefixo do tenant versionados na base persistida.",
      lastReviewedLabel: formatDate(profile?.lastReviewedAtUtc),
      reviewModeLabel: "Mudancas exigem trilha auditavel e coerencia com o perfil regulatorio.",
      checklistItems: [
        `Razao social persistida: ${input.organizationName}.`,
        `Slug operacional: ${input.organizationSlug}.`,
        `Codigo organizacional: ${profile?.organizationCode ?? "pendente"}.`,
      ],
      blockers: [],
      warnings: [],
      links: {
        onboardingScenarioId: input.onboarding ? "ready" : "blocked",
        workspaceScenarioId: openServiceOrders > 0 ? "team-attention" : "baseline-ready",
      },
    },
    {
      key: "branding",
      title: "Branding",
      status: "ready" as const,
      detail: "A V5 preserva branding institucional sem abrir editor transacional dedicado nesta fatia.",
      ownerLabel: "Administracao",
      lastUpdatedLabel: formatDate(profile?.lastReviewedAtUtc),
      actionLabel: "Revisar branding",
      summary: "Branding permanece controlado no tenant sem reabrir a trilha critica da emissao.",
      evidenceLabel: "Template atual coerente com a organizacao e com o portal persistido.",
      lastReviewedLabel: formatDate(profile?.lastReviewedAtUtc),
      reviewModeLabel: "Mudancas visuais continuam sob controle antes de nova publicacao.",
      checklistItems: [
        "Identidade visual coerente com a organizacao persistida.",
        "Nao ha dependencia de branding para liberar a V5.",
      ],
      blockers: [],
      warnings: [],
      links: {
        workspaceScenarioId: emittedOrders > 0 ? "baseline-ready" : "team-attention",
      },
    },
    {
      key: "regulatory_profile",
      title: "Perfil regulatorio",
      status: regulatoryStatus,
      detail: profile
        ? `Perfil ${profile.regulatoryProfile} com release ${profile.releaseNormVersion} e governanca ${profile.normativeGovernanceStatus}.`
        : "Perfil regulatorio ainda nao materializado no tenant.",
      ownerLabel: "Gestao da Qualidade",
      lastUpdatedLabel: formatDate(profile?.lastReviewedAtUtc),
      actionLabel: "Revisar perfil",
      summary:
        "A V5 integra perfil regulatorio, escopo/CMC, parecer juridico e rito de release-norm ao tenant real.",
      evidenceLabel: profile
        ? `${profile.legalOpinionReference} · ${profile.normativeGovernanceReference}`
        : "Perfil regulatorio pendente de cadastro.",
      lastReviewedLabel: formatDate(profile?.lastReviewedAtUtc),
      reviewModeLabel: "Qualquer mudanca de perfil permanece fail-closed e exige governance real.",
      checklistItems: [
        `Perfil regulatorio: ${profile?.regulatoryProfile ?? "pendente"}.`,
        `Escopo cadastrado: ${profile?.scopeItemCount ?? 0} item(ns).`,
        `CMC cadastrada: ${profile?.cmcItemCount ?? 0} item(ns).`,
        `Release-norm vigente: ${profile?.releaseNormVersion ?? "pendente"}.`,
      ],
      blockers:
        regulatoryStatus === "blocked"
          ? ["Perfil Tipo A sem escopo/CMC ou sem acreditacao valida materializada no tenant."]
          : [],
      warnings:
        regulatoryStatus === "attention"
          ? ["A governanca regulatoria ainda exige follow-up antes do fechamento final da release."]
          : [],
      links: {
        workspaceScenarioId: regulatoryStatus === "blocked" ? "release-blocked" : "baseline-ready",
        auditTrailScenarioId: regulatoryStatus === "blocked" ? "integrity-blocked" : "recent-emission",
        standardScenarioId: "operational-ready",
      },
    },
    {
      key: "numbering",
      title: "Numeracao",
      status: profile?.certificatePrefix ? "ready" : "attention",
      detail: profile?.certificatePrefix
        ? `Prefixo ${profile.certificatePrefix} persistido para o tenant.`
        : "Prefixo certificado ainda nao informado no perfil do tenant.",
      ownerLabel: "Administracao",
      lastUpdatedLabel: formatDate(profile?.lastReviewedAtUtc),
      actionLabel: "Revisar numeracao",
      summary: "A numeracao real de certificados agora faz parte da governanca persistida do tenant.",
      evidenceLabel: profile?.certificatePrefix
        ? `Prefixo ${profile.certificatePrefix} e codigo ${profile.organizationCode}.`
        : "Prefixo ausente no perfil persistido.",
      lastReviewedLabel: formatDate(profile?.lastReviewedAtUtc),
      reviewModeLabel: "Mudancas exigem coerencia com emissao, reemissao e release-norm.",
      checklistItems: [
        `Prefixo atual: ${profile?.certificatePrefix ?? "pendente"}.`,
        `OS emitidas no tenant: ${emittedOrders}.`,
      ],
      blockers: [],
      warnings: profile?.certificatePrefix ? [] : ["Prefixo de certificado ainda nao materializado no tenant."],
      links: {
        onboardingScenarioId: input.onboarding?.certificateNumberingConfigured ? "ready" : "blocked",
        workspaceScenarioId: emittedOrders > 0 ? "baseline-ready" : "team-attention",
      },
    },
    {
      key: "plan",
      title: "Plano",
      status: profile?.planLabel ? "ready" : "attention",
      detail: profile?.planLabel ? `Plano atual: ${profile.planLabel}.` : "Plano ainda nao explicitado no perfil persistido.",
      ownerLabel: "Financeiro",
      lastUpdatedLabel: formatDate(profile?.lastReviewedAtUtc),
      actionLabel: "Revisar plano",
      summary: "A V5 expõe o plano operacional junto ao perfil real do tenant.",
      evidenceLabel: profile?.planLabel ?? "Plano pendente no perfil do tenant.",
      lastReviewedLabel: formatDate(profile?.lastReviewedAtUtc),
      reviewModeLabel: "Mudancas contratuais nao reabrem a trilha critica sem revisao de impacto.",
      checklistItems: [
        `Plano operacional: ${profile?.planLabel ?? "pendente"}.`,
        `Usuarios ativos: ${input.users.filter((user) => user.status === "active").length}.`,
      ],
      blockers: [],
      warnings: profile?.planLabel ? [] : ["Plano nao foi materializado no cadastro persistido."],
      links: {
        workspaceScenarioId: "baseline-ready",
      },
    },
    {
      key: "integrations",
      title: "Integracoes",
      status: "ready" as const,
      detail: "A V5 continua sem dependencia externa obrigatoria para operar o fluxo real principal.",
      ownerLabel: "TI",
      lastUpdatedLabel: formatDate(profile?.lastReviewedAtUtc),
      actionLabel: "Revisar integracoes",
      summary: "Integracoes nao bloqueiam o recorte persistido da V5.",
      evidenceLabel: "Fluxo central, Qualidade e governanca rodam sobre a mesma base persistida.",
      lastReviewedLabel: formatDate(profile?.lastReviewedAtUtc),
      reviewModeLabel: "Novas integracoes seguem evolucao futura sem desbloquear falhas silenciosas.",
      checklistItems: [
        "Nenhuma integracao externa e requisito para operar a V5 local.",
        "Backoffice e API usam a mesma base persistida do tenant.",
      ],
      blockers: [],
      warnings: [],
      links: {
        procedureScenarioId: "operational-ready",
        workspaceScenarioId: "baseline-ready",
      },
    },
    {
      key: "security",
      title: "Seguranca",
      status: mfaCovered ? "ready" : "attention",
      detail: mfaCovered
        ? "Perfis privilegiados persistidos com MFA enrolado."
        : "Ainda existem perfis privilegiados sem MFA enrolado no tenant.",
      ownerLabel: "Gestao da Qualidade",
      lastUpdatedLabel: formatDate(profile?.lastReviewedAtUtc),
      actionLabel: "Revisar seguranca",
      summary: "A seguranca da V5 considera usuarios reais que operam Qualidade, revisao e assinatura.",
      evidenceLabel: `${privilegedUsers.length} usuario(s) privilegiado(s) avaliados.`,
      lastReviewedLabel: formatDate(profile?.lastReviewedAtUtc),
      reviewModeLabel: "Acesso privilegiado continua sob RBAC e MFA no tenant persistido.",
      checklistItems: [
        `${privilegedUsers.filter((user) => user.mfaEnrolled).length}/${privilegedUsers.length} perfis privilegiados com MFA.`,
        `${input.users.filter((user) => user.status === "suspended").length} usuario(s) suspenso(s).`,
      ],
      blockers: [],
      warnings: mfaCovered ? [] : ["Existem perfis privilegiados sem MFA enrolado."],
      links: {
        userDirectoryScenarioId: "operational-team",
        workspaceScenarioId: mfaCovered ? "baseline-ready" : "team-attention",
      },
    },
    {
      key: "sso_saml",
      title: "SSO / SAML",
      status: "attention" as const,
      detail: "A V5 preserva o contrato canônico de auth, mas nao abre SSO corporativo transacional nesta fatia.",
      ownerLabel: "TI",
      lastUpdatedLabel: formatDate(profile?.lastReviewedAtUtc),
      actionLabel: "Revisar SSO",
      summary: "SSO/SAML continua documentado, sem ser eixo bloqueante do fechamento da V5.",
      evidenceLabel: "Sessao HTTP-only e RBAC reais seguem como mecanismo de auth persistido desta fatia.",
      lastReviewedLabel: formatDate(profile?.lastReviewedAtUtc),
      reviewModeLabel: "SSO corporativo continua evolucao futura sem abrir excecao de seguranca.",
      checklistItems: [
        "Sessao persistida ativa no backend.",
        "RBAC aplicado nas rotas sensiveis da V5.",
      ],
      blockers: [],
      warnings: ["SSO/SAML corporativo continua sem fluxo transacional dedicado nesta fatia."],
      links: {
        selfSignupScenarioId: "signatory-ready",
        userDirectoryScenarioId: "operational-team",
      },
    },
    {
      key: "notifications",
      title: "Notificacoes",
      status: "ready" as const,
      detail: "A V5 usa o mesmo backoffice persistido para registrar follow-up e evidencias sem depender de canal externo.",
      ownerLabel: "Operacoes",
      lastUpdatedLabel: formatDate(profile?.lastReviewedAtUtc),
      actionLabel: "Revisar notificacoes",
      summary: "Notificacoes nao bloqueiam o fechamento da V5 no recorte atual.",
      evidenceLabel: "Follow-up do tenant pode ser conduzido inteiramente pelo backoffice persistido.",
      lastReviewedLabel: formatDate(profile?.lastReviewedAtUtc),
      reviewModeLabel: "Canais externos seguem opcionais e nao substituem rastreabilidade do sistema.",
      checklistItems: [
        "Acoes da Qualidade podem ser registradas sem dependencia de e-mail transacional.",
        "A trilha auditavel continua sendo a evidencia principal.",
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
      status: profile ? (profile.legalOpinionStatus.toLowerCase().includes("approved") ? "ready" : "attention") : "blocked",
      detail: profile
        ? `Parecer juridico: ${profile.legalOpinionStatus}. DPA: ${profile.dpaReference}.`
        : "Parecer juridico e DPA ainda nao materializados no tenant.",
      ownerLabel: "Legal",
      lastUpdatedLabel: formatDate(profile?.lastReviewedAtUtc),
      actionLabel: "Revisar LGPD",
      summary: "A V5 integra parecer juridico e referencia de DPA ao estado real da organizacao.",
      evidenceLabel: profile
        ? `${profile.legalOpinionReference} · ${profile.dpaReference}`
        : "Parecer e DPA pendentes no tenant.",
      lastReviewedLabel: formatDate(profile?.lastReviewedAtUtc),
      reviewModeLabel: "Governanca juridica permanece visivel e auditavel junto ao perfil regulatorio.",
      checklistItems: [
        `Status do parecer: ${profile?.legalOpinionStatus ?? "pendente"}.`,
        `Referencia do DPA: ${profile?.dpaReference ?? "pendente"}.`,
      ],
      blockers: profile ? [] : ["Parecer juridico e DPA nao foram materializados no tenant."],
      warnings:
        profile && !profile.legalOpinionStatus.toLowerCase().includes("approved")
          ? ["Parecer juridico ainda nao esta em estado aprovado."]
          : [],
      links: {
        auditTrailScenarioId: "recent-emission",
        workspaceScenarioId: "baseline-ready",
      },
    },
  ];

  const selectedSection =
    sections.find((section) => section.key === input.selectedSectionKey) ??
    sections.find((section) => section.key === "regulatory_profile") ??
    sections[0]!;

  const summaryStatus: SettingsStatus = sections.some((section) => section.status === "blocked")
    ? "blocked"
    : sections.some((section) => section.status === "attention")
      ? "attention"
      : "ready";

  const scenarios = [
    {
      id: "operational-ready" as const,
      label: "Configuracao operacional persistida",
      description: "A organizacao passa a expor perfil e governanca reais da V5 sem depender so de cenarios demonstrativos.",
    },
    {
      id: "renewal-attention" as const,
      label: "Governanca em acompanhamento",
      description: "O recorte destaca secoes reais do tenant que ainda pedem follow-up.",
    },
    {
      id: "profile-change-blocked" as const,
      label: "Mudanca regulatoria bloqueada",
      description: "O recorte fail-closed mostra quando o tenant ainda nao sustenta a governanca regulatoria requerida.",
    },
  ].map((scenario) => ({
    id: scenario.id,
    label: scenario.label,
    description: scenario.description,
    summary: {
      status: summaryStatus,
      organizationName: input.organizationName,
      organizationCode: profile?.organizationCode ?? input.organizationSlug.toUpperCase(),
      profileLabel: describeProfile(profile),
      accreditationLabel: describeAccreditation(profile),
      planLabel: profile?.planLabel ?? "Plano pendente",
      configuredSections: sections.filter((section) => section.status === "ready").length,
      attentionSections: sections.filter((section) => section.status === "attention").length,
      blockedSections: sections.filter((section) => section.status === "blocked").length,
      recommendedAction:
        summaryStatus === "blocked"
          ? "Regularizar perfil regulatorio e LGPD antes de liberar qualquer mudanca sensivel do tenant."
          : summaryStatus === "attention"
            ? "Fechar os pontos de follow-up real antes do rito final de release."
            : "Manter a governanca persistida e auditavel da V5 em revisao continua.",
      blockers: sections.flatMap((section) => section.blockers),
      warnings: sections.flatMap((section) => section.warnings),
    },
    selectedSectionKey: selectedSection.key,
    sections: sections.map(({ summary, evidenceLabel, lastReviewedLabel, reviewModeLabel, checklistItems, blockers, warnings, links, ...section }) => section),
    detail: {
      sectionKey: selectedSection.key,
      title: selectedSection.title,
      status: selectedSection.status,
      summary: selectedSection.summary,
      evidenceLabel: selectedSection.evidenceLabel,
      lastReviewedLabel: selectedSection.lastReviewedLabel,
      reviewModeLabel: selectedSection.reviewModeLabel,
      checklistItems: selectedSection.checklistItems,
      blockers: selectedSection.blockers,
      warnings: selectedSection.warnings,
      links: selectedSection.links,
    },
  }));

  return {
    selectedScenarioId:
      summaryStatus === "blocked"
        ? "profile-change-blocked"
        : summaryStatus === "attention"
          ? "renewal-attention"
          : "operational-ready",
    scenarios,
  };
}

function formatDate(value?: string) {
  if (!value) {
    return "Sem revisao registrada";
  }

  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(new Date(value));
}

function describeProfile(profile?: PersistedComplianceProfileRecord | null) {
  if (!profile) {
    return "Perfil pendente";
  }

  switch (profile.regulatoryProfile) {
    case "type_a":
      return "Tipo A - RBC acreditado";
    case "type_c":
      return "Tipo C - nao acreditado";
    case "type_b":
    default:
      return "Tipo B - rastreavel";
  }
}

function describeAccreditation(profile?: PersistedComplianceProfileRecord | null) {
  if (!profile?.accreditationNumber) {
    return "Acreditacao pendente";
  }

  const validUntil = profile.accreditationValidUntilUtc
    ? new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeZone: "UTC" }).format(
        new Date(profile.accreditationValidUntilUtc),
      )
    : "sem validade registrada";

  return `${profile.accreditationNumber} valida ate ${validUntil}`;
}
