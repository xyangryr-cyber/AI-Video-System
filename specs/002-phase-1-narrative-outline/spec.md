# Feature Specification: Phase 1 - Narrative Outline Generation

**Feature Branch**: `002-phase-1-narrative-outline`
**Created**: 2026-05-02
**Status**: Draft
**Input**: User description: "在需求定义以后继续进行第二个phase 延续需求定义阶段 将project从Artifact推进到产出内容主线(大纲) ;与客户的交互过程依然是在对话框中完成;根据用户提出的视频需求 生成3个不同的叙事大纲提案 ,每个版本包含：开头设计（类型 + 具体做法 + 预期时长占比）、主体观点列表（每观点含标题/核心论据/支撑数据/时长占比/过渡说明）、结尾设计;提案澄清(为什么推荐用这个) ,审核agent:不同脚本有实质的差异,逻辑连贯,包含用户提出的所有主题无遗漏,契合用户的主题;"

## Clarifications

### Session 2026-05-02

- Q: Frontend display format for proposal content → A: All user-facing language interactions use rendered Markdown formatted text. No special card components or complex display forms.
- Q: Duration-related rules in Phase 1 → A: Phase 1 does not handle or introduce any duration-related rules. Duration percentages and time constraints are completely removed from this phase.
- Q: Fact-checking for outline content → A: Introduce a fact-checking agent (FactChecker) that extracts key factual claims from outline proposals, searches for information sources, verifies authenticity, and flags unverifiable or false claims to prevent incorrect content from entering the outline.
- Q: User-driven regeneration and mandatory re-check → A: Users can provide their own requirements/opinions to request regeneration of one or more proposals. After EVERY outline update (revise, regenerate, mix), both fact-checking and quality review MUST re-run on affected proposals before the advance button becomes active.
- Q: Fact-checking persistence and structured output → A: Fact-checking results are persisted as a standalone versioned artifact (`fact_check.json`), independently recoverable. All factual claims MUST be output in a fixed structured JSON schema; the LLM is NOT allowed to freely improvise format or add unstructured commentary.
- Q: Agent system prompt management → A: All agent system prompts (OutlineAgent, FactChecker, OutlineReviewer) are maintained in configuration files under `config/prompts/`, not hardcoded in agent code. Prompt changes are configuration changes, not code changes.
- Q: Fact-checking source priority → A: FactChecker prioritizes high-authority sources (government databases, regulatory filings, academic publications). Only free APIs and publicly accessible datasets are used; no paid/proprietary data services.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Generate Three Narrative Outline Proposals (Priority: P1)

After Phase 0 requirements are confirmed and the project advances to Phase 1, the system automatically invokes an AI agent to analyze the confirmed requirements and generate three distinct narrative outline proposals. Each proposal presents a different storytelling approach to the same topic. The user sees all three proposals displayed as rendered Markdown formatted text in the chat interface, each with an opening design, main argument list, and closing design.

**Why this priority**: This is the core value of Phase 1. Without outline proposals, the user has no content mainline to evaluate, select, or refine, and the pipeline cannot proceed to script writing.

**Independent Test**: Can be fully tested by advancing a project from Phase 0 to Phase 1 with confirmed requirements, then verifying that three outline proposals appear as rendered Markdown text within 60 seconds, each containing all required sections.

**Acceptance Scenarios**:

1. **Given** a project with Phase 0 completed and confirmed requirements, **When** the user clicks "确认进入下一阶段" in Phase 0, **Then** Phase 1 becomes active, the system automatically invokes the OutlineAgent to generate three narrative outline proposals based on the confirmed requirements artifact.
2. **Given** the OutlineAgent is generating proposals, **When** generation completes, **Then** three distinct proposals appear in the chat area as rendered Markdown text, each labeled "方案A", "方案B", "方案C" with a structured outline containing opening design, main argument list, and closing design.
3. **Given** the confirmed requirements specify a topic and viewpoints, **When** proposals are generated, **Then** each proposal addresses all user-specified topics and viewpoints—no topic from the requirements is omitted.

---

### User Story 2 - Review Proposal Details and Understand Rationale (Priority: P1)

