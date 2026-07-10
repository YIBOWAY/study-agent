import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import {
  Activity,
  Braces,
  AlertCircle,
  CheckCircle2,
  CircleDot,
  XCircle,
  Database,
  FileText,
  Gauge,
  GitBranch,
  LayoutDashboard,
  Library,
  Network,
  Play,
  RefreshCcw,
  Save,
  Search,
  Send,
  Settings2,
  ShieldCheck,
  Sparkles,
  Wrench
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type {
  JsonObject,
  WorkbenchDelegationNode,
  WorkbenchEvalItem,
  WorkbenchMemoryItem,
  WorkbenchSkillItem,
  WorkbenchSnapshot,
  WorkbenchTimelineItem
} from "./types";

const fallbackSnapshot: WorkbenchSnapshot = {
  project: {
    id: "project_workbench_demo",
    title: "Research Agent Workbench",
    description: "Deterministic local snapshot for the Phase 5 product surface.",
    metadata: { owner: "research_core.product" }
  },
  run: {
    id: "run_workbench_demo",
    project_id: "project_workbench_demo",
    title: "Workbench snapshot contract demo",
    question: "How should a research workbench preserve traceability?",
    status: "completed",
    metadata: { mode: "demo" }
  },
  timeline: [
    {
      id: "evt_model_request",
      run_id: "run_workbench_demo",
      type: "model_request",
      title: "Model request",
      summary: "Asked the planner to identify evidence requirements.",
      timestamp: "",
      metadata: { model: "demo-research-model", tokens: { prompt: 128 } }
    },
    {
      id: "evt_tool_call",
      run_id: "run_workbench_demo",
      type: "tool_call",
      title: "Tool call",
      summary: "Retrieved source material for the report claim.",
      timestamp: "",
      metadata: {
        tool: "retriever.search",
        query: "workbench claim source links"
      }
    },
    {
      id: "evt_delegate_start",
      run_id: "run_workbench_demo",
      type: "delegate_start",
      title: "Delegate start",
      summary: "Started a focused source-review child run.",
      timestamp: "",
      metadata: {
        task_id: "task_source_review",
        child_run_id: "run_child_source_review"
      }
    },
    {
      id: "evt_delegate_finish",
      run_id: "run_workbench_demo",
      type: "delegate_finish",
      title: "Delegate finish",
      summary: "Merged the child review back into the parent run.",
      timestamp: "",
      metadata: {
        task_id: "task_source_review",
        child_run_id: "run_child_source_review",
        status: "completed"
      }
    }
  ],
  delegation: [
    {
      id: "task_source_review",
      title: "Source review",
      role: "evidence-reviewer",
      status: "completed",
      run_id: "run_child_source_review",
      summary: "Confirmed that each report claim keeps a source-backed link.",
      parent_id: "",
      children: [],
      metadata: { parent_run_id: "run_workbench_demo" }
    }
  ],
  sources: [
    {
      id: "source_claim_links",
      title: "Workbench Contract Notes",
      uri: "memory://workbench/claim-links",
      summary: "Contract note used to prove claim-source continuity.",
      evidence: [
        {
          id: "evidence_claim_links",
          source_id: "source_claim_links",
          quote: "Every report claim keeps an evidence link back to a source.",
          claim_ids: ["claim_1"],
          summary: "",
          location: "note-1",
          metadata: { confidence: 1 }
        }
      ],
      metadata: { kind: "demo" }
    }
  ],
  report: {
    id: "report_workbench_demo",
    run_id: "run_workbench_demo",
    title: "Workbench Snapshot Demo",
    summary:
      "The snapshot exposes timeline, delegation, sources, report, memory, skills, and eval panels.",
    claim_source_links: [
      {
        claim_id: "claim_1",
        claim_text:
          "Citation-backed workbench snapshots make research auditable.",
        evidence_id: "evidence_claim_links",
        source_id: "source_claim_links",
        source_title: "Workbench Contract Notes",
        source_uri: "memory://workbench/claim-links",
        quote: "Every report claim keeps an evidence link back to a source.",
        location: "note-1"
      }
    ],
    metadata: {}
  },
  memory: [
    {
      id: "mem_citation_rule",
      title: "Citation rule",
      kind: "pinned",
      content: "Always preserve citation links in research reports.",
      summary: "Pinned rule that keeps report claims auditable.",
      tags: ["citation", "reporting"],
      importance: 0.95,
      summary_row: {
        id: "mem_citation_rule",
        title: "Citation rule",
        kind: "pinned",
        importance: 0.95,
        tags: ["citation", "reporting"]
      },
      metadata: {}
    },
    {
      id: "mem_workbench_preference",
      title: "Workbench preference",
      kind: "semantic",
      content: "The workbench should show dense operational panels.",
      summary: "Durable product preference recalled for the UI.",
      tags: ["product"],
      importance: 0.8,
      summary_row: {
        id: "mem_workbench_preference",
        title: "Workbench preference",
        kind: "semantic",
        importance: 0.8,
        tags: ["product"]
      },
      metadata: {}
    }
  ],
  skills: [
    {
      id: "skill_source_mapping",
      title: "Source mapping",
      name: "source-mapping",
      description: "Checks that report claims keep source links.",
      status: "loaded",
      resources: ["references/claim-source-links.md", "scripts/check_links.py"],
      summary_row: {
        id: "skill_source_mapping",
        title: "Source mapping",
        name: "source-mapping",
        status: "loaded",
        resource_count: 2
      },
      metadata: {}
    }
  ],
  evals: [
    {
      id: "eval_claim_links",
      title: "Claim links",
      metric: "claim_source_coverage",
      status: "passed",
      score: 1,
      details: "All report claims include source-backed evidence links.",
      summary_row: {
        id: "eval_claim_links",
        title: "Claim links",
        metric: "claim_source_coverage",
        status: "passed",
        score: 1
      },
      metadata: {}
    }
  ]
};

const navItems: Array<{ label: string; icon: LucideIcon; active?: boolean }> = [
  { label: "Workspace", icon: LayoutDashboard, active: true },
  { label: "Runs", icon: Activity },
  { label: "Evidence", icon: Library },
  { label: "Delegation", icon: Network },
  { label: "Memory", icon: Database },
  { label: "Skills", icon: Wrench },
  { label: "Evals", icon: Gauge }
];

type DataSource = "loading" | "api" | "fixture";

export default function App() {
  const [snapshot, setSnapshot] = useState<WorkbenchSnapshot>(fallbackSnapshot);
  const [dataSource, setDataSource] = useState<DataSource>("loading");
  const [taskDraft, setTaskDraft] = useState(fallbackSnapshot.run.question);
  const [reportDraft, setReportDraft] = useState(
    fallbackSnapshot.report?.summary ?? "",
  );

  useEffect(() => {
    const controller = new AbortController();

    async function loadSnapshot() {
      try {
        const response = await fetch("/api/workbench/snapshot", {
          signal: controller.signal
        });
        if (!response.ok) {
          throw new Error(`Snapshot request failed: ${response.status}`);
        }
        const data = (await response.json()) as WorkbenchSnapshot;
        setSnapshot(data);
        setTaskDraft(data.run.question);
        setReportDraft(data.report?.summary ?? "");
        setDataSource("api");
      } catch (error) {
        if (!controller.signal.aborted) {
          setSnapshot(fallbackSnapshot);
          setTaskDraft(fallbackSnapshot.run.question);
          setReportDraft(fallbackSnapshot.report?.summary ?? "");
          setDataSource("fixture");
        }
      }
    }

    void loadSnapshot();
    return () => controller.abort();
  }, []);

  const evidenceCount = useMemo(
    () =>
      snapshot.sources.reduce(
        (count, source) => count + source.evidence.length,
        0,
      ),
    [snapshot.sources],
  );

  const report = snapshot.report;

  return (
    <div className="app-shell">
      <aside className="workspace-nav" aria-label="Workspace navigation">
        <div className="brand-block">
          <div className="brand-mark">RA</div>
          <div>
            <span className="eyebrow">Research</span>
            <strong>Workbench</strong>
          </div>
        </div>

        <nav className="nav-list">
          {navItems.map((item) => (
            <button
              className={`nav-button${item.active ? " is-active" : ""}`}
              key={item.label}
              title={item.label}
              type="button"
            >
              <item.icon size={18} />
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="nav-footer">
          <button className="icon-button" title="Refresh snapshot" type="button">
            <RefreshCcw size={16} />
          </button>
          <button className="icon-button" title="Workspace settings" type="button">
            <Settings2 size={16} />
          </button>
        </div>
      </aside>

      <main className="workbench-shell">
        <header className="workbench-header">
          <div className="title-block">
            <span className="eyebrow">{snapshot.project.id}</span>
            <h1>{snapshot.project.title}</h1>
          </div>
          <div className="header-metrics" aria-label="Run metrics">
            <Metric label="run" value={snapshot.run.status} tone="green" />
            <Metric label="events" value={String(snapshot.timeline.length)} />
            <Metric label="evidence" value={String(evidenceCount)} tone="blue" />
            <span className={`source-pill source-pill-${dataSource}`}>
              {dataSource === "api" ? "api" : dataSource}
            </span>
          </div>
        </header>

        <section className="surface-grid" aria-label="Workbench panels">
          <section className="panel task-panel" aria-labelledby="task-title">
            <PanelHeader
              id="task-title"
              icon={Send}
              kicker="Task composer"
              title={snapshot.run.title}
            />
            <textarea
              aria-label="Task question"
              className="task-input"
              value={taskDraft}
              onChange={(event) => setTaskDraft(event.target.value)}
            />
            <div className="composer-actions">
              <button className="primary-action" type="button">
                <Play size={15} />
                Run
              </button>
              <button className="tool-button" title="Search sources" type="button">
                <Search size={15} />
              </button>
              <button className="tool-button" title="Attach context" type="button">
                <Braces size={15} />
              </button>
            </div>
          </section>

          <section className="panel timeline-panel" aria-labelledby="timeline-title">
            <PanelHeader
              id="timeline-title"
              icon={CircleDot}
              kicker="Run timeline"
              title="Trace"
            />
            <div className="timeline-list">
              {snapshot.timeline.map((item, index) => (
                <TimelineRow
                  index={index}
                  item={item}
                  key={item.id}
                  total={snapshot.timeline.length}
                />
              ))}
            </div>
          </section>

          <section className="panel sources-panel" aria-labelledby="sources-title">
            <PanelHeader
              id="sources-title"
              icon={ShieldCheck}
              kicker="Sources and evidence"
              title="Claim links"
            />
            <div className="source-list">
              {snapshot.sources.map((source) => (
                <div className="source-row" key={source.id}>
                  <div className="row-heading">
                    <strong>{source.title}</strong>
                    <span>{source.uri}</span>
                  </div>
                  <p>{source.summary}</p>
                  {source.evidence.map((evidence) => (
                    <blockquote className="evidence-quote" key={evidence.id}>
                      <span>{evidence.quote}</span>
                      <footer>
                        {evidence.location} / {evidence.claim_ids.join(", ")}
                      </footer>
                    </blockquote>
                  ))}
                </div>
              ))}
            </div>
          </section>

          <section
            className="panel delegation-panel"
            aria-labelledby="delegation-title"
          >
            <PanelHeader
              id="delegation-title"
              icon={GitBranch}
              kicker="Delegation tree"
              title="Agents"
            />
            <div className="delegation-list">
              {snapshot.delegation.map((node) => (
                <DelegationNode node={node} key={node.id} />
              ))}
            </div>
          </section>

          <section className="panel report-panel" aria-labelledby="report-title">
            <PanelHeader
              id="report-title"
              icon={FileText}
              kicker="Report editor"
              title={report?.title ?? "Draft report"}
            >
              <button className="tool-button" title="Save report" type="button">
                <Save size={15} />
              </button>
            </PanelHeader>
            <textarea
              aria-label="Report summary"
              className="report-editor"
              value={reportDraft}
              onChange={(event) => setReportDraft(event.target.value)}
            />
            <div className="claim-list">
              {(report?.claim_source_links ?? []).map((link) => (
                <div className="claim-row" key={link.claim_id}>
                  <strong>{link.claim_text}</strong>
                  <span>{link.source_title}</span>
                </div>
              ))}
            </div>
          </section>

          <section className="panel memory-panel" aria-labelledby="memory-title">
            <PanelHeader
              id="memory-title"
              icon={Database}
              kicker="Memory panel"
              title="Recall"
            />
            <MemoryList items={snapshot.memory} />
          </section>

          <section className="panel skills-panel" aria-labelledby="skills-title">
            <PanelHeader
              id="skills-title"
              icon={Sparkles}
              kicker="Skills panel"
              title="Runtime"
            />
            <SkillList items={snapshot.skills} />
          </section>

          <section className="panel eval-panel" aria-labelledby="eval-title">
            <PanelHeader
              id="eval-title"
              icon={Gauge}
              kicker="Eval panel"
              title="Quality"
            />
            <EvalList items={snapshot.evals} />
          </section>
        </section>
      </main>
    </div>
  );
}

function PanelHeader({
  children,
  id,
  icon: Icon,
  kicker,
  title
}: {
  children?: ReactNode;
  id?: string;
  icon: LucideIcon;
  kicker: string;
  title: string;
}) {
  const headingId = id ?? `${kicker.toLowerCase().replaceAll(" ", "-")}-title`;

  return (
    <div className="panel-header">
      <div className="panel-title">
        <Icon size={16} />
        <div>
          <span className="eyebrow">{kicker}</span>
          <h2 id={headingId}>{title}</h2>
        </div>
      </div>
      {children ? <div className="panel-tools">{children}</div> : null}
    </div>
  );
}

function TimelineRow({
  index,
  item,
  total
}: {
  index: number;
  item: WorkbenchTimelineItem;
  total: number;
}) {
  return (
    <article className={`timeline-row tone-${toneFor(item.type)}`}>
      <div className="timeline-glyph" aria-hidden="true">
        {index + 1}
      </div>
      <div className="timeline-copy">
        <div className="row-heading">
          <strong>{item.title}</strong>
          <span>
            {index + 1}/{total} {labelize(item.type)}
          </span>
        </div>
        <p>{item.summary}</p>
        <code>{metadataPreview(item.metadata)}</code>
      </div>
    </article>
  );
}

function DelegationNode({ node }: { node: WorkbenchDelegationNode }) {
  return (
    <article className="delegation-node">
      <div className="node-line">
        <Network size={15} />
        <strong>{node.title}</strong>
        <span className={`status-chip ${statusTone(node.status)}`}>
          {node.status}
        </span>
      </div>
      <p>{node.summary}</p>
      <div className="node-meta">
        <span>{node.role}</span>
        <span>{node.run_id}</span>
      </div>
      {node.children.length > 0 ? (
        <div className="child-nodes">
          {node.children.map((child) => (
            <DelegationNode node={child} key={child.id} />
          ))}
        </div>
      ) : null}
    </article>
  );
}

function MemoryList({ items }: { items: WorkbenchMemoryItem[] }) {
  return (
    <div className="compact-list">
      {items.map((item) => (
        <article className="memory-row" key={item.id}>
          <div className="row-heading">
            <strong>{item.title}</strong>
            <span>{item.kind}</span>
          </div>
          <p>{item.summary}</p>
          <div className="meter" aria-label={`${item.title} importance`}>
            <span style={{ width: `${item.importance * 100}%` }} />
          </div>
          <div className="tag-list">
            {item.tags.map((tag) => (
              <span key={tag}>{tag}</span>
            ))}
          </div>
        </article>
      ))}
    </div>
  );
}

function SkillList({ items }: { items: WorkbenchSkillItem[] }) {
  return (
    <div className="compact-list">
      {items.map((item) => (
        <article className="skill-row" key={item.id}>
          <div className="row-heading">
            <strong>{item.title}</strong>
            <span>{item.status}</span>
          </div>
          <p>{item.description}</p>
          <div className="resource-list">
            {item.resources.map((resource) => (
              <code key={resource}>{resource}</code>
            ))}
          </div>
        </article>
      ))}
    </div>
  );
}

function EvalList({ items }: { items: WorkbenchEvalItem[] }) {
  return (
    <div className="compact-list">
      {items.map((item) => {
        const tone = evalStatusTone(item.status);
        const Icon =
          tone === "good" ? CheckCircle2 : tone === "bad" ? XCircle : AlertCircle;
        return (
          <article className="eval-row" key={item.id}>
            <div className={`eval-score eval-score-${tone}`}>
              <Icon size={18} />
              <strong>{Math.round(item.score * 100)}%</strong>
            </div>
            <div>
              <div className="row-heading">
                <strong>{item.title}</strong>
                <span className={statusTone(item.status)}>{item.status}</span>
              </div>
              <p>{item.details}</p>
              <code>{item.metric}</code>
            </div>
          </article>
        );
      })}
    </div>
  );
}

function evalStatusTone(status: string): "good" | "bad" | "neutral" {
  const normalized = status.toLowerCase();
  if (
    normalized === "passed" ||
    normalized === "pass" ||
    normalized === "completed" ||
    normalized === "ok"
  ) {
    return "good";
  }
  if (
    normalized === "failed" ||
    normalized === "fail" ||
    normalized === "error"
  ) {
    return "bad";
  }
  return "neutral";
}

function Metric({
  label,
  tone = "neutral",
  value
}: {
  label: string;
  tone?: "neutral" | "green" | "blue";
  value: string;
}) {
  return (
    <div className={`metric metric-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function labelize(value: string) {
  return value.replaceAll("_", " ");
}

function toneFor(value: string) {
  if (value.includes("delegate")) {
    return "purple";
  }
  if (value.includes("tool")) {
    return "amber";
  }
  if (value.includes("model")) {
    return "blue";
  }
  return "neutral";
}

function statusTone(status: string) {
  if (status === "completed" || status === "passed" || status === "loaded") {
    return "status-good";
  }
  if (status === "failed" || status === "error") {
    return "status-bad";
  }
  return "status-neutral";
}

function metadataPreview(metadata: JsonObject) {
  const preview = JSON.stringify(metadata);
  return preview === "{}" ? "metadata: none" : preview;
}
