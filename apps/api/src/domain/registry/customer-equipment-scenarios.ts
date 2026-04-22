import type {
  CustomerAddress,
  CustomerAttachment,
  CustomerCertificateHighlight,
  CustomerContact,
  CustomerDetail,
  CustomerHistoryItem,
  CustomerListItem,
  CustomerRegistryCatalog,
  CustomerRegistryScenario,
  EmissionDryRunScenarioId,
  EquipmentDetail,
  EquipmentListItem,
  EquipmentRegistryCatalog,
  EquipmentRegistryScenario,
  RegistryOperationalStatus,
  RegistryScenarioId,
  ServiceOrderReviewScenarioId,
} from "@afere/contracts";

import type { EquipmentRegistrationInput } from "../equipment/equipment-registration.js";
import { validateEquipmentRegistration } from "../equipment/equipment-registration.js";

type CustomerRecord = {
  customerId: string;
  legalName: string;
  tradeName: string;
  documentLabel: string;
  segmentLabel: string;
  equipmentCount: number;
  accountOwnerLabel: string;
  contractLabel: string;
  specialConditionsLabel: string;
  contacts: CustomerContact[];
  addresses: CustomerAddress[];
  certificateHighlights: CustomerCertificateHighlight[];
  attachments: CustomerAttachment[];
  history: CustomerHistoryItem[];
  equipmentHighlightIds: string[];
  defaultServiceOrderScenarioId?: ServiceOrderReviewScenarioId;
  defaultReviewItemId?: string;
  defaultDryRunScenarioId?: EmissionDryRunScenarioId;
};

type EquipmentRecord = {
  equipmentId: string;
  customerId: string;
  code: string;
  tagCode: string;
  serialNumber: string;
  typeModelLabel: string;
  capacityClassLabel: string;
  registrationInput: EquipmentRegistrationInput;
  addressLabel: string;
  standardSetLabel: string;
  lastServiceOrderLabel: string;
  defaultDryRunScenarioId?: EmissionDryRunScenarioId;
  defaultServiceOrderScenarioId?: ServiceOrderReviewScenarioId;
  defaultReviewItemId?: string;
};

type ScenarioCustomerState = {
  customerId: string;
  certificatesThisMonth: number;
  nextDueLabel: string;
  status: RegistryOperationalStatus;
  blockers: string[];
  warnings: string[];
};

type ScenarioEquipmentState = {
  equipmentId: string;
  lastCalibrationLabel: string;
  nextCalibrationLabel: string;
  dueSoon: boolean;
  blockers: string[];
  warnings: string[];
};

type RegistryScenarioDefinition = {
  label: string;
  description: string;
  recommendedAction: string;
  selectedCustomerId: string;
  selectedEquipmentId: string;
  customers: ScenarioCustomerState[];
  equipments: ScenarioEquipmentState[];
};

