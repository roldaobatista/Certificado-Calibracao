/**
 * Abstract PDF/A validator interface.
 * Production requires veraPDF CLI or external validation API.
 */

export interface PdfaValidationResult {
  compliant: boolean;
  profile: "PDF/A-1a" | "PDF/A-1b" | "PDF/A-2a" | "PDF/A-2b" | "PDF/A-2u" | "PDF/A-3a" | "PDF/A-3b" | "PDF/A-3u" | "unknown";
  errors: Array<{ ruleId: string; description: string; page?: number }>;
  warnings: Array<{ ruleId: string; description: string }>;
}

export interface PdfaValidator {
  validate(buffer: Buffer, expectedProfile?: PdfaValidationResult["profile"]): Promise<PdfaValidationResult>;
}

// Stub implementation for development.
// Always returns compliant for well-formed PDFs starting with %PDF.
export function createDevPdfaValidator(): PdfaValidator {
  return {
    async validate(buffer, expectedProfile = "PDF/A-3b") {
      const isPdf = buffer.length > 4 && buffer.subarray(0, 5).toString() === "%PDF-";
      return {
        compliant: isPdf,
        profile: expectedProfile,
        errors: isPdf ? [] : [{ ruleId: "DEV-001", description: "Invalid PDF header (stub validator)" }],
        warnings: [{ ruleId: "DEV-W001", description: "Stub validator does not perform real PDF/A validation" }],
      };
    },
  };
}