The user reads the full outline details for each proposal in the chat interface as rendered Markdown text: the opening design (type, specific approach), each main argument (title, core evidence, supporting data, transition description), and the closing design. Each proposal also includes a "提案澄清" (proposal rationale) section explaining why this narrative approach is recommended—what makes it compelling, what audience it suits, and its strengths relative to alternatives.

**Why this priority**: Without understanding the details and rationale, the user cannot make an informed selection. This is the decision-making interface.

**Independent Test**: Can be tested by reading a proposal's rendered Markdown content and verifying that all sections (opening, arguments, closing, rationale) are displayed with complete information and no placeholder text.

**Acceptance Scenarios**:

1. **Given** three proposal summaries are displayed as Markdown text, **When** the user reads a proposal, **Then** the full outline is shown with: opening design (type label + specific approach description), a numbered list of main arguments (each with title, core evidence, supporting data points, transition description to the next argument), and closing design (approach description).
2. **Given** a proposal displayed as Markdown, **When** the user reads the proposal rationale section, **Then** it explains in natural language: why this narrative structure was chosen, what makes it effective for the topic, what type of audience it best serves, and how it differs from the other two proposals.
3. **Given** three proposals are displayed, **When** the user compares them, **Then** each proposal's opening type is clearly different (e.g., different hook strategies: question-led, data-shock, story-anecdote), and the main argument organizations follow different logical structures.

---

### User Story 3 - Fact-Checking Agent Verifies Key Claims (Priority: P1)

After the three proposals are generated, a fact-checking agent (FactChecker) automatically extracts key factual claims from each proposal's arguments. For each claim, the agent searches for information sources, evaluates the authenticity and accuracy of the claim, and produces a fact-check report. Claims that cannot be verified or are found to be inaccurate are flagged so the user can review them before the outline is finalized—preventing incorrect content from entering the content mainline.

**Why this priority**: Financial content must be factually accurate. An incorrect statistic or false claim in the outline would cascade into the script and final video, damaging credibility. Fact-checking is a hard quality gate.

**Independent Test**: Can be tested by generating proposals that contain verifiable claims (e.g., specific statistics, historical events), then verifying the FactChecker produces a report identifying each claim, its verification status, and source references.

**Acceptance Scenarios**:

1. **Given** three proposals have been generated, **When** the FactChecker completes its analysis, **Then** a fact-check report appears as rendered Markdown text listing: each extracted factual claim, its verification status (verified / unverifiable / disputed), source references (where available), and an overall fact-check verdict (PASS / FAIL).
2. **Given** a proposal contains a claim like "2024年中国GDP增长5.2%", **When** the FactChecker evaluates it, **Then** the claim is marked as "verified" with a source reference if a matching authoritative source is found, or "unverifiable" if no reliable source confirms it.
3. **Given** a proposal contains a claim that contradicts known facts, **When** the FactChecker identifies the contradiction, **Then** the claim is marked as "disputed" with the conflicting evidence and source cited.
4. **Given** a fact-check report with FAIL verdict, **When** the user views it, **Then** the disputed or unverifiable claims are clearly highlighted, and the user can request regeneration of affected proposal sections with corrected information.

---

### User Story 4 - Review Agent Validates Proposal Quality (Priority: P2)

After the three proposals are generated and fact-checking is complete, a review agent automatically audits them for quality. The review checks: (1) substantial differentiation—the three proposals use genuinely different narrative approaches, not superficial variations; (2) logical coherence—each proposal's argument flow is logically sound and transitions are natural; (3) topic completeness—all topics and viewpoints from the confirmed requirements are covered without omission; (4) thematic fit—each proposal's tone and structure align with the user's stated theme and platform context.

**Why this priority**: Quality assurance prevents poor proposals from reaching the user. However, the user can still review proposals even if the audit fails (the audit flag is advisory, not blocking).

**Independent Test**: Can be tested by generating proposals from varied requirements inputs, then verifying the review agent produces a verdict with specific findings for each of the four checks.

**Acceptance Scenarios**:

1. **Given** three proposals have been generated and fact-checked, **When** the review agent completes its audit, **Then** a review verdict appears as rendered Markdown text showing: overall verdict (PASS/FAIL), differentiation score with specific comparison notes, coherence assessment per proposal, topic completeness checklist mapped to requirements topics, and thematic fit evaluation.
2. **Given** two proposals use the same opening type and argument structure with only wording changes, **When** the review agent audits differentiation, **Then** the verdict is FAIL with a specific note: "方案A 和方案B 叙事结构高度相似，缺乏实质差异".
3. **Given** a proposal omits a topic that was specified in the confirmed requirements, **When** the review agent audits completeness, **Then** the verdict is FAIL with the missing topic explicitly listed in the blocking issues.
4. **Given** a proposal's arguments are logically inconsistent (e.g., contradictory claims or broken reasoning chain), **When** the review agent audits coherence, **Then** the verdict is FAIL with the specific incoherence described in notes.

---

### User Story 5 - Interact with Proposals via Chat (Priority: P2)

The user can interact with the proposals through the same chat dialog interface used in Phase 0. The user can: ask questions about a specific proposal ("方案A的开头为什么用数据冲击型？"), provide feedback to request modifications to a proposal ("把方案B的第三个观点换成技术分析角度"), request regeneration of one or more proposals based on their own requirements ("按我的要求重新生成方案A和方案C", "全部重做"), or express a preference that triggers the selection flow. **Every time an outline is updated (revised, regenerated, or mixed), both fact-checking and quality review MUST re-run on the affected proposals before the user can advance.** All responses are rendered as Markdown formatted text.

**Why this priority**: Chat interaction is the established interaction pattern from Phase 0 and maintains consistency. However, the core value is in proposal generation and selection, so interaction is P2.

**Independent Test**: Can be tested by typing various chat commands after proposals are displayed and verifying appropriate system responses.

**Acceptance Scenarios**:

1. **Given** three proposals are displayed, **When** the user types a question about a specific proposal (e.g., "方案A适合什么受众？"), **Then** the system responds with a targeted answer as Markdown text without modifying the proposals.
2. **Given** the user wants to modify one proposal, **When** they type a revise command (e.g., "把方案B的主体观点减少到3个"), **Then** only the specified proposal is regenerated with the modification applied, the other two proposals remain unchanged, and fact-checking re-runs on the updated proposal.
3. **Given** the user is unsatisfied with all proposals, **When** they type "全部重做", **Then** all three proposals are discarded and regenerated from scratch, and both fact-checking and review re-run on the new set.
4. **Given** the user's chat message is ambiguous about which proposal to modify, **When** the Router cannot determine the target, **Then** the system asks a clarifying question: "你想修改哪个方案？" with quick-reply options for "方案A", "方案B", "方案C".
5. **Given** the user requests regeneration with specific requirements (e.g., "按我的要求重新生成方案B,加强技术分析的角度"), **When** the regeneration completes, **Then** fact-checking and quality review automatically re-run on the updated proposal, and the updated proposal is displayed with its new fact-check and review results.
6. **Given** the user requests regeneration of multiple proposals, **When** regeneration completes, **Then** fact-checking and review re-run on all affected proposals, and results are displayed before the advance button becomes active.

---

### User Story 6 - Select a Proposal and Advance (Priority: P1)

The user selects one of the three proposals as the chosen content mainline. The system confirms the selection, persists the chosen outline as the authoritative artifact for Phase 1, and displays the advance button for the next phase. The selected outline becomes the foundation for script writing in Phase 2.

**Why this priority**: Selection is the gate that concludes Phase 1 and produces the artifact that Phase 2 depends on. Without selection, the pipeline stalls.

**Independent Test**: Can be tested by selecting a proposal, verifying the system confirms the selection, the proposal is marked as selected, and the advance button becomes active.

**Acceptance Scenarios**:

1. **Given** three proposals are displayed with review verdict PASS and fact-check verdict PASS, **When** the user selects a proposal via the selection action, **Then** a confirmation message appears: "确认选择方案B作为内容主线？" with "确认" and "取消" options.
2. **Given** the user confirms the selection, **When** the system processes it, **Then** the selected proposal is persisted as the Phase 1 artifact (`outline.json`), the other two proposals are archived for reference, the selected proposal is marked as "已选择", and the advance button becomes active.
3. **Given** a proposal is selected, **When** the user views the phase navigation, **Then** Phase 1 shows the selected proposal name and a green checkmark.
4. **Given** a fact-check verdict of FAIL, **When** the user attempts to select a proposal, **Then** the system shows a warning: "事实核查未通过，建议先处理 disputed 或 unverifiable 的声明再选择" but still allows selection (the user may override the fact-check).
5. **Given** a review verdict of FAIL, **When** the user attempts to select a proposal, **Then** the system shows a warning: "审核未通过，建议先处理审核意见再选择" but still allows selection.