const CUSTOMER_RECORDS: Record<string, CustomerRecord> = {
  "customer-001": {
    customerId: "customer-001",
    legalName: "Lab. Acme Analises Ltda.",
    tradeName: "Lab. Acme",
    documentLabel: "12.345.678/0001-XX",
    segmentLabel: "Laboratorio clinico",
    equipmentCount: 23,
    accountOwnerLabel: "Joao das Neves (joao@lab-acme.com.br)",
    contractLabel: "Contrato vigente ate 31/12/2026",
    specialConditionsLabel: "Sala climatizada 21+/-2 C, restricao de acesso",
    contacts: [
      {
        name: "Joao das Neves",
        roleLabel: "Responsavel tecnico",
        email: "joao@lab-acme.com.br",
        phoneLabel: "(65) 99999-0001",
        primary: true,
      },
      {
        name: "Ana Operacoes",
        roleLabel: "Coordenadora operacional",
        email: "ana@lab-acme.com.br",
        phoneLabel: "(65) 99999-0002",
        primary: false,
      },
    ],
    addresses: [
      {
        label: "Matriz",
        line1: "Rua da Calibracao, 100",
        cityStateLabel: "Cuiaba / MT",
        postalCodeLabel: "78000-000",
        countryLabel: "Brasil",
        conditionsLabel: "Sala climatizada 21+/-2 C, acesso controlado.",
      },
    ],
    certificateHighlights: [
      {
        certificateNumber: "AFR-000124",
        workOrderNumber: "OS-2026-00142",
        issuedAtLabel: "22/04/2026",
        revisionLabel: "R0",
        statusLabel: "Emitido",
      },
      {
        certificateNumber: "AFR-000123",
        workOrderNumber: "OS-2026-00139",
        issuedAtLabel: "21/04/2026",
        revisionLabel: "R0",
        statusLabel: "Emitido",
      },
    ],
    attachments: [
      { label: "Contrato master", statusLabel: "Vigente" },
      { label: "DPA LGPD", statusLabel: "Assinado" },
    ],
    history: [
      { label: "Cliente revisado no onboarding", timestampLabel: "12/04 08:30" },
      { label: "Ultima emissao concluida sem ressalvas", timestampLabel: "22/04 13:45" },
    ],
    equipmentHighlightIds: ["equipment-001", "equipment-005"],
    defaultServiceOrderScenarioId: "review-ready",
    defaultReviewItemId: "os-2026-00142",
    defaultDryRunScenarioId: "type-b-ready",
  },
  "customer-002": {
    customerId: "customer-002",
    legalName: "Padaria Pao Doce Comercio Ltda.",
    tradeName: "Padaria Pao Doce",
    documentLabel: "23.456.789/0001-YY",
    segmentLabel: "Panificacao",
    equipmentCount: 4,
    accountOwnerLabel: "Marcia Lima (marcia@paodoce.com.br)",
    contractLabel: "Contrato vigente ate 30/11/2026",
    specialConditionsLabel: "Atendimento antes da abertura da loja",
    contacts: [
      {
        name: "Marcia Lima",
        roleLabel: "Responsavel administrativa",
        email: "marcia@paodoce.com.br",
        phoneLabel: "(65) 99999-1101",
        primary: true,
      },
    ],
    addresses: [
      {
        label: "Loja principal",
        line1: "Avenida do Comercio, 45",
        cityStateLabel: "Cuiaba / MT",
        postalCodeLabel: "78005-010",
        countryLabel: "Brasil",
        conditionsLabel: "Afericao antes das 6h para nao interromper a producao.",
      },
    ],
    certificateHighlights: [
      {
        certificateNumber: "AFR-000118",
        workOrderNumber: "OS-2026-00135",
        issuedAtLabel: "17/04/2026",
        revisionLabel: "R0",
        statusLabel: "Aguardando assinatura",
      },
    ],
    attachments: [
      { label: "Checklist de acesso ao local", statusLabel: "Atualizado" },
      { label: "Contrato comercial", statusLabel: "Vigente" },
    ],
    history: [
      { label: "Cliente ativado para operacao assistida", timestampLabel: "10/04 15:10" },
      { label: "Endereco revisado pelo back-office", timestampLabel: "18/04 09:20" },
    ],
    equipmentHighlightIds: ["equipment-002"],
    defaultServiceOrderScenarioId: "review-ready",
    defaultReviewItemId: "os-2026-00135",
    defaultDryRunScenarioId: "type-b-ready",
  },
  "customer-003": {
    customerId: "customer-003",
    legalName: "Industria XYZ Alimentos S.A.",
    tradeName: "Industria XYZ",
    documentLabel: "34.567.890/0001-ZZ",
    segmentLabel: "Industria alimenticia",
    equipmentCount: 67,
    accountOwnerLabel: "Carlos Mendes (carlos@xyz.com.br)",
    contractLabel: "Contrato vigente ate 30/09/2026",
    specialConditionsLabel: "Janela operacional entre 22h e 4h para linhas criticas",
    contacts: [
      {
        name: "Carlos Mendes",
        roleLabel: "Coordenador de manutencao",
        email: "carlos@xyz.com.br",
        phoneLabel: "(65) 99999-2201",
        primary: true,
      },
      {
        name: "Fernanda Qualidade",
        roleLabel: "Controle de qualidade",
        email: "fernanda@xyz.com.br",
        phoneLabel: "(65) 99999-2202",
        primary: false,
      },
    ],
    addresses: [
      {
        label: "Planta industrial",
        line1: "Distrito Industrial, 2200",
        cityStateLabel: "Varzea Grande / MT",
        postalCodeLabel: "78110-500",
        countryLabel: "Brasil",
        conditionsLabel: "Acesso controlado e EPIs obrigatorios.",
      },
    ],
    certificateHighlights: [
      {
        certificateNumber: "XYZ-000218",
        workOrderNumber: "OS-2026-00141",
        issuedAtLabel: "Pendente",
        revisionLabel: "R0",
        statusLabel: "Revisao em atencao",
      },
    ],
    attachments: [
      { label: "Contrato comercial", statusLabel: "Vigente" },
      { label: "Anexo de seguranca operacional", statusLabel: "Assinado" },
    ],
    history: [
      { label: "Cliente migrado da planilha legada", timestampLabel: "08/04 11:40" },
      { label: "Ultima visita teve vencimento proximo sinalizado", timestampLabel: "19/04 14:05" },
    ],
    equipmentHighlightIds: ["equipment-003"],
    defaultServiceOrderScenarioId: "history-pending",
    defaultReviewItemId: "os-2026-00141",
    defaultDryRunScenarioId: "type-b-ready",
  },
  "customer-004": {
    customerId: "customer-004",
    legalName: "Cliente sem cadastro completo",
    tradeName: "Cadastro pendente",
    documentLabel: "CNPJ pendente",
    segmentLabel: "Homologacao",
    equipmentCount: 1,
    accountOwnerLabel: "Responsavel nao confirmado",
    contractLabel: "Contrato aguardando formalizacao",
    specialConditionsLabel: "Endereco do equipamento ainda nao validado",
    contacts: [
      {
        name: "Contato nao confirmado",
        roleLabel: "Ponto focal pendente",
        email: "pendente@cliente.local",
        primary: true,
      },
    ],
    addresses: [
      {
        label: "Endereco em validacao",
        line1: "Rua Sem CEP, 10",
        cityStateLabel: "Campo Grande / MS",
        postalCodeLabel: "CEP pendente",
        countryLabel: "Brasil",
        conditionsLabel: "Confirmacao documental em aberto.",
      },
    ],
    certificateHighlights: [
      {
        certificateNumber: "Sem numeracao",
        workOrderNumber: "OS-2026-00147",
        issuedAtLabel: "Pendente",
        revisionLabel: "R0",
        statusLabel: "Bloqueado",
      },
    ],
    attachments: [
      { label: "Checklist cadastral", statusLabel: "Pendente" },
      { label: "Contrato comercial", statusLabel: "Nao recebido" },
    ],
    history: [
      { label: "Cliente aberto para homologacao assistida", timestampLabel: "19/04 08:10" },
      { label: "Cadastro travado por endereco incompleto", timestampLabel: "19/04 10:15" },
    ],
    equipmentHighlightIds: ["equipment-004"],
    defaultServiceOrderScenarioId: "review-blocked",
    defaultReviewItemId: "os-2026-00147",
    defaultDryRunScenarioId: "type-c-blocked",
  },
};

