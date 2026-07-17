// Strict JSON Schema for OpenAI Structured Outputs. Every property is required;
// unknown transcript values are represented with null instead of being invented.
const sourceSchema = {
  type: "object",
  additionalProperties: false,
  properties: {
    pageNumber: { type: "integer", minimum: 1 },
    parserBlockIds: { type: "array", items: { type: "string" } },
    rawText: { type: ["string", "null"] },
  },
  required: ["pageNumber", "parserBlockIds", "rawText"],
} as const;

export const transcriptExtractionJsonSchema = {
  type: "object",
  additionalProperties: false,
  properties: {
    documentType: { type: "string", enum: ["college_transcript", "unknown"] },
    studentName: { type: ["string", "null"] },
    institutions: {
      type: "array",
      items: {
        type: "object",
        additionalProperties: false,
        properties: {
          id: { type: "string" }, name: { type: "string" }, studentIdentifier: { type: ["string", "null"] },
          attendanceStart: { type: ["string", "null"] }, attendanceEnd: { type: ["string", "null"] },
          degreeName: { type: ["string", "null"] }, degreeDate: { type: ["string", "null"] },
          confidence: { type: "number", minimum: 0, maximum: 1 }, source: sourceSchema,
        },
        required: ["id", "name", "studentIdentifier", "attendanceStart", "attendanceEnd", "degreeName", "degreeDate", "confidence", "source"],
      },
    },
    terms: {
      type: "array",
      items: {
        type: "object",
        additionalProperties: false,
        properties: {
          id: { type: "string" }, institutionId: { type: "string" }, label: { type: "string" },
          startDate: { type: ["string", "null"] }, endDate: { type: ["string", "null"] }, academicLevel: { type: ["string", "null"] },
          creditsAttempted: { type: ["number", "null"] }, creditsEarned: { type: ["number", "null"] }, termGpa: { type: ["number", "null"] },
          confidence: { type: "number", minimum: 0, maximum: 1 }, source: sourceSchema,
        },
        required: ["id", "institutionId", "label", "startDate", "endDate", "academicLevel", "creditsAttempted", "creditsEarned", "termGpa", "confidence", "source"],
      },
    },
    courses: {
      type: "array",
      items: {
        type: "object",
        additionalProperties: false,
        properties: {
          id: { type: "string" }, institutionId: { type: "string" }, termId: { type: "string" }, courseCode: { type: "string" }, courseTitle: { type: "string" },
          creditsAttempted: { type: ["number", "null"] }, creditsEarned: { type: ["number", "null"] }, grade: { type: ["string", "null"] },
          status: { type: "string", enum: ["completed", "in_progress", "withdrawn", "failed", "audit", "unknown"] },
          repeatIndicator: { type: "boolean" }, transferIndicator: { type: "boolean" }, confidence: { type: "number", minimum: 0, maximum: 1 }, source: sourceSchema,
        },
        required: ["id", "institutionId", "termId", "courseCode", "courseTitle", "creditsAttempted", "creditsEarned", "grade", "status", "repeatIndicator", "transferIndicator", "confidence", "source"],
      },
    },
    examCredits: {
      type: "array",
      items: {
        type: "object",
        additionalProperties: false,
        properties: {
          id: { type: "string" }, examType: { type: "string", enum: ["AP", "IB", "CLEP", "other"] }, subject: { type: "string" },
          score: { type: ["string", "null"] }, creditsAwarded: { type: ["number", "null"] }, confidence: { type: "number", minimum: 0, maximum: 1 }, source: sourceSchema,
        },
        required: ["id", "examType", "subject", "score", "creditsAwarded", "confidence", "source"],
      },
    },
    summary: {
      type: "object",
      additionalProperties: false,
      properties: {
        cumulativeGpa: { type: ["number", "null"] }, totalCreditsAttempted: { type: ["number", "null"] }, totalCreditsEarned: { type: ["number", "null"] },
        totalQualityPoints: { type: ["number", "null"] }, degreeName: { type: ["string", "null"] }, degreeDate: { type: ["string", "null"] },
        confidence: { type: "number", minimum: 0, maximum: 1 }, source: sourceSchema,
      },
      required: ["cumulativeGpa", "totalCreditsAttempted", "totalCreditsEarned", "totalQualityPoints", "degreeName", "degreeDate", "confidence", "source"],
    },
  },
  required: ["documentType", "studentName", "institutions", "terms", "courses", "examCredits", "summary"],
} as const;
