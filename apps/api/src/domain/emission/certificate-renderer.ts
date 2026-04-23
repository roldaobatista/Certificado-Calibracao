import { createHash } from "node:crypto";

import type { EmissionDryRunProfile, EmissionDryRunResult } from "@afere/contracts";

import type { RunCertificateEmissionDryRunInput } from "./dry-run.js";

export const CERTIFICATE_RENDERER_ID = "deterministic-pdf-v1";
export const CERTIFICATE_PDFA_STATUS = "pending_external_validation";

export type CertificatePdfaStatus = typeof CERTIFICATE_PDFA_STATUS;

export type RenderCertificateDocumentInput = {
  snapshotId: string;
  label: string;
  description: string;
  input: RunCertificateEmissionDryRunInput;
  result: EmissionDryRunResult;
};

export type RenderedCertificateDocument = {
  renderer: typeof CERTIFICATE_RENDERER_ID;
  pdfaStatus: CertificatePdfaStatus;
  profile: EmissionDryRunProfile;
  fileName: string;
  lines: string[];
  bytes: Buffer;
  sha256: string;
};

export function renderCertificateDocument(
  input: RenderCertificateDocumentInput,
): RenderedCertificateDocument {
  const lines = buildCertificateDocumentLines(input);
  const fileName = `${slugify(input.snapshotId)}.pdf`;
  const bytes = buildPdfDocument(lines, {
    title: `Certificado canonico ${input.snapshotId}`,
    subject: input.description,
    author: "Aferê",
    keywords: `afere,certificate,${input.result.profile},${input.snapshotId}`,
  });

  return {
    renderer: CERTIFICATE_RENDERER_ID,
    pdfaStatus: CERTIFICATE_PDFA_STATUS,
    profile: input.result.profile,
    fileName,
    lines,
    bytes,
    sha256: createHash("sha256").update(bytes).digest("hex"),
  };
}

export function buildCertificateDocumentLines(input: RenderCertificateDocumentInput): string[] {
  const { result } = input;
  const certificateNumber = result.artifacts.certificateNumber ?? "NUMERACAO-PENDENTE";
  const organizationName = input.input.organization.displayName ?? input.input.organization.organizationCode;
  const customerName = input.input.equipment.customerName ?? input.input.equipment.customerId ?? "CLIENTE-PENDENTE";
  const address = formatAddress(input.input.equipment.address);
  const instrumentLabel = compactValues([
    input.input.equipment.instrumentDescription,
    input.input.equipment.manufacturer,
    input.input.equipment.model,
    input.input.equipment.serialNumber,
  ]).join(" | ");
  const headerStatus = result.status === "ready" ? "PRONTO PARA ASSINATURA" : "BLOQUEADO ANTES DA ASSINATURA";
  const lines = [
    "AFERE - CERTIFICADO CANONICO DE CALIBRACAO",
    `SNAPSHOT: ${input.snapshotId}`,
    `CENARIO: ${input.label}`,
    `STATUS: ${headerStatus}`,
    `PERFIL REGULATORIO: TIPO ${result.profile}`,
    `RENDERER: ${CERTIFICATE_RENDERER_ID}`,
    `PDFA STATUS: ${CERTIFICATE_PDFA_STATUS}`,
    "",
    "EMISSOR",
    `Organizacao: ${organizationName}`,
    `Codigo: ${input.input.organization.organizationCode}`,
    `Certificado: ${certificateNumber}`,
    `Revisao: ${input.input.certificate.revision}`,
    "",
    "IDENTIFICACAO",
    `Cliente: ${customerName}`,
    `Endereco: ${address}`,
    `Equipamento: ${instrumentLabel}`,
    `TAG: ${input.input.equipment.tagCode ?? "NAO INFORMADA"}`,
    "",
    "PADROES E RASTREABILIDADE",
    `Fonte do padrao: ${input.input.standard.source}`,
    `Conjunto: ${input.input.standard.standardSetLabel ?? "NAO INFORMADO"}`,
    `Certificado do padrao: ${input.input.standard.certificateReference ?? "NAO INFORMADO"}`,
    `Validade do padrao: ${input.input.standard.certificateValidUntil ?? "NAO INFORMADA"}`,
    "",
    "RESULTADOS",
    `Resultado: ${formatNumber(input.input.measurement.resultValue, input.input.measurement.unit)}`,
    `Incerteza expandida: ${formatNumber(input.input.measurement.expandedUncertaintyValue, input.input.measurement.unit)}`,
    `Fator de abrangencia: k=${input.input.measurement.coverageFactor}`,
    `Declaracao tecnica: ${result.artifacts.declarationSummary ?? "INDISPONIVEL"}`,
    "",
    "DECISAO E PUBLICACAO",
    `Politica de simbolo: ${result.artifacts.symbolPolicy}`,
    `Template: ${result.artifacts.templateId}`,
    `QR publico: ${result.artifacts.qrCodeUrl ?? "INDISPONIVEL"}`,
    `QR status: ${result.artifacts.qrVerificationStatus ?? "PENDENTE"}`,
    `Assinatura prevista: ${input.input.audit.signedAtUtc}`,
    `Emissao prevista: ${input.input.audit.emittedAtUtc}`,
  ];

  if (input.input.decision?.requested) {
    lines.push(`Regra de decisao: ${input.input.decision.ruleLabel ?? "NAO INFORMADA"}`);
    lines.push(`Resultado da decisao: ${input.input.decision.outcomeLabel ?? "PENDENTE"}`);
  }

  if (input.input.notes && input.input.notes.length > 0) {
    lines.push("");
    lines.push("OBSERVACOES");
    for (const note of input.input.notes) {
      lines.push(`- ${note}`);
    }
  }

  if (result.warnings.length > 0) {
    lines.push("");
    lines.push("WARNINGS");
    for (const warning of result.warnings) {
      lines.push(`- ${warning}`);
    }
  }

  if (result.blockers.length > 0) {
    lines.push("");
    lines.push("BLOQUEIOS");
    for (const blocker of result.blockers) {
      lines.push(`- ${blocker}`);
    }
  }

  lines.push("");
  lines.push("CHECKLIST DE EMISSAO");
  for (const check of result.checks) {
    lines.push(`- [${check.status.toUpperCase()}] ${check.title}: ${check.detail}`);
  }

  lines.push("");
  lines.push(
    "NOTA REGULATORIA: artefato deterministico para regressao canônica. A conformidade PDF/A formal depende de validacao externa e segue fail-closed.",
  );

  return lines.map(normalizeAsciiLine);
}