const EQUIPMENT_RECORDS: Record<string, EquipmentRecord> = {
  "equipment-001": {
    equipmentId: "equipment-001",
    customerId: "customer-001",
    code: "EQ-0007",
    tagCode: "BAL-007",
    serialNumber: "SN-300-01",
    typeModelLabel: "NAWI Toledo Prix 3",
    capacityClassLabel: "300 kg · 0,05 kg · III",
    registrationInput: {
      customerId: "customer-001",
      address: {
        line1: "Rua da Calibracao, 100",
        city: "Cuiaba",
        state: "MT",
        postalCode: "78000-000",
        country: "BR",
      },
    },
    addressLabel: "Rua da Calibracao, 100 · Cuiaba/MT · 78000-000",
    standardSetLabel: "PESO-001 / PESO-002 / TH-003",
    lastServiceOrderLabel: "OS-2026-00142 · 19/04",
    defaultDryRunScenarioId: "type-b-ready",
    defaultServiceOrderScenarioId: "review-ready",
    defaultReviewItemId: "os-2026-00142",
  },
  "equipment-005": {
    equipmentId: "equipment-005",
    customerId: "customer-001",
    code: "EQ-0012",
    tagCode: "BAL-012",
    serialNumber: "SN-300-12",
    typeModelLabel: "NAWI Toledo Prix 4",
    capacityClassLabel: "30 kg · 0,01 kg · III",
    registrationInput: {
      customerId: "customer-001",
      address: {
        line1: "Rua da Calibracao, 100",
        city: "Cuiaba",
        state: "MT",
        postalCode: "78000-000",
        country: "BR",
      },
    },
    addressLabel: "Rua da Calibracao, 100 · Cuiaba/MT · 78000-000",
    standardSetLabel: "PESO-004 / TH-003",
    lastServiceOrderLabel: "OS-2026-00139 · 18/04",
    defaultDryRunScenarioId: "type-b-ready",
    defaultServiceOrderScenarioId: "review-ready",
    defaultReviewItemId: "os-2026-00139",
  },
  "equipment-002": {
    equipmentId: "equipment-002",
    customerId: "customer-002",
    code: "EQ-0011",
    tagCode: "PAD-011",
    serialNumber: "SN-PD-011",
    typeModelLabel: "NAWI Urano Pop 30",
    capacityClassLabel: "30 kg · 0,01 kg · III",
    registrationInput: {
      customerId: "customer-002",
      address: {
        line1: "Avenida do Comercio, 45",
        city: "Cuiaba",
        state: "MT",
        postalCode: "78005-010",
        country: "BR",
      },
    },
    addressLabel: "Avenida do Comercio, 45 · Cuiaba/MT · 78005-010",
    standardSetLabel: "PESO-011 / TH-002",
    lastServiceOrderLabel: "OS-2026-00135 · 17/04",
    defaultDryRunScenarioId: "type-b-ready",
    defaultServiceOrderScenarioId: "review-ready",
    defaultReviewItemId: "os-2026-00135",
  },
  "equipment-003": {
    equipmentId: "equipment-003",
    customerId: "customer-003",
    code: "EQ-0008",
    tagCode: "BL-X-22",
    serialNumber: "SN-XY-22",
    typeModelLabel: "NAWI Marte L50",
    capacityClassLabel: "50 kg · 0,005 kg · III",
    registrationInput: {
      customerId: "customer-003",
      address: {
        line1: "Distrito Industrial, 2200",
        city: "Varzea Grande",
        state: "MT",
        postalCode: "78110-500",
        country: "BR",
      },
    },
    addressLabel: "Distrito Industrial, 2200 · Varzea Grande/MT · 78110-500",
    standardSetLabel: "PESO-021 / TH-010",
    lastServiceOrderLabel: "OS-2026-00141 · 19/04",
    defaultDryRunScenarioId: "type-b-ready",
    defaultServiceOrderScenarioId: "history-pending",
    defaultReviewItemId: "os-2026-00141",
  },
  "equipment-004": {
    equipmentId: "equipment-004",
    customerId: "customer-004",
    code: "EQ-0404",
    tagCode: "BAL-404",
    serialNumber: "SN-C-500",
    typeModelLabel: "Balanca plataforma Marte 500",
    capacityClassLabel: "500 kg · 0,1 kg · III",
    registrationInput: {
      customerId: "customer-004",
      address: {
        line1: "Rua Sem CEP, 10",
        city: "Campo Grande",
        state: "MS",
        country: "BR",
      },
    },
    addressLabel: "Rua Sem CEP, 10 · Campo Grande/MS · CEP pendente",
    standardSetLabel: "PESO-009 / TH-404",
    lastServiceOrderLabel: "OS-2026-00147 · 19/04",
    defaultDryRunScenarioId: "type-c-blocked",
    defaultServiceOrderScenarioId: "review-blocked",
    defaultReviewItemId: "os-2026-00147",
  },
};

