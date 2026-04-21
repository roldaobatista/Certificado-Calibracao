import { z } from "zod";

const CERTIFICATE_NUMBER_PATTERN = /^[A-Z0-9]{2,12}-\d{6}$/;

export const offlineCalibrationMeasurementSchema = z.object({
  parameterId: z.string().min(1),
  value: z.number().finite(),
  unit: z.string().min(1),
});

export const offlineCalibrationSessionSchema = z.object({
  sessionId: z.string().min(1),
  workOrderId: z.string().min(1),
  organizationId: z.string().min(1),
  deviceId: z.string().min(1),
  networkState: z.enum(["offline", "online"]),
  reservedCertificateNumber: z.string().regex(CERTIFICATE_NUMBER_PATTERN),
  measurements: z.array(offlineCalibrationMeasurementSchema).min(1),
  technicalReviewCompleted: z.boolean(),
  certificateSignedOnDevice: z.boolean(),
  equipmentId: z.string().min(1),
  customerId: z.string().min(1),
});

export const offlineCertificateDraftSchema = z.object({
  sessionId: z.string().min(1),
  workOrderId: z.string().min(1),
  certificateNumber: z.string().regex(CERTIFICATE_NUMBER_PATTERN),
  generatedOnDevice: z.literal(true),
  syncState: z.enum(["pending_sync", "ready_for_upload"]),
  measurementCount: z.number().int().positive(),
});

export type OfflineCalibrationMeasurement = z.infer<typeof offlineCalibrationMeasurementSchema>;
export type OfflineCalibrationSession = z.infer<typeof offlineCalibrationSessionSchema>;
export type OfflineCertificateDraft = z.infer<typeof offlineCertificateDraftSchema>;