---

### Edge Cases

- What happens when the OutlineAgent fails to generate three substantially different proposals (e.g., all three are very similar)? The review agent flags the differentiation check as FAIL, and the system suggests the user request regeneration with specific guidance on what kind of variety to expect.
- What happens when the user's requirements are extremely minimal (e.g., very short description with few concrete viewpoints)? The OutlineAgent produces proposals based on what is available, expanding minimally specified topics with reasonable inferences. The review agent notes the limited input in its assessment.
- What happens when the user switches between proposals rapidly with multiple revise commands? The system processes them sequentially, each targeting the specified proposal and triggering re-review and fact-checking only for affected proposals.
- What happens when the user wants to mix elements from different proposals (e.g., "用方案A的开头，方案B的主体，方案C的结尾")? The system treats this as a custom composition request and generates a new merged proposal, presented as "方案D (自定义)". Fact-checking runs on the merged proposal.
- What happens when the LLM API call fails during generation? Each proposal is generated independently; if one fails, the other two are still displayed while the failed one shows a retry button. Fact-checking and review only run when all three are successfully generated.
- What happens when the user advances without selecting a proposal? The advance button remains disabled; a proposal must be explicitly selected to advance. The system shows: "请先选择一个方案作为内容主线".
- What happens when the FactChecker cannot find any sources for a claim? The claim is marked as "unverifiable" with a note explaining the search was exhaustive but no authoritative source was found. The system does not fabricate sources.
- What happens when a proposal contains a large number of factual claims (e.g., 20+)? The FactChecker prioritizes claims by materiality—claims central to the argument are checked first. Minor or widely-known claims may be batched or deferred with a note.
- What happens when the FactChecker's source search returns conflicting information from different sources? The claim is marked as "disputed" with all conflicting sources cited, and the user is advised to review and choose which source to rely on.
- What happens when a proposal is revised after fact-checking? The FactChecker re-runs only on the revised proposal, checking new or modified claims while preserving existing verification results for unchanged claims.
- What happens when the user requests regeneration of multiple proposals simultaneously (e.g., "重新生成方案A和方案C")? Both proposals are regenerated, and fact-checking plus review run on both before the advance button becomes active. The system does not allow partial advancement with unchecked proposals.
- What happens when a user attempts to advance while fact-checking or review is still running after an update? The advance button is disabled with the message "事实核查和审核进行中，请等待完成". The button only becomes active after both agents complete.

## Requirements _(mandatory)_

### Functional Requirements

**Proposal Generation**

- **FR-001**: System MUST automatically invoke an AI agent (OutlineAgent) to generate three narrative outline proposals when Phase 1 becomes active, using the confirmed Phase 0 requirements artifact as input.
- **FR-002**: Each proposal MUST include: an opening design, a main argument list, and a closing design.
- **FR-003**: The opening design MUST specify: type (e.g., 数据冲击型, 故事引入型, 问题引导型, 观点直给型) and specific approach description (concrete execution plan, not generic label).
- **FR-004**: The main argument list MUST contain at least 2 and at most 8 arguments. Each argument MUST include: title, core evidence (the central claim or reasoning), supporting data (specific facts, statistics, or examples), and transition description (how this argument connects to the next).
- **FR-005**: The closing design MUST specify: type (e.g., 总结升华型, 行动号召型, 开放式结尾型, 回扣开头型), specific approach description, and the closing message or call to action.
- **FR-006**: Each proposal MUST include a proposal rationale ("提案澄清") explaining: why this narrative structure was chosen, its target audience fit, its strengths, and how it differs from the other proposals.
- **FR-007**: The three proposals MUST use substantially different narrative approaches—different opening types, different argument organization logic, and different closing strategies. Superficial wording changes alone do not satisfy this requirement.

**Proposal Display**

- **FR-008**: System MUST display all user-facing language interaction content as rendered Markdown formatted text in the chat interface. No special card components or complex display forms.
- **FR-009**: System MUST display the three proposals as rendered Markdown text, each labeled with a distinct identifier (方案A, 方案B, 方案C).
- **FR-010**: Each proposal's Markdown display MUST include all opening design fields, the complete main argument list with all sub-fields, the closing design, and the proposal rationale.