const SCENARIOS: Record<RegistryScenarioId, RegistryScenarioDefinition> = {
  "operational-ready": {
    label: "Clientes ativos e cadastros consistentes",
    description: "Recorte operacional com clientes ativos, detalhe coerente e equipamentos aptos a sustentar a emissao.",
    recommendedAction: "Seguir com a operacao normal e revisar apenas os proximos vencimentos planejados.",
    selectedCustomerId: "customer-001",
    selectedEquipmentId: "equipment-001",
    customers: [
      {
        customerId: "customer-001",
        certificatesThisMonth: 15,
        nextDueLabel: "02/05/2026",
        status: "ready",
        blockers: [],
        warnings: [],
      },
      {
        customerId: "customer-002",
        certificatesThisMonth: 2,
        nextDueLabel: "18/05/2026",
        status: "ready",
        blockers: [],
        warnings: [],
      },
      {
        customerId: "customer-003",
        certificatesThisMonth: 8,
        nextDueLabel: "23/06/2026",
        status: "ready",
        blockers: [],
        warnings: [],
      },
    ],
    equipments: [
      {
        equipmentId: "equipment-001",
        lastCalibrationLabel: "18/04/2026",
        nextCalibrationLabel: "18/10/2026",
        dueSoon: false,
        blockers: [],
        warnings: [],
      },
      {
        equipmentId: "equipment-005",
        lastCalibrationLabel: "18/04/2026",
        nextCalibrationLabel: "18/10/2026",
        dueSoon: false,
        blockers: [],
        warnings: [],
      },
      {
        equipmentId: "equipment-002",
        lastCalibrationLabel: "17/04/2026",
        nextCalibrationLabel: "17/10/2026",
        dueSoon: false,
        blockers: [],
        warnings: [],
      },
      {
        equipmentId: "equipment-003",
        lastCalibrationLabel: "02/03/2026",
        nextCalibrationLabel: "02/09/2026",
        dueSoon: false,
        blockers: [],
        warnings: [],
      },
    ],
  },
  "certificate-attention": {
    label: "Cliente com vencimento proximo",
    description: "Recorte com cliente e equipamento em atencao por proxima calibracao iminente, sem bloqueio cadastral.",
    recommendedAction: "Planejar a janela de recalibracao do cliente selecionado antes do vencimento sinalizado.",
    selectedCustomerId: "customer-003",
    selectedEquipmentId: "equipment-003",
    customers: [
      {
        customerId: "customer-001",
        certificatesThisMonth: 15,
        nextDueLabel: "02/05/2026",
        status: "ready",
        blockers: [],
        warnings: [],
      },
      {
        customerId: "customer-002",
        certificatesThisMonth: 2,
        nextDueLabel: "18/05/2026",
        status: "ready",
        blockers: [],
        warnings: [],
      },
      {
        customerId: "customer-003",
        certificatesThisMonth: 8,
        nextDueLabel: "23/04/2026 ⚠",
        status: "attention",
        blockers: [],
        warnings: ["Cliente com proxima calibracao critica nas proximas 24 horas."],
      },
    ],
    equipments: [
      {
        equipmentId: "equipment-001",
        lastCalibrationLabel: "18/04/2026",
        nextCalibrationLabel: "18/10/2026",
        dueSoon: false,
        blockers: [],
        warnings: [],
      },
      {
        equipmentId: "equipment-005",
        lastCalibrationLabel: "18/04/2026",
        nextCalibrationLabel: "18/10/2026",
        dueSoon: false,
        blockers: [],
        warnings: [],
      },
      {
        equipmentId: "equipment-002",
        lastCalibrationLabel: "17/04/2026",
        nextCalibrationLabel: "17/10/2026",
        dueSoon: false,
        blockers: [],
        warnings: [],
      },
      {
        equipmentId: "equipment-003",
        lastCalibrationLabel: "02/03/2026",
        nextCalibrationLabel: "02/05/2026 ⚠",
        dueSoon: true,
        blockers: [],
        warnings: ["Equipamento entra na janela critica de vencimento nos proximos 10 dias."],
      },
    ],
  },
  "registration-blocked": {
    label: "Cadastro bloqueado por equipamento incompleto",
    description: "Recorte com equipamento principal sem endereco minimo completo e cliente ainda em homologacao cadastral.",
    recommendedAction: "Completar endereco e formalizacao cadastral antes de liberar novas OS para o cliente selecionado.",
    selectedCustomerId: "customer-004",
    selectedEquipmentId: "equipment-004",
    customers: [
      {
        customerId: "customer-001",
        certificatesThisMonth: 15,
        nextDueLabel: "02/05/2026",
        status: "ready",
        blockers: [],
        warnings: [],
      },
      {
        customerId: "customer-002",
        certificatesThisMonth: 2,
        nextDueLabel: "18/05/2026",
        status: "ready",
        blockers: [],
        warnings: [],
      },
      {
        customerId: "customer-003",
        certificatesThisMonth: 8,
        nextDueLabel: "23/06/2026",
        status: "ready",
        blockers: [],
        warnings: [],
      },
      {
        customerId: "customer-004",
        certificatesThisMonth: 0,
        nextDueLabel: "Cadastro pendente",
        status: "blocked",
        blockers: ["Equipamento principal sem CEP validado no cadastro."],
        warnings: ["Contrato comercial e documento fiscal ainda nao foram anexados."],
      },
    ],
    equipments: [
      {
        equipmentId: "equipment-001",
        lastCalibrationLabel: "18/04/2026",
        nextCalibrationLabel: "18/10/2026",
        dueSoon: false,
        blockers: [],
        warnings: [],
      },
      {
        equipmentId: "equipment-005",
        lastCalibrationLabel: "18/04/2026",
        nextCalibrationLabel: "18/10/2026",
        dueSoon: false,
        blockers: [],
        warnings: [],
      },
      {
        equipmentId: "equipment-002",
        lastCalibrationLabel: "17/04/2026",
        nextCalibrationLabel: "17/10/2026",
        dueSoon: false,
        blockers: [],
        warnings: [],
      },
      {
        equipmentId: "equipment-003",
        lastCalibrationLabel: "02/03/2026",
        nextCalibrationLabel: "02/09/2026",
        dueSoon: false,
        blockers: [],
        warnings: [],
      },
      {
        equipmentId: "equipment-004",
        lastCalibrationLabel: "19/04/2026",
        nextCalibrationLabel: "Cadastro pendente",
        dueSoon: false,
        blockers: ["Endereco minimo do equipamento continua incompleto para a emissao."],
        warnings: ["Cliente permanece em homologacao assistida."],
      },
    ],
  },
};

