# Project instructions

## Resume a work session

Read these files before planning or changing the project:

1. [Project progress](docs/progress.md): current state, ticket status, decisions,
   validation evidence and the next concrete actions.
2. [Agent roadmap](docs/agent-roadmap.md): ticket definitions, dependencies,
   acceptance criteria and delivery sequence. Read the relevant ticket sections.
3. [Contributing](CONTRIBUTING.md): code boundaries, quality checks and data handling.

Consult [architecture](docs/architecture.md) for the implemented runtime and
[the council review](docs/agent-council-review.md) for design rationale. Do not
repeat the research council just to recover context.

Check the actual branch, recent commits and working-tree changes. Treat recorded
Git state as a dated snapshot; preserve unrelated user changes. Reconcile stale
progress with repository evidence before relying on it. Never print credentials
or read the complete environment file into the conversation.

When the user asks to continue, use the next eligible action in the progress file
within their current authorization. Do not ask them to restate documented context
or reconfirm settled decisions. Their latest instructions take precedence; record
new decisions and the scope of any authorization. A proposed budget or an agent's
review is not user approval for paid execution.

## Where work is tracked

- **Ticket scope and acceptance:** [docs/agent-roadmap.md](docs/agent-roadmap.md),
  using stable IDs SV-01 through SV-11. These are repository tickets; do not imply
  external issues exist unless their links are recorded.
- **Live status and handoff:** [docs/progress.md](docs/progress.md). This is the
  single source of truth for execution status, active milestone and next moves.
- **Design rationale:** [docs/agent-council-review.md](docs/agent-council-review.md).
  It is a historical review, not a second live status board.

Keep scope in the roadmap and status in the progress file. If scope or acceptance
changes, update the roadmap and record the reason in progress. Avoid copying the
entire backlog or conversation into multiple documents.

## Update progress as part of the work

Updating [docs/progress.md](docs/progress.md) is part of completing each milestone.
Do it without waiting for the user to ask. Also checkpoint when work is blocked,
material decisions change, or the session ends with unfinished work.

At the start of an implementation milestone, record the active ticket/substep and
branch. At a milestone boundary or handoff:

1. Update the dated current-state summary and affected ticket statuses.
2. Record what changed, relevant files/artifacts and commit/PR links if they exist.
   Distinguish local, committed, pushed and merged work.
   When publication is authorized, push the intended branch and verify its remote
   SHA directly. A local commit or merge is not publication; report any unpublished
   work explicitly instead of calling the repository synchronized.
3. Record validation actually performed, its outcome and outstanding checks.
   Separate offline software checks, paid evaluation and engineering acceptance.
4. Record blockers and pending decisions with their affected scope. Preserve
   previously granted authorization; do not infer new approval.
5. Write ordered next actions with ticket IDs, the first concrete action and the
   condition that permits it. Include enough detail to resume without this chat.
6. Append a concise milestone/history entry. Keep the current snapshot short;
   preserve earlier milestone evidence rather than replacing it with new claims.

Use statuses: planned, in_progress, in_review, blocked, done, deferred. Mark done
only when the ticket's acceptance criteria have evidence; a partial substep does
not complete its parent. An optional deferred feature is not a blocker. Record
technical completion separately from pending semantic acceptance or PR review.
Never present an old check as rerun in the current session.

## Project constraints to preserve

- The actual Management CPU DOCX is the acceptance workload. OpenTitan is
  supporting diagnostic material. Keep authored references outside agent retrieval.
- The current runtime uses OpenAI Agents SDK specialists, OpenRouter and Python
  orchestration. Follow the roadmap before expanding agents or redesigning schemas.
- Application changes use focused branches and reviewed PRs. Keep persisted
  contracts and prompt versions explicit; preserve historical export/spend access.
- Normal tests are offline. Paid runs require the recorded applicable authorization
  and budget; report confirmed charges separately from unsettled reservations.
- Never store keys, private source excerpts, reference answers or generated plans
  in progress or tracked docs. Use ignored local artifacts and safe paths/hashes.
- Follow [README](README.md) and [CONTRIBUTING](CONTRIBUTING.md) for checks. For
  documentation-only edits, verify links and consistency without claiming code
  tests or paid evaluations were run.