**Fact-Checking Agent**

- **FR-011**: System MUST automatically invoke a fact-checking agent (FactChecker) after all three proposals are successfully generated and before the quality review agent.
- **FR-012**: The FactChecker MUST extract key factual claims from each proposal's main arguments. A key factual claim is any statement that: asserts a specific statistic, references a historical event or date, attributes a statement to a specific person/organization, or makes a quantifiable comparison.
- **FR-013**: For each extracted claim, the FactChecker MUST search for information sources and assign a verification status: `verified` (confirmed by at least one authoritative source), `unverifiable` (no reliable source found after exhaustive search), or `disputed` (conflicting information from multiple sources, or contradiction with authoritative source).
- **FR-014**: The FactChecker MUST cite the specific source(s) used for verification (URL, publication name, or dataset reference). Claims without sources MUST be marked as "unverifiable"—the system MUST NOT fabricate source references.
- **FR-015**: The FactChecker MUST prioritize high-authority sources when searching for verification: government statistical databases, official regulatory filings, peer-reviewed academic publications, and established financial data providers. Free APIs and publicly accessible datasets MUST be used for data retrieval; no paid/proprietary data services are assumed.
- **FR-016**: The FactChecker MUST output all extracted factual claims in a structured format (JSON with defined schema fields: claim_text, source_proposal_id, source_argument_index, verification_status, cited_sources, verification_note). The LLM MUST NOT freely improvise the output format or add unstructured commentary—the output schema is fixed and machine-validated.
- **FR-017**: The FactChecker MUST output a fact-check report containing: the list of extracted claims with verification status and sources (in the structured format defined by FR-016), and an overall fact-check verdict (PASS if all claims are verified or no key claims were found; FAIL if any claim is unverifiable or disputed).
- **FR-018**: When any proposal is updated (revised, regenerated, or mixed), the FactChecker MUST re-run on the affected proposals, re-checking new or modified claims while preserving existing verification results for unchanged claims. This is a hard rule—no outline update may skip fact-checking.
- **FR-019**: The FactChecker's structured output (factual claims list and fact-check report) MUST be persisted as a standalone artifact (`fact_check.json`) within the project, independently recoverable and immutable per generation run. Each fact-check run produces a versioned snapshot.

**Agent Prompt Configuration**

- **FR-020**: All agent system prompts (OutlineAgent, FactChecker, OutlineReviewer) MUST be maintained in configuration files under a designated prompts directory (e.g., `config/prompts/`), NOT hardcoded in agent implementation code. Changing an agent's prompt MUST be achievable by editing a configuration file without modifying source code.

**Quality Review Agent**

- **FR-021**: System MUST automatically invoke a quality review agent (OutlineReviewer) after fact-checking is complete.
- **FR-022**: The OutlineReviewer MUST audit four dimensions: differentiation (are the three proposals substantially different?), logical coherence (is each proposal's argument flow sound?), topic completeness (are all user-specified topics covered?), and thematic fit (does each proposal align with the user's theme and platform context?).
- **FR-023**: The OutlineReviewer MUST output a binary verdict (PASS/FAIL) with dimension-level scores and specific findings. A FAIL on any dimension produces an overall FAIL with blocking issues listed.
- **FR-024**: On differentiation check, the reviewer MUST compare opening types, argument structures, and closing strategies across all three proposals. If any two proposals share the same opening type AND similar argument organization, the check MUST fail.
- **FR-025**: On topic completeness check, the reviewer MUST map every topic and viewpoint from the confirmed requirements artifact to coverage in each proposal. Any uncovered topic MUST be listed as a blocking issue.

**User Interaction**