const DEFAULT_SCENARIO: RegistryScenarioId = "operational-ready";

export function listCustomerRegistryScenarios(): CustomerRegistryScenario[] {
  return (Object.keys(SCENARIOS) as RegistryScenarioId[]).map((scenarioId) =>
    resolveCustomerRegistryScenario(scenarioId),
  );
}

export function listEquipmentRegistryScenarios(): EquipmentRegistryScenario[] {
  return (Object.keys(SCENARIOS) as RegistryScenarioId[]).map((scenarioId) =>
    resolveEquipmentRegistryScenario(scenarioId),
  );
}

export function resolveCustomerRegistryScenario(
  scenarioId?: string,
  customerId?: string,
): CustomerRegistryScenario {
  const definition = SCENARIOS[isRegistryScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO];
  const customerStates = definition.customers.map(buildCustomerListItem);
  const selectedCustomer =
    customerStates.find((item) => item.customerId === customerId) ??
    customerStates.find((item) => item.customerId === definition.selectedCustomerId) ??
    customerStates[0];

  if (!selectedCustomer) {
    throw new Error("missing_customer_registry_customers");
  }

  const detail = buildCustomerDetail(definition, selectedCustomer.customerId);

  return {
    id: resolveScenarioId(scenarioId),
    label: definition.label,
    description: definition.description,
    summary: buildCustomerRegistrySummary(definition.recommendedAction, customerStates, detail),
    selectedCustomerId: selectedCustomer.customerId,
    customers: customerStates,
    detail,
  };
}

