## ADDED Requirements

### Requirement: Brain Content Lives in a Separate Repo From antigravity-app
The system SHALL store all second-brain content (`raw/` inbox and compiled pages) in a separate sibling repository (`contexia-brain`), never inside `antigravity-app`. This is a structural requirement, not a convention: `antigravity-app`'s `main` branch auto-deploys to Vercel/Railway on every push, and GBrain's autonomous maintenance cycle commits to the brain repo on a schedule, so co-locating them would make autonomous brain maintenance trigger production deployments.

#### Scenario: No brain folders in antigravity-app
- **WHEN** the `antigravity-app` repository is inspected
- **THEN** no `raw/` or brain-compiled-page folders exist at its root or anywhere within it

#### Scenario: Brain repo commits never touch antigravity-app's deploy pipeline
- **WHEN** GBrain's autonomous maintenance cycle commits and pushes to `contexia-brain`
- **THEN** no Vercel or Railway deployment is triggered, because `contexia-brain` is not connected to either deploy pipeline

#### Scenario: GBrain indexes the brain repo only
- **WHEN** GBrain's sync/import runs
- **THEN** it indexes `contexia-brain` (plus `antigravity-app`'s canon docs as read-only sources), and never indexes `antigravity-app`'s code, skills, or OpenSpec artifacts as brain content

### Requirement: Raw Inbox for Unstructured Capture
The system SHALL provide a `raw/` folder at the root of the `contexia-brain` repository where unstructured input (transcribed voice notes, meeting summaries, quick decisions, Telegram/client call notes) can be dropped without any required structure or formatting.

#### Scenario: Note dropped without structure
- **WHEN** a plain-text or markdown file is added to `contexia-brain/raw/` with no required frontmatter or naming convention
- **THEN** the file is accepted as valid input for the librarian loop

#### Scenario: Raw folder never auto-deleted
- **WHEN** the librarian loop processes a file in `contexia-brain/raw/`
- **THEN** the original file is never deleted or silently overwritten (git history plus an explicit move/archive step, not deletion, is the only way content leaves `raw/`)

### Requirement: MECE Compiled Directories Adapted to Contexia's Domain
The `contexia-brain` repository SHALL organize compiled pages into MECE (mutually exclusive, collectively exhaustive) directories adapted from GBrain's default schema to Contexia's B2B agency domains (`people/`, `companies/`, `deals/`, `meetings/`, `concepts/`, `ideas/`, `media/`, `sources/`, `archive/`), each with a `README.md` resolver, plus a top-level `RESOLVER.md` decision tree. Directories that would duplicate existing `antigravity-app` structures (`projects/`, `prompts/`) or that address domains outside Contexia's B2B scope (`civic/`, `household/`, `personal/`, `hiring/`, `diligence/`) SHALL be deliberately excluded, with the exclusion documented.

#### Scenario: Every compiled directory has a resolver
- **WHEN** the `contexia-brain` directory structure is inspected
- **THEN** every MECE directory has a `README.md` explaining what goes there and what does not

#### Scenario: No duplicate project or prompt tracking
- **WHEN** `contexia-brain`'s directory structure is inspected
- **THEN** no `projects/` or `prompts/` directory exists there, and `RESOLVER.md` explicitly redirects that content to `openspec/changes/` and `ai-specs/skills/` in `antigravity-app`

### Requirement: Librarian Loop Is the Interim Path, Superseded by the Dream Cycle
`antigravity-app`'s root `CLAUDE.md`/`AGENTS.md` SHALL be extended with librarian instructions that read `contexia-brain/raw/`, propose updates to the relevant target (a `contexia-brain` compiled page, per its `RESOLVER.md`, or a canon doc: GLOSARIO-MAESTRO, `AGENTES.md`, ground-truth docs), and log uncertainty instead of guessing. These instructions SHALL NOT introduce new `raw/`, brain, `prompts/`, or `projects/` folders inside `antigravity-app`. This manual librarian loop is explicitly the **interim/fallback** enrichment path; once GBrain's Dream Cycle (see `gbrain-adoption`) is live, autonomous enrichment is the primary path and the manual loop is retained only for cases a human wants to drive directly.

#### Scenario: Enrichment ownership is unambiguous
- **WHEN** GBrain's Dream Cycle is live
- **THEN** routine consolidation/enrichment of `contexia-brain/raw/` captures is performed by the Dream Cycle, and the librarian instructions clearly mark themselves as the manual/fallback path (no duplicated, conflicting enrichment authority)

#### Scenario: Librarian proposes a compiled-page update
- **WHEN** the librarian loop is invoked with new content in `contexia-brain/raw/`
- **THEN** it proposes specific edits to the relevant existing target in `contexia-brain/` or a canon doc, rather than creating a new untracked file
- **AND** it never deletes or blindly overwrites existing content without first reading it

#### Scenario: Uncertain content is logged, not guessed
- **WHEN** the librarian cannot confidently map a raw note to an existing topic or doc
- **THEN** it records the uncertainty explicitly (e.g., in a changelog entry) rather than fabricating a placement

#### Scenario: No parallel folders created in antigravity-app
- **WHEN** the librarian instructions are reviewed
- **THEN** they reference `ai-specs/skills/` for reusable prompts and `openspec/changes/` for project tracking, and `contexia-brain/` for all knowledge content
- **AND** no new `raw/`, brain, `prompts/`, or `projects/` folder exists anywhere in `antigravity-app` as a result of this change

### Requirement: Stage 11 Reports Harvested Into the Brain Repo
The system SHALL provide a mechanism (script or scheduled task) in `antigravity-app` that reads completed `openspec/changes/*/reports/*.md` (Stage 11 deployment reports) and writes references to their learnings into `contexia-brain/raw/`, so they compound into the brain instead of remaining inert in an archived change folder.

#### Scenario: Completed Stage 11 report is harvested into the brain repo
- **WHEN** a change's Stage 11 deployment report is created and the change is archived
- **THEN** the harvest mechanism writes a reference to the report's key learnings into `contexia-brain/raw/`, not into `antigravity-app`

#### Scenario: Harvest does not duplicate already-harvested reports
- **WHEN** the harvest mechanism runs and a report has already been harvested in a prior run
- **THEN** it does not re-harvest the same report content, verified via a content-hash-keyed ledger

### Requirement: Brain Pages Use Compiled-Truth + Timeline Structure
New second-brain pages in `contexia-brain` (the ones GBrain's Dream Cycle maintains) SHALL follow GBrain's two-section page model: an upper **compiled-truth** section holding the current best understanding (rewritten as evidence arrives) and a lower **append-only timeline** section that is only added to, never edited. Legacy Contexia canon docs in `antigravity-app` (GLOSARIO-MAESTRO, `AGENTES.md`, ground-truth) are indexed as-is and are NOT required to be reformatted, but new pages in `contexia-brain` SHALL adopt this structure so the Dream Cycle can enrich them.

#### Scenario: New brain page has both sections
- **WHEN** a new compiled page is created in `contexia-brain` from `raw/` content
- **THEN** it contains a compiled-truth section (current synthesis) and a separate append-only timeline section (evidence trail with sources)

#### Scenario: Timeline is append-only
- **WHEN** new evidence about an existing topic arrives and the page is updated
- **THEN** the compiled-truth section may be rewritten, but prior timeline entries are preserved (added to, never deleted or overwritten)

#### Scenario: Legacy canon docs indexed without reformatting
- **WHEN** GBrain indexes GLOSARIO-MAESTRO / `AGENTES.md` / ground-truth docs in `antigravity-app`
- **THEN** they are searchable as-is, with no requirement to retrofit the two-section structure