- **FR-026**: System MUST allow users to interact with proposals via natural language chat input, maintaining the same dialog interface pattern as Phase 0. Users may provide their own requirements and opinions to request regeneration of one or more proposals.
- **FR-027**: A Router component MUST classify Phase 1 user messages into intents: `ask_about_proposal` (question about a specific proposal), `revise_proposal` (modify a specific proposal per user feedback), `regenerate_one` (redo a single proposal per user requirements), `regenerate_all` (redo all three), `select_proposal` (choose a proposal as the mainline), `mix_proposals` (combine elements from different proposals), or `clarify` (ambiguous intent).
- **FR-028**: On `revise_proposal`, the system MUST regenerate only the specified proposal with the user's feedback merged, leaving the other two proposals unchanged, and trigger fact-checking and re-review for the affected proposal.
- **FR-029**: On `regenerate_all`, the system MUST discard all current proposals, regenerate three new proposals from scratch, and re-run both fact-checking and the full review.
- **FR-030**: On `mix_proposals`, the system MUST create a new merged proposal (labeled "方案D (自定义)") combining the specified elements, without discarding the original three proposals. Fact-checking and review MUST run on the merged proposal.
- **FR-031**: After EVERY outline update (revise, regenerate_one, regenerate_all, mix_proposals), the system MUST automatically trigger fact-checking and quality review on the affected proposals. The advance button MUST NOT become active until both fact-checking and review have completed on all current proposals.

**Selection and Advancement**

- **FR-032**: System MUST allow the user to select any one proposal as the chosen content mainline via an explicit selection action.
- **FR-033**: On selection confirmation, the system MUST persist the chosen proposal as the authoritative Phase 1 artifact (`outline.json`) and mark it as selected.
- **FR-034**: A GateKeeper MUST verify before allowing advancement: outline artifact exists and passes schema validation, a proposal has been explicitly selected, fact-checking is complete with results persisted, review is complete, and all tasks are in terminal states.
- **FR-035**: If the fact-check verdict is FAIL, the advance button MUST show a warning but remain clickable—the user may override.
- **FR-036**: If the review verdict is FAIL, the advance button MUST show a warning but remain clickable—the user may override.

**Artifact and State**

- **FR-037**: System MUST persist the Phase 1 artifact (`outline.json`) containing: project_id, requirements_ref (link to Phase 0 artifact), three proposals with all fields, the selected proposal reference, fact-check report reference, review verdict, and generation metadata (timestamp, model, token usage).
- **FR-038**: System MUST persist the fact-check report as a standalone versioned artifact (`fact_check.json`) containing: project_id, run_timestamp, proposals_checked, extracted claims with structured fields per FR-016, overall verdict. Each fact-check run produces a new version; old versions are retained for audit trail.
- **FR-039**: System MUST persist all Phase 1 dialogue history and task states for recovery on browser close/reopen or server restart.

### Key Entities

