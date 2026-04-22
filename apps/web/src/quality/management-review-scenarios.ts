import type {
  ManagementReviewCatalog,
  ManagementReviewScenario,
} from "@afere/contracts";

export interface ManagementReviewScenarioViewModel extends ManagementReviewScenario {
  selectedMeeting: ManagementReviewScenario["meetings"][number];
  summaryLabel: string;
}

export interface ManagementReviewCatalogViewModel {
  selectedScenario: ManagementReviewScenarioViewModel;
  scenarios: ManagementReviewScenarioViewModel[];
}

export function buildManagementReviewCatalogView(
  catalog: ManagementReviewCatalog,
): ManagementReviewCatalogViewModel {
  const scenarios = catalog.scenarios.map((scenario) => {
    const selectedMeeting =
      scenario.meetings.find((meeting) => meeting.meetingId === scenario.selectedMeetingId) ??
      scenario.meetings[0];

    if (!selectedMeeting) {
      throw new Error("missing_management_review_meetings");
    }

    return {
      ...scenario,
      selectedMeeting,
      summaryLabel:
        scenario.summary.status === "ready"
          ? "Ata arquivada e sem decisao aberta"
          : scenario.summary.status === "attention"
            ? `${scenario.summary.openDecisionCount} decisao(oes) pendente(s) na pauta`
            : "Reuniao extraordinaria obrigatoria",
    };
  });

  const selectedScenario =
    scenarios.find((scenario) => scenario.id === catalog.selectedScenarioId) ??
    scenarios[0];

  if (!selectedScenario) {
    throw new Error("missing_management_review_scenarios");
  }

  return {
    selectedScenario,
    scenarios,
  };
}