export function resolveEquipmentRegistryScenario(
  scenarioId?: string,
  equipmentId?: string,
): EquipmentRegistryScenario {
  const definition = SCENARIOS[isRegistryScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO];
  const equipmentItems = definition.equipments.map((state) => buildEquipmentListItem(definition, state));
  const selectedEquipment =
    equipmentItems.find((item) => item.equipmentId === equipmentId) ??
    equipmentItems.find((item) => item.equipmentId === definition.selectedEquipmentId) ??
    equipmentItems[0];

  if (!selectedEquipment) {
    throw new Error("missing_equipment_registry_items");
  }

  const detail = buildEquipmentDetail(definition, selectedEquipment.equipmentId);

  return {
    id: resolveScenarioId(scenarioId),
    label: definition.label,
    description: definition.description,
    summary: buildEquipmentRegistrySummary(definition.recommendedAction, equipmentItems, detail),
    selectedEquipmentId: selectedEquipment.equipmentId,
    items: equipmentItems,
    detail,
  };
}

export function buildCustomerRegistryCatalog(
  scenarioId?: string,
  customerId?: string,
): CustomerRegistryCatalog {
  const selectedScenario = resolveCustomerRegistryScenario(scenarioId, customerId);

  return {
    selectedScenarioId: selectedScenario.id,
    scenarios: listCustomerRegistryScenarios().map((scenario) =>
      scenario.id === selectedScenario.id ? selectedScenario : scenario,
    ),
  };
}

export function buildEquipmentRegistryCatalog(
  scenarioId?: string,
  equipmentId?: string,
): EquipmentRegistryCatalog {
  const selectedScenario = resolveEquipmentRegistryScenario(scenarioId, equipmentId);

  return {
    selectedScenarioId: selectedScenario.id,
    scenarios: listEquipmentRegistryScenarios().map((scenario) =>
      scenario.id === selectedScenario.id ? selectedScenario : scenario,
    ),
  };
}

function buildCustomerListItem(state: ScenarioCustomerState): CustomerListItem {
  const record = getCustomerRecord(state.customerId);

  return {
    customerId: record.customerId,
    legalName: record.legalName,
    tradeName: record.tradeName,
    documentLabel: record.documentLabel,
    segmentLabel: record.segmentLabel,
    equipmentCount: record.equipmentCount,
    certificatesThisMonth: state.certificatesThisMonth,
    nextDueLabel: state.nextDueLabel,
    status: state.status,
  };
}

function buildCustomerDetail(
  definition: RegistryScenarioDefinition,
  customerId: string,
): CustomerDetail {
  const record = getCustomerRecord(customerId);
  const state = getScenarioCustomerState(definition, customerId);
  const relatedEquipments = definition.equipments
    .map((equipmentState) => buildEquipmentListItem(definition, equipmentState))
    .filter((item) => item.customerId === customerId);
  const blockers = uniqueStrings([
    ...state.blockers,
    ...relatedEquipments.flatMap((item) =>
      item.status === "blocked" ? [`${item.code}: ${item.registrationStatusLabel}`] : [],
    ),
  ]);
  const warnings = uniqueStrings([
    ...state.warnings,
    ...relatedEquipments.flatMap((item) =>
      item.status === "attention" ? [`${item.code}: ${item.nextCalibrationLabel}`] : [],
    ),
  ]);
  const selectedEquipmentId = record.equipmentHighlightIds.find((equipmentId) =>
    relatedEquipments.some((item) => item.equipmentId === equipmentId),
  );

  return {
    customerId: record.customerId,
    title: `${record.tradeName} · ${record.documentLabel}`,
    status: state.status,
    statusLine: buildCustomerStatusLine(state.status, record.accountOwnerLabel),
    accountOwnerLabel: record.accountOwnerLabel,
    contractLabel: record.contractLabel,
    specialConditionsLabel: record.specialConditionsLabel,
    tabs: buildCustomerTabs(record, relatedEquipments.length),
    contacts: record.contacts,
    addresses: record.addresses,
    equipmentHighlights: relatedEquipments
      .filter((item) => record.equipmentHighlightIds.includes(item.equipmentId))
      .map((item) => ({
        equipmentId: item.equipmentId,
        code: item.code,
        tagCode: item.tagCode,
        typeModelLabel: item.typeModelLabel,
        nextDueLabel: item.nextCalibrationLabel,
        status: item.status,
      })),
    certificateHighlights: record.certificateHighlights,
    attachments: record.attachments,
    history: record.history,
    blockers,
    warnings,
    links: {
      equipmentScenarioId: resolveScenarioId(undefined, definition),
      selectedEquipmentId,
      serviceOrderScenarioId: record.defaultServiceOrderScenarioId,
      reviewItemId: record.defaultReviewItemId,
      dryRunScenarioId: record.defaultDryRunScenarioId,
    },
  };
}

