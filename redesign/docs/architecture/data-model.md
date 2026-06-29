# Research Data Model

Phase 2 introduces the first research-domain layer under
`packages/research_core/src/research_core/research/`. These contracts are
offline-first, frozen dataclasses and do not depend on FastAPI, React, databases,
provider SDKs, embeddings, or legacy root code.

## Entity Boundary

The Phase 2 entities are:

- `Project`: a research workspace boundary with an `id`, `name`, optional
  `description`, and JSON-compatible metadata.
- `ResearchRun`: one research task inside a project with an `id`, `project_id`,
  `question`, `status`, and JSON-compatible metadata.
- `ResearchRunStatus`: the run lifecycle enum: `planned`, `running`,
  `completed`, and `failed`.
- `Source`: ingested material with `id`, `uri`, `title`, `content`, and
  JSON-compatible metadata.
- `Evidence`: a quoted support item extracted from a `Source`, including
  `source_id`, `quote`, optional `summary`, optional `location`, and metadata.
- `Claim`: a verifiable report statement with ordered `evidence_ids`.
- `Report`: a research output with `run_id`, `title`, `summary`, ordered
  `Claim` objects, and metadata.

All metadata is copied, recursively read-only, and strict JSON-compatible. Claim
evidence IDs and report claims are stored as immutable tuples so later evals and
trajectory fixtures can rely on stable ordering.

## Source Ingestion

`SourceInput` is the caller-facing ingestion request. `SourceIngestor` turns a
sequence of inputs into `Source` objects with deterministic IDs such as
`source_1`, `source_2`, or a caller-provided prefix. The ingestor rejects blank
URI, title, content, and ID prefix values.

This is intentionally local and deterministic. Real crawlers, document parsers,
embedding pipelines, and databases arrive in later product or retrieval phases.

## Fake Retrieval

`FakeRetriever` provides offline search over ingested `Source` objects.
`SearchResult` records the source ID, title, snippet, score, and metadata.

The fake retriever uses deterministic token and phrase scoring:

- query token matches provide the base score,
- title token matches add a bonus,
- full query phrase matches add a bonus,
- ties keep source ingestion order.

This is a fixture boundary, not a production search engine. Its job is to make
research tests, labs, and future eval fixtures repeatable without API keys or
network access.

## Claim-Source Mapping

`build_claim_source_links(report, evidence, sources)` turns report claims into
stable `ClaimSourceLink` records. It walks report claims in order and follows
each claim's evidence ID order.

The mapper rejects:

- a claim with no evidence IDs,
- a claim that references missing evidence,
- evidence that references a missing source.

This gives Phase 2 its first citation-quality gate: a report claim is not
considered grounded unless it can be traced to concrete evidence and a concrete
source.

## Deferred Research Workflow

Research planning and report synthesis are not implemented by Phase 2. Phase 3
now provides the first memory and skill policies they need, but richer eval
fixtures are still required before they become useful product workflows. Until
that slice lands, Phase 2 should be treated as the stable data contract layer
for later planning and synthesis work.

## Memory Model

Phase 3 introduces `MemoryRecord` as the first stateful-agent memory contract.
A record has an `id`, `kind`, `content`, ordered tags, an `importance` value,
and JSON-compatible metadata.

Supported `MemoryKind` values are:

- `working`
- `session`
- `episodic`
- `semantic`
- `procedural`
- `pinned`

`MemoryWritePolicy` controls which records can be written by kind, importance,
content length, and forbidden phrases. `MemoryRecallPolicy` controls deterministic
token recall by query, allowed kinds, limit, and pinned-first ordering.

## Skill Model

`SkillPackage` is the loaded representation of a folder-based skill. It contains
the skill name, description, root path, `SKILL.md` entrypoint content, and
discovered resource paths.

`SkillRuntime` enforces progressive disclosure:

- load `SKILL.md` first,
- discover `references/`, `scripts/`, and `assets/` paths,
- read reference content only through explicit `read_reference()` calls,
- reject path traversal and non-reference reads.

## Delegation Model

Phase 4 introduces the first multi-agent contracts under
`packages/research_core/src/research_core/delegation/`.

`AgentRolePolicy` defines a child agent role: role ID, display name, system
prompt, scoped tool names, scoped skill names, scoped memory kinds, and max
steps. `DelegationTask` assigns one child objective from a parent run to a child
run and includes only explicit non-system context messages.

`DelegationBudget` records local limits for child count, per-child steps, and
total steps. `DelegationResult` stores the task, status, final child message,
child events, parent delegation events, error message, and derived step count.
`DelegationMergeResult` preserves child result order and treats every
non-completed child as unresolved until the parent reviews it. When callers pass
an explicit `unresolved_conflicts` list, it must be drawn from the same
`decisions` sequence and must not contain completed results.

`A2AEnvelope` is a versioned task-delegation export record for future remote
agent protocols. It includes task/run IDs, role identity, objective, scoped
tool/skill/memory names, context message IDs, schema version, and message type.
It does not export parent-private task metadata. `A2AAdapterStub` can export this
record but does not implement remote send transport.

## Workbench Product Model

Phase 5 introduces `research_core.product` as the first product-shaped data
contract layer. Its core object is `WorkbenchSnapshot`, a frozen dataclass that
collects product panel records for:

- project,
- run,
- timeline,
- delegation,
- sources and evidence,
- report and claim-source links,
- memory,
- skills,
- evals.

Evidence rows are public `WorkbenchEvidenceItem` records nested under
`WorkbenchSourceItem`. Snapshot construction validates cross-field references:
the run must belong to the project, timeline and report run IDs must match the
snapshot run, source evidence must point back to its source, report links must
reference snapshot evidence, and delegation tree IDs/parent IDs must be
consistent.

`WorkbenchSnapshot.to_record()` returns independent JSON-compatible plain
records for FastAPI and React. This is not raw runtime state and not a database
model. It is the stable adapter between internal contracts and the Workbench
product surface.

The product layer may adapt `RunEvent`, `Source`, `Evidence`, `Report`,
`ClaimSourceLink`, `MemoryRecord`, and delegation records, but it must remain
independent from FastAPI, React, provider SDKs, network transport, and
persistence.
