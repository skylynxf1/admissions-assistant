import type { Citation, SchoolDefinition } from "@/lib/types";

// SAMPLE POLICY DATA ONLY. URLs point to likely official destinations, but policy summaries are not verified.
export const sampleCitations: Citation[] = [
  {
    id: "uw-transfer",
    title: "Transfer application information",
    url: "https://admit.washington.edu/apply/transfer/",
    publisher: "University of Washington Admissions",
    effectiveTerm: "Sample 2026–27",
    lastChecked: "Demo data — not verified",
    official: true,
    demoLabel: "sample-unverified",
  },
  {
    id: "uw-equivalency",
    title: "Transfer equivalency guide",
    url: "https://admit.washington.edu/apply/transfer/equivalency-guide/",
    publisher: "University of Washington Admissions",
    effectiveTerm: "Sample 2026–27",
    lastChecked: "Demo data — not verified",
    official: true,
    demoLabel: "sample-unverified",
  },
  {
    id: "uw-info",
    title: "Informatics admissions",
    url: "https://ischool.uw.edu/programs/informatics/admissions",
    publisher: "UW Information School",
    effectiveTerm: "Sample 2026–27",
    lastChecked: "Demo data — not verified",
    official: true,
    demoLabel: "sample-unverified",
  },
  {
    id: "berkeley-transfer",
    title: "Transfer admission requirements",
    url: "https://admissions.berkeley.edu/apply-to-berkeley/transfer-students/",
    publisher: "UC Berkeley Admissions",
    effectiveTerm: "Sample 2026–27",
    lastChecked: "Demo data — not verified",
    official: true,
    demoLabel: "sample-unverified",
  },
  {
    id: "berkeley-data",
    title: "Data Science major requirements",
    url: "https://cdss.berkeley.edu/dsus/academics/data-science-major",
    publisher: "UC Berkeley CDSS",
    effectiveTerm: "Sample 2026–27",
    lastChecked: "Demo data — not verified",
    official: true,
    demoLabel: "sample-unverified",
  },
  {
    id: "ucla-transfer",
    title: "Transfer admission guide",
    url: "https://admission.ucla.edu/apply/transfer",
    publisher: "UCLA Undergraduate Admission",
    effectiveTerm: "Sample 2026–27",
    lastChecked: "Demo data — not verified",
    official: true,
    demoLabel: "sample-unverified",
  },
];

export const schoolCatalog: SchoolDefinition[] = [
  {
    id: "uw",
    name: "University of Washington",
    shortName: "UW Seattle",
    location: "Seattle, WA",
    color: "#4b2e83",
    minimumTransferCredits: 40,
    preferredCreditRange: [60, 90],
    maximumTransferCredits: 90,
    majors: [
      { id: "uw-informatics", name: "Informatics", college: "Information School", admissionType: "competitive" },
      { id: "uw-computer-science", name: "Computer Science", college: "Allen School", admissionType: "capacity-constrained" },
      { id: "uw-statistics", name: "Statistics", college: "College of Arts & Sciences", admissionType: "competitive" },
    ],
    citations: sampleCitations.filter((citation) => citation.id.startsWith("uw-")),
  },
  {
    id: "berkeley",
    name: "University of California, Berkeley",
    shortName: "UC Berkeley",
    location: "Berkeley, CA",
    color: "#003262",
    minimumTransferCredits: 60,
    preferredCreditRange: [60, 70],
    maximumTransferCredits: 70,
    majors: [
      { id: "berkeley-data-science", name: "Data Science", college: "College of Computing, Data Science, and Society", admissionType: "competitive" },
      { id: "berkeley-cognitive-science", name: "Cognitive Science", college: "College of Letters & Science", admissionType: "competitive" },
      { id: "berkeley-economics", name: "Economics", college: "College of Letters & Science", admissionType: "competitive" },
    ],
    citations: sampleCitations.filter((citation) => citation.id.startsWith("berkeley-")),
  },
  {
    id: "ucla",
    name: "University of California, Los Angeles",
    shortName: "UCLA",
    location: "Los Angeles, CA",
    color: "#2774ae",
    minimumTransferCredits: 60,
    preferredCreditRange: [60, 70],
    maximumTransferCredits: 70,
    majors: [
      { id: "ucla-cognitive-science", name: "Cognitive Science", college: "College of Letters & Science", admissionType: "competitive" },
      { id: "ucla-data-theory", name: "Data Theory", college: "College of Letters & Science", admissionType: "competitive" },
      { id: "ucla-statistics", name: "Statistics & Data Science", college: "College of Letters & Science", admissionType: "competitive" },
    ],
    citations: sampleCitations.filter((citation) => citation.id.startsWith("ucla-")),
  },
];

export const defaultTargets = [
  { schoolId: "uw", majorIds: ["uw-informatics", "uw-computer-science"] },
  { schoolId: "berkeley", majorIds: ["berkeley-data-science"] },
];

export function getSchool(schoolId: string) {
  return schoolCatalog.find((school) => school.id === schoolId);
}

export function getMajor(majorId: string) {
  return schoolCatalog.flatMap((school) => school.majors).find((major) => major.id === majorId);
}