function buildEquipmentListItem(
  definition: RegistryScenarioDefinition,
  state: ScenarioEquipmentState,
): EquipmentListItem {
  const record = getEquipmentRecord(state.equipmentId);
  const customer = getCustomerRecord(record.customerId);
  const validation = validateEquipmentRegistration(record.registrationInput);
  const blockers = uniqueStrings([
    ...state.blockers,
    ...(validation.ok ? [] : [`Campos ausentes: ${validation.missingFields.join(", ")}.`]),
  ]);
  const status = resolveEquipmentStatus(validation.ok, state.dueSoon, blockers.length > 0, state.warnings.length > 0);

  return {
    equipmentId: record.equipmentId,
    customerId: record.customerId,
    customerName: customer.tradeName,
    code: record.code,
    tagCode: record.tagCode,
    serialNumber: record.serialNumber,
    typeModelLabel: record.typeModelLabel,
    capacityClassLabel: record.capacityClassLabel,
    lastCalibrationLabel: state.lastCalibrationLabel,
    nextCalibrationLabel: state.nextCalibrationLabel,
    registrationStatusLabel: validation.ok
      ? "Cliente e endereco minimo validados."
      : `Cadastro incompleto: ${validation.missingFields.join(", ")}.`,
    status,
    missingFields: validation.missingFields,
    dryRunScenarioId: record.defaultDryRunScenarioId,
  };
}

function buildEquipmentDetail(
  definition: RegistryScenarioDefinition,
  equipmentId: string,
): EquipmentDetail {
  const state = getScenarioEquipmentState(definition, equipmentId);
  const record = getEquipmentRecord(equipmentId);
  const item = buildEquipmentListItem(definition, state);
  const customer = getCustomerRecord(record.customerId);
  const blockers = uniqueStrings([
    ...state.blockers,
    ...(item.missingFields.length > 0 ? [`Campos ausentes: ${item.missingFields.join(", ")}.`] : []),
  ]);
  const warnings = uniqueStrings(state.warnings);

  return {
    equipmentId: item.equipmentId,
    title: `${item.code} · ${item.tagCode} · ${item.typeModelLabel}`,
    status: item.status,
    statusLine: buildEquipmentStatusLine(item.status, customer.tradeName),
    customerLabel: customer.legalName,
    addressLabel: record.addressLabel,
    standardSetLabel: record.standardSetLabel,
    lastServiceOrderLabel: record.lastServiceOrderLabel,
    nextCalibrationLabel: item.nextCalibrationLabel,
    blockers,
    warnings,
    links: {
      customerScenarioId: resolveScenarioId(undefined, definition),
      customerId: customer.customerId,
      serviceOrderScenarioId: record.defaultServiceOrderScenarioId,
      reviewItemId: record.defaultReviewItemId,
      dryRunScenarioId: record.defaultDryRunScenarioId,
    },
  };
}

function buildCustomerRegistrySummary(
  recommendedAction: string,
  customers: CustomerListItem[],
  detail: CustomerDetail,
): CustomerRegistryScenario["summary"] {
  const readyCustomers = customers.filter((item) => item.status === "ready").length;
  const attentionCustomers = customers.filter((item) => item.status === "attention").length;
  const blockedCustomers = customers.filter((item) => item.status === "blocked").length;

  return {
    status: detail.status,
    headline:
      detail.status === "ready"
        ? "Cadastros de clientes prontos para sustentar a emissao"
        : detail.status === "attention"
          ? "Cliente com calendario operacional em atencao"
          : "Cadastro bloqueado por dado minimo ausente",
    activeCustomers: customers.length - blockedCustomers,
    attentionCustomers,
    blockedCustomers,
    totalEquipment: customers.reduce((sum, item) => sum + item.equipmentCount, 0),
    certificatesThisMonth: customers.reduce((sum, item) => sum + item.certificatesThisMonth, 0),
    dueSoonCount: customers.filter((item) => item.nextDueLabel.includes("⚠")).length,
    recommendedAction,
    blockers: detail.blockers,
    warnings: detail.warnings,
  };
}

