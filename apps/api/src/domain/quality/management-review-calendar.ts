import type { ManagementReviewCalendar, RegistryOperationalStatus } from "@afere/contracts";

export type ManagementReviewCalendarMeeting = {
  meetingId: string;
  titleLabel: string;
  status: RegistryOperationalStatus;
  scheduledForUtc: string;
  noticeLabel: string;
  chairLabel: string;
  attendeesLabel: string;
  periodLabel: string;
  outcomeLabel?: string;
  evidenceLabel?: string;
};

export function buildManagementReviewCalendar(input: {
  meetings: ManagementReviewCalendarMeeting[];
  scenarioId?: string;
  nowUtc?: string;
}): ManagementReviewCalendar {
  const ordered = [...input.meetings].sort((left, right) => left.scheduledForUtc.localeCompare(right.scheduledForUtc));
  const nextMeeting = selectNextMeeting(ordered, input.nowUtc ?? new Date().toISOString()) ?? ordered[0];

  if (!nextMeeting) {
    throw new Error("missing_management_review_calendar_meetings");
  }

  return {
    timezoneLabel: "UTC",
    nextScheduledLabel: formatManagementReviewSchedule(nextMeeting.scheduledForUtc),
    entries: ordered.map((meeting) => ({
      meetingId: meeting.meetingId,
      titleLabel: meeting.titleLabel,
      scheduledForLabel: formatManagementReviewSchedule(meeting.scheduledForUtc),
      status: meeting.status,
      exportHref: buildManagementReviewCalendarExportHref({
        meetingId: meeting.meetingId,
        scenarioId: input.scenarioId,
      }),
    })),
  };
}

export function buildManagementReviewCalendarExportHref(input: {
  meetingId: string;
  scenarioId?: string;
}) {
  const params = new URLSearchParams({ meeting: input.meetingId });
  if (input.scenarioId) {
    params.set("scenario", input.scenarioId);
  }

  return `/quality/management-review/calendar.ics?${params.toString()}`;
}

export function buildManagementReviewCalendarIcs(input: {
  meeting: ManagementReviewCalendarMeeting;
  generatedAtUtc?: string;
}) {
  const generatedAtUtc = input.generatedAtUtc ?? new Date().toISOString();
  const startsAt = input.meeting.scheduledForUtc;
  const endsAt = new Date(Date.parse(startsAt) + 60 * 60 * 1000).toISOString();
  const description = [
    input.meeting.noticeLabel,
    `Periodo: ${input.meeting.periodLabel}`,
    `Presidencia: ${input.meeting.chairLabel}`,
    `Participantes: ${input.meeting.attendeesLabel}`,
    input.meeting.outcomeLabel ? `Resultado esperado: ${input.meeting.outcomeLabel}` : undefined,
    input.meeting.evidenceLabel ? `Evidencia: ${input.meeting.evidenceLabel}` : undefined,
  ]
    .filter((line): line is string => Boolean(line))
    .join("\n");

  const lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Afere//Management Review//PT-BR",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    "BEGIN:VEVENT",
    `UID:management-review-${escapeIcsText(input.meeting.meetingId)}@afere.local`,
    `DTSTAMP:${toIcsUtc(generatedAtUtc)}`,
    `DTSTART:${toIcsUtc(startsAt)}`,
    `DTEND:${toIcsUtc(endsAt)}`,
    `SUMMARY:${escapeIcsText(input.meeting.titleLabel)}`,
    `DESCRIPTION:${escapeIcsText(description)}`,
    `CATEGORIES:${escapeIcsText(`analise-critica,${input.meeting.status}`)}`,
    "END:VEVENT",
    "END:VCALENDAR",
  ];

  return `${lines.map(foldIcsLine).join("\r\n")}\r\n`;
}

export function formatManagementReviewSchedule(value: string) {
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(new Date(value));
}

function selectNextMeeting(
  meetings: ManagementReviewCalendarMeeting[],
  nowUtc: string,
) {
  return meetings.find((meeting) => meeting.scheduledForUtc >= nowUtc) ?? meetings[meetings.length - 1];
}

function toIcsUtc(value: string) {
  return value.replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
}

function escapeIcsText(value: string) {
  return value
    .replace(/\\/g, "\\\\")
    .replace(/\r?\n/g, "\\n")
    .replace(/;/g, "\\;")
    .replace(/,/g, "\\,");
}

function foldIcsLine(line: string) {
  const maxLength = 72;
  if (line.length <= maxLength) {
    return line;
  }

  const chunks: string[] = [];
  let cursor = 0;
  while (cursor < line.length) {
    const part = line.slice(cursor, cursor + maxLength);
    chunks.push(cursor === 0 ? part : ` ${part}`);
    cursor += maxLength;
  }

  return chunks.join("\r\n");
}
