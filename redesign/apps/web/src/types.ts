export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonValue[] | JsonObject;
export type JsonObject = { [key: string]: JsonValue };

export type WorkbenchProject = {
  id: string;
  title: string;
  description: string;
  metadata: JsonObject;
};

export type WorkbenchRun = {
  id: string;
  project_id: string;
  title: string;
  question: string;
  status: string;
  metadata: JsonObject;
};

export type WorkbenchTimelineItem = {
  id: string;
  run_id: string;
  type: string;
  title: string;
  summary: string;
  timestamp: string;
  metadata: JsonObject;
};

export type WorkbenchDelegationNode = {
  id: string;
  title: string;
  role: string;
  status: string;
  run_id: string;
  summary: string;
  parent_id: string;
  children: WorkbenchDelegationNode[];
  metadata: JsonObject;
};

export type WorkbenchEvidenceItem = {
  id: string;
  source_id: string;
  quote: string;
  claim_ids: string[];
  summary: string;
  location: string;
  metadata: JsonObject;
};

export type WorkbenchSourceItem = {
  id: string;
  title: string;
  uri: string;
  summary: string;
  evidence: WorkbenchEvidenceItem[];
  metadata: JsonObject;
};

export type WorkbenchClaimSourceLink = {
  claim_id: string;
  claim_text: string;
  evidence_id: string;
  source_id: string;
  source_title: string;
  source_uri: string;
  quote: string;
  location: string;
};

export type WorkbenchReport = {
  id: string;
  run_id: string;
  title: string;
  summary: string;
  claim_source_links: WorkbenchClaimSourceLink[];
  metadata: JsonObject;
};

export type WorkbenchMemorySummaryRow = {
  id: string;
  title: string;
  kind: string;
  importance: number;
  tags: string[];
};

export type WorkbenchMemoryItem = {
  id: string;
  title: string;
  kind: string;
  content: string;
  summary: string;
  tags: string[];
  importance: number;
  summary_row: WorkbenchMemorySummaryRow;
  metadata: JsonObject;
};

export type WorkbenchSkillSummaryRow = {
  id: string;
  title: string;
  name: string;
  status: string;
  resource_count: number;
};

export type WorkbenchSkillItem = {
  id: string;
  title: string;
  name: string;
  description: string;
  status: string;
  resources: string[];
  summary_row: WorkbenchSkillSummaryRow;
  metadata: JsonObject;
};

export type WorkbenchEvalSummaryRow = {
  id: string;
  title: string;
  metric: string;
  status: string;
  score: number;
};

export type WorkbenchEvalItem = {
  id: string;
  title: string;
  metric: string;
  status: string;
  score: number;
  details: string;
  summary_row: WorkbenchEvalSummaryRow;
  metadata: JsonObject;
};

export type WorkbenchSnapshot = {
  project: WorkbenchProject;
  run: WorkbenchRun;
  timeline: WorkbenchTimelineItem[];
  delegation: WorkbenchDelegationNode[];
  sources: WorkbenchSourceItem[];
  report: WorkbenchReport | null;
  memory: WorkbenchMemoryItem[];
  skills: WorkbenchSkillItem[];
  evals: WorkbenchEvalItem[];
};