function buildEquipmentRegistrySummary(
  recommendedAction: string,
  items: EquipmentListItem[],
  detail: EquipmentDetail,
): EquipmentRegistryScenario["summary"] {
  return {
    status: detail.status,
    headline:
      detail.status === "ready"
        ? "Equipamentos ativos e cadastros consistentes"
        : detail.status === "attention"
          ? "Equipamento exige acao preventiva antes do vencimento"
          : "Equipamento bloqueado por cadastro incompleto",
    totalEquipment: items.length,
    readyCount: items.filter((item) => item.status === "ready").length,
    attentionCount: items.filter((item) => item.status === "attention").length,
    blockedCount: items.filter((item) => item.status === "blocked").length,
    dueSoonCount: items.filter((item) => item.nextCalibrationLabel.includes("⚠")).length,
    recommendedAction,
    blockers: detail.blockers,
    warnings: detail.warnings,
  };
}

function buildCustomerTabs(
  record: CustomerRecord,
  relatedEquipmentCount: number,
): CustomerDetail["tabs"] {
  return [
    { key: "data", label: "Dados" },
    { key: "contacts", label: "Contatos", countLabel: String(record.contacts.length) },
    { key: "addresses", label: "Enderecos", countLabel: String(record.addresses.length) },
    { key: "equipment", label: "Equipamentos", countLabel: String(record.equipmentCount) },
    { key: "certificates", label: "Certificados", countLabel: String(record.certificateHighlights.length) },
    { key: "attachments", label: "Anexos", countLabel: String(record.attachments.length) },
    {
      key: "history",
      label: "Hist.",
      countLabel: String(Math.max(record.history.length, relatedEquipmentCount)),
    },
  ];
}

function resolveEquipmentStatus(
  registrationOk: boolean,
  dueSoon: boolean,
  hasBlockers: boolean,
  hasWarnings: boolean,
): RegistryOperationalStatus {
  if (!registrationOk || hasBlockers) {
    return "blocked";
  }

  if (dueSoon || hasWarnings) {
    return "attention";
  }

  return "ready";
}

function buildCustomerStatusLine(
  status: RegistryOperationalStatus,
  accountOwnerLabel: string,
): string {
  if (status === "blocked") {
    return `Cadastro bloqueado · Responsavel: ${accountOwnerLabel}`;
  }

  if (status === "attention") {
    return `Cliente em atencao operacional · Responsavel: ${accountOwnerLabel}`;
  }

  return `Cadastro pronto para sustentar a emissao · Responsavel: ${accountOwnerLabel}`;
}

function buildEquipmentStatusLine(
  status: RegistryOperationalStatus,
  customerLabel: string,
): string {
  if (status === "blocked") {
    return `Equipamento bloqueado por cadastro incompleto · Cliente: ${customerLabel}`;
  }

  if (status === "attention") {
    return `Equipamento exige acao preventiva de vencimento · Cliente: ${customerLabel}`;
  }

  return `Equipamento apto para emissao controlada · Cliente: ${customerLabel}`;
}

function resolveScenarioId(
  scenarioId?: string,
  definition?: RegistryScenarioDefinition,
): RegistryScenarioId {
  if (definition) {
    return (Object.keys(SCENARIOS) as RegistryScenarioId[]).find((id) => SCENARIOS[id] === definition) ?? DEFAULT_SCENARIO;
  }

  return isRegistryScenarioId(scenarioId) ? scenarioId : DEFAULT_SCENARIO;
}

function getCustomerRecord(customerId: string): CustomerRecord {
  const record = CUSTOMER_RECORDS[customerId];
  if (!record) {
    throw new Error(`missing_customer_record:${customerId}`);
  }

  return record;
}

function getEquipmentRecord(equipmentId: string): EquipmentRecord {
  const record = EQUIPMENT_RECORDS[equipmentId];
  if (!record) {
    throw new Error(`missing_equipment_record:${equipmentId}`);
  }

  return record;
}

function getScenarioCustomerState(
  definition: RegistryScenarioDefinition,
  customerId: string,
): ScenarioCustomerState {
  const state = definition.customers.find((item) => item.customerId === customerId);
  if (!state) {
    throw new Error(`missing_customer_state:${customerId}`);
  }

  return state;
}

function getScenarioEquipmentState(
  definition: RegistryScenarioDefinition,
  equipmentId: string,
): ScenarioEquipmentState {
  const state = definition.equipments.find((item) => item.equipmentId === equipmentId);
  if (!state) {
    throw new Error(`missing_equipment_state:${equipmentId}`);
  }

  return state;
}

function isRegistryScenarioId(value: string | undefined): value is RegistryScenarioId {
  return typeof value === "string" && value in SCENARIOS;
}

function uniqueStrings(values: string[]): string[] {
  return Array.from(new Set(values));
}
