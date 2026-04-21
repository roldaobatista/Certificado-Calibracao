import {
  offlineCalibrationSessionSchema,
  offlineCertificateDraftSchema,
  type OfflineCalibrationSession,
  type OfflineCertificateDraft,
} from "../../../packages/contracts/src/mobile-offline-calibration.js";

export interface CompleteMobileOfflineCalibrationResult {
  ok: boolean;
  reason?: "missing_required_data" | "technical_review_pending" | "signature_pending";
  certificateDraft?: OfflineCertificateDraft;
}

export function completeMobileOfflineCalibration(
  session: OfflineCalibrationSession,
): CompleteMobileOfflineCalibrationResult {
  const parsedSession = offlineCalibrationSessionSchema.safeParse(session);
  if (!parsedSession.success) {
    return { ok: false, reason: "missing_required_data" };
  }

  if (!parsedSession.data.technicalReviewCompleted) {
    return { ok: false, reason: "technical_review_pending" };
  }

  if (!parsedSession.data.certificateSignedOnDevice) {
    return { ok: false, reason: "signature_pending" };
  }

  const certificateDraft = offlineCertificateDraftSchema.parse({
    sessionId: parsedSession.data.sessionId,
    workOrderId: parsedSession.data.workOrderId,
    certificateNumber: parsedSession.data.reservedCertificateNumber,
    generatedOnDevice: true,
    syncState: parsedSession.data.networkState === "offline" ? "pending_sync" : "ready_for_upload",
    measurementCount: parsedSession.data.measurements.length,
  });

  return {
    ok: true,
    certificateDraft,
  };
}