function buildPdfDocument(
  lines: string[],
  metadata: {
    title: string;
    subject: string;
    author: string;
    keywords: string;
  },
): Buffer {
  const pages = paginateLines(lines, 52);
  const objectBodies = new Map<number, string>();
  const fontObjectId = 3;
  let nextObjectId = 4;
  const pageObjectIds: number[] = [];

  objectBodies.set(1, "<< /Type /Catalog /Pages 2 0 R >>");
  objectBodies.set(3, "<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>");

  for (const pageLines of pages) {
    const contentObjectId = nextObjectId++;
    const pageObjectId = nextObjectId++;
    const stream = buildPageStream(pageLines);
    objectBodies.set(contentObjectId, `<< /Length ${Buffer.byteLength(stream, "binary")} >>\nstream\n${stream}\nendstream`);
    objectBodies.set(
      pageObjectId,
      `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 ${fontObjectId} 0 R >> >> /Contents ${contentObjectId} 0 R >>`,
    );
    pageObjectIds.push(pageObjectId);
  }

  objectBodies.set(2, `<< /Type /Pages /Count ${pageObjectIds.length} /Kids [${pageObjectIds.map((id) => `${id} 0 R`).join(" ")}] >>`);

  const infoObjectId = nextObjectId++;
  objectBodies.set(
    infoObjectId,
    `<< /Title (${escapePdfLiteral(metadata.title)}) /Subject (${escapePdfLiteral(metadata.subject)}) /Author (${escapePdfLiteral(
      metadata.author,
    )}) /Creator (${CERTIFICATE_RENDERER_ID}) /Producer (${CERTIFICATE_RENDERER_ID}) /Keywords (${escapePdfLiteral(
      metadata.keywords,
    )}) /CreationDate (D:20260423000000Z) /ModDate (D:20260423000000Z) >>`,
  );

  let pdf = "%PDF-1.4\n%\xE2\xE3\xCF\xD3\n";
  const offsets: number[] = [0];
  for (let objectId = 1; objectId < nextObjectId; objectId += 1) {
    const body = objectBodies.get(objectId);
    if (!body) {
      throw new Error(`pdf_object_missing:${objectId}`);
    }
    offsets[objectId] = Buffer.byteLength(pdf, "binary");
    pdf += `${objectId} 0 obj\n${body}\nendobj\n`;
  }

  const startXref = Buffer.byteLength(pdf, "binary");
  pdf += `xref\n0 ${nextObjectId}\n`;
  pdf += "0000000000 65535 f \n";
  for (let objectId = 1; objectId < nextObjectId; objectId += 1) {
    pdf += `${String(offsets[objectId]).padStart(10, "0")} 00000 n \n`;
  }
  pdf += `trailer\n<< /Size ${nextObjectId} /Root 1 0 R /Info ${infoObjectId} 0 R >>\n`;
  pdf += `startxref\n${startXref}\n%%EOF\n`;

  return Buffer.from(pdf, "binary");
}

function buildPageStream(lines: string[]): string {
  const content = [
    "BT",
    "/F1 10 Tf",
    "12 TL",
    "48 794 Td",
    "0 g",
  ];

  lines.forEach((line, index) => {
    const escaped = escapePdfLiteral(line);
    if (index === 0) {
      content.push(`(${escaped}) Tj`);
      return;
    }
    content.push(`T* (${escaped}) Tj`);
  });

  content.push("ET");
  return content.join("\n");
}

function paginateLines(lines: string[], linesPerPage: number): string[][] {
  const normalized = lines.length === 0 ? ["DOCUMENTO VAZIO"] : lines;
  const pages: string[][] = [];
  for (let index = 0; index < normalized.length; index += linesPerPage) {
    pages.push(normalized.slice(index, index + linesPerPage));
  }
  return pages;
}

function formatAddress(address: RunCertificateEmissionDryRunInput["equipment"]["address"]): string {
  if (!address) {
    return "ENDERECO NAO INFORMADO";
  }

  return compactValues([
    address.line1,
    address.city,
    address.state,
    address.postalCode,
    address.country,
  ]).join(" | ");
}

function compactValues(values: Array<string | undefined>): string[] {
  return values.filter((value): value is string => typeof value === "string" && value.trim().length > 0);
}

function formatNumber(value: number, unit: string): string {
  if (!Number.isFinite(value)) {
    return `NAO INFORMADO ${unit}`.trim();
  }
  return `${trimTrailingZeros(value)} ${unit}`.trim();
}

function trimTrailingZeros(value: number): string {
  return value.toFixed(6).replace(/\.?0+$/, "");
}

function normalizeAsciiLine(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^\x20-\x7E]/g, " ")
    .replace(/\s+/g, " ")
    .trimEnd();
}

function escapePdfLiteral(value: string): string {
  return normalizeAsciiLine(value).replace(/\\/g, "\\\\").replace(/\(/g, "\\(").replace(/\)/g, "\\)");
}

function slugify(value: string): string {
  return normalizeAsciiLine(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}