- **Narrative Outline Proposal**: A complete content mainline for a video. Contains: proposal_id, label (A/B/C/D), opening design (type, approach), main arguments list (each with title, core_evidence, supporting_data, transition), closing design (type, approach, closing_message), rationale (explanation, target_audience, strengths, differentiation), and status (active/selected/archived).
- **Opening Design**: Defines how the video begins. Fields: type (enum: data_shock, story_anecdote, question_lead, opinion_first), approach_description (concrete execution plan).
- **Main Argument**: A single viewpoint in the video body. Fields: title, core_evidence (central claim), supporting_data (facts/statistics/examples), transition_description.
- **Closing Design**: Defines how the video ends. Fields: type (enum: summary_elevation, call_to_action, open_ended, callback_opening), approach_description, closing_message.
- **Fact-Check Report** (`fact_check.json`): The persisted, versioned output of the FactChecker. Each run produces a new versioned snapshot; old versions are retained for audit trail. Contains: project_id, run_timestamp, proposals_checked (array of proposal IDs), extracted claims (array of FactualClaim objects in the structured schema defined by FR-016), overall verdict (PASS/FAIL). Stored independently from `outline.json` for immutability per run.
- **Factual Claim**: A single verifiable statement extracted from a proposal argument, output in a fixed structured schema (JSON). Fields: claim_text, source_proposal_id, source_argument_index, verification_status (enum: verified / unverifiable / disputed), cited_sources (array of {source_name, source_url, source_type}), verification_note. LLM MUST NOT deviate from this schema or add unstructured commentary.
- **Phase 1 Artifact** (`outline.json`): The output of Phase 1. Contains: project_id, requirements_ref, proposals array, selected_proposal_id, fact_check_report_ref (reference to latest `fact_check.json` version), review_verdict, generation_metadata.
- **Review Verdict**: The output of the OutlineReviewer. Contains: verdict (PASS/FAIL), dimension scores (differentiation, coherence, completeness, thematic_fit), notes per dimension, blocking_issues list.
- **Agent Prompt Configuration**: System prompts for each agent (OutlineAgent, FactChecker, OutlineReviewer) stored as configuration files under `config/prompts/`. Each prompt file is independently editable without modifying agent source code. Changing prompt behavior is a configuration change, not a code change.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: Three substantially different narrative outline proposals are generated and displayed within 60 seconds of entering Phase 1 for a typical requirements input (3-5 viewpoints).
- **SC-002**: The OutlineReviewer correctly flags proposals with insufficient differentiation—proposals sharing the same opening type AND argument structure receive a FAIL on differentiation with specific comparison notes.
- **SC-003**: The topic completeness check achieves 100% coverage—every topic and viewpoint from the confirmed Phase 0 requirements is mapped to at least one argument in every proposal.
- **SC-004**: Users can complete the full Phase 1 flow (view proposals → fact-check review → quality review → optionally revise → select → advance) in under 10 minutes for a typical requirements input.
- **SC-005**: The proposal selection and advancement gate prevents advancement when no proposal is selected (zero false-positive gate passes for unselected state).
- **SC-006**: 90% of proposal generations produce three proposals where at least two have different opening types and different argument organization strategies on the first attempt.
- **SC-007**: All Phase 1 state (proposals, selection, dialogue, tasks) is fully recoverable within 10 seconds of reopening the browser or after a server restart.
- **SC-008**: The FactChecker extracts and verifies at least 80% of key factual claims present in proposals—no claim marked as "verified" is later found to be factually incorrect (zero false-positive verifications).
- **SC-009**: 100% of claims marked as "verified" include at least one cited source reference. Zero claims are marked as "verified" with fabricated sources.
- **SC-010**: 100% of factual claims output by the FactChecker conform to the structured schema defined in FR-016—zero instances of LLM free-form text in place of structured fields (validated by schema check after each FactChecker run).
- **SC-011**: After every outline update (revise, regenerate, mix), both fact-checking and quality review complete automatically within 90 seconds for a typical single-proposal update—the advance button is never activatable with stale or missing fact-check/review results.
- **SC-012**: Fact-check reports are persisted as versioned snapshots—at least the 5 most recent `fact_check.json` versions are recoverable, and each run is independently auditable by comparing versions.
- **SC-013**: Changing an agent's system prompt requires editing only a configuration file under `config/prompts/`—zero source code modifications are needed to update prompt behavior.

## Assumptions

- Phase 0 has been completed and a valid, confirmed `requirements.json` artifact exists for the project.
- Duration-related constraints are NOT handled in Phase 1. Section durations, timing, and pacing are deferred to the script-writing phase (Phase 2).
- The user interacts in Chinese natural language (consistent with Phase 0).
- All agents (OutlineAgent, FactChecker, OutlineReviewer) use the same LLM infrastructure configured in `config/model_config.json` as Phase 0 agents.
- The proposal selection is final once confirmed—Phase 1 becomes read-only after advancement (consistent with the Phase 0 pattern).
- The FactChecker's FAIL verdict and the OutlineReviewer's FAIL verdict are advisory (warning) for advancement, not blocking—the user may override them.
- Custom composition (mixing elements from different proposals) creates a new proposal rather than modifying existing ones.
- The three-proposal count is fixed for v1; future versions may allow configurable counts.
- All user-facing language interaction content is displayed as rendered Markdown formatted text—no specialized card components, expand/collapse widgets, or complex display forms are used for content presentation.
- Fact-checking is scoped to key factual claims (statistics, historical events, attributions, quantifiable comparisons); it does not check opinions, subjective analysis, or rhetorical statements.
- All agent system prompts (OutlineAgent, FactChecker, OutlineReviewer) are stored as configuration files under `config/prompts/`, following the project's existing pattern of externalized configuration. No prompts are hardcoded in agent implementation modules.
- The FactChecker uses only free, publicly accessible APIs and websites for source verification. No paid or proprietary data services are assumed or required. High-authority sources (government databases, regulatory filings, academic publications) are prioritized over general web search results.
- The FactChecker's output is strictly structured (JSON schema defined in `src/shared/schemas/`). The LLM is constrained to fill predefined fields; free-form text generation is not permitted for factual claim output. Schema validation runs as a post-generation gate on every fact-check run.
