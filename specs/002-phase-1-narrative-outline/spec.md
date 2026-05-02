# Feature Specification: Phase 1 - Narrative Outline Generation

**Feature Branch**: `002-phase-1-narrative-outline`
**Created**: 2026-05-02
**Status**: Draft
**Input**: User description: "在需求定义以后继续进行第二个phase 延续需求定义阶段 将project从Artifact推进到产出内容主线(大纲) ;与客户的交互过程依然是在对话框中完成;根据用户提出的视频需求 生成3个不同的叙事大纲提案 ,每个版本包含：开头设计（类型 + 具体做法 + 预期时长占比）、主体观点列表（每观点含标题/核心论据/支撑数据/时长占比/过渡说明）、结尾设计;提案澄清(为什么推荐用这个) ,审核agent:不同脚本有实质的差异,逻辑连贯,包含用户提出的所有主题无遗漏,契合用户的主题;"

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Generate Three Narrative Outline Proposals (Priority: P1)

After Phase 0 requirements are confirmed and the project advances to Phase 1, the system automatically invokes an AI agent to analyze the confirmed requirements and generate three distinct narrative outline proposals. Each proposal presents a different storytelling approach to the same topic. The user sees all three proposals displayed as structured cards in the chat interface, each with an opening design, main argument list, and closing design.

**Why this priority**: This is the core value of Phase 1. Without outline proposals, the user has no content mainline to evaluate, select, or refine, and the pipeline cannot proceed to script writing.

**Independent Test**: Can be fully tested by advancing a project from Phase 0 to Phase 1 with confirmed requirements, then verifying that three outline proposals appear as structured cards within 60 seconds, each containing all required sections.

**Acceptance Scenarios**:

1. **Given** a project with Phase 0 completed and confirmed requirements, **When** the user clicks "确认进入下一阶段" in Phase 0, **Then** Phase 1 becomes active, the system automatically invokes the OutlineAgent to generate three narrative outline proposals based on the confirmed requirements artifact.
2. **Given** the OutlineAgent is generating proposals, **When** generation completes, **Then** three distinct proposal cards appear in the chat area, each labeled "方案A", "方案B", "方案C" with a structured outline containing opening design, main argument list, and closing design.
3. **Given** the confirmed requirements specify a target duration, **When** proposals are generated, **Then** each proposal's section durations sum to approximately the target duration (within ±15% tolerance).
4. **Given** the confirmed requirements specify a topic and viewpoints, **When** proposals are generated, **Then** each proposal addresses all user-specified topics and viewpoints—no topic from the requirements is omitted.

---

### User Story 2 - Review Proposal Details and Understand Rationale (Priority: P1)

The user can expand any proposal card to view the full outline details: the opening design (type, specific approach, expected duration percentage), each main argument (title, core evidence, supporting data, duration percentage, transition description), and the closing design. Each proposal also includes a "提案澄清" (proposal rationale) section explaining why this narrative approach is recommended—what makes it compelling, what audience it suits, and its strengths relative to alternatives.

**Why this priority**: Without understanding the details and rationale, the user cannot make an informed selection. This is the decision-making interface.

**Independent Test**: Can be tested by expanding a proposal card and verifying that all sections (opening, arguments, closing, rationale) are displayed with complete information and no placeholder text.

**Acceptance Scenarios**:

1. **Given** three proposal summary cards are displayed, **When** the user clicks to expand a proposal card, **Then** the full outline is shown with: opening design (type label + specific approach description + expected duration percentage), a numbered list of main arguments (each with title, core evidence, supporting data points, duration percentage, transition description to the next argument), and closing design (approach description).
2. **Given** an expanded proposal card, **When** the user reads the proposal rationale section, **Then** it explains in natural language: why this narrative structure was chosen, what makes it effective for the topic, what type of audience it best serves, and how it differs from the other two proposals.
3. **Given** three proposals are displayed, **When** the user compares them, **Then** each proposal's opening type is clearly different (e.g., different hook strategies: question-led, data-shock, story-anecdote), and the main argument organizations follow different logical structures.

---

### User Story 3 - Review Agent Validates Proposal Quality (Priority: P2)

After the three proposals are generated, a review agent automatically audits them for quality. The review checks: (1) substantial differentiation—the three proposals use genuinely different narrative approaches, not superficial variations; (2) logical coherence—each proposal's argument flow is logically sound and transitions are natural; (3) topic completeness—all topics and viewpoints from the confirmed requirements are covered without omission; (4) thematic fit—each proposal's tone and structure align with the user's stated theme and platform context.

**Why this priority**: Quality assurance prevents poor proposals from reaching the user. However, the user can still review proposals even if the audit fails (the audit flag is advisory, not blocking).

**Independent Test**: Can be tested by generating proposals from varied requirements inputs, then verifying the review agent produces a verdict with specific findings for each of the four checks.

**Acceptance Scenarios**:

1. **Given** three proposals have been generated, **When** the review agent completes its audit, **Then** a review verdict card appears showing: overall verdict (PASS/FAIL), differentiation score with specific comparison notes, coherence assessment per proposal, topic completeness checklist mapped to requirements topics, and thematic fit evaluation.
2. **Given** two proposals use the same opening type and argument structure with only wording changes, **When** the review agent audits differentiation, **Then** the verdict is FAIL with a specific note: "方案A 和方案B 叙事结构高度相似，缺乏实质差异".
3. **Given** a proposal omits a topic that was specified in the confirmed requirements, **When** the review agent audits completeness, **Then** the verdict is FAIL with the missing topic explicitly listed in the blocking issues.
4. **Given** a proposal's arguments are logically inconsistent (e.g., contradictory claims or broken reasoning chain), **When** the review agent audits coherence, **Then** the verdict is FAIL with the specific incoherence described in notes.

---

### User Story 4 - Interact with Proposals via Chat (Priority: P2)

The user can interact with the proposals through the same chat dialog interface used in Phase 0. The user can: ask questions about a specific proposal ("方案A的开头为什么用数据冲击型？"), request modifications to a proposal ("把方案B的第三个观点换成技术分析角度"), request regeneration of one or all proposals ("重新生成方案C", "全部重做"), or express a preference that triggers the selection flow.

**Why this priority**: Chat interaction is the established interaction pattern from Phase 0 and maintains consistency. However, the core value is in proposal generation and selection, so interaction is P2.

**Independent Test**: Can be tested by typing various chat commands after proposals are displayed and verifying appropriate system responses.

**Acceptance Scenarios**:

1. **Given** three proposals are displayed, **When** the user types a question about a specific proposal (e.g., "方案A适合什么受众？"), **Then** the system responds with a targeted answer in the chat without modifying the proposals.
2. **Given** the user wants to modify one proposal, **When** they type a revise command (e.g., "把方案B的主体观点减少到3个"), **Then** only the specified proposal is regenerated with the modification applied, and the other two proposals remain unchanged.
3. **Given** the user is unsatisfied with all proposals, **When** they type "全部重做", **Then** all three proposals are discarded and regenerated from scratch, and the review agent re-runs on the new set.
4. **Given** the user's chat message is ambiguous about which proposal to modify, **When** the Router cannot determine the target, **Then** the system asks a clarifying question: "你想修改哪个方案？" with quick-reply buttons for "方案A", "方案B", "方案C".

---

### User Story 5 - Select a Proposal and Advance (Priority: P1)

The user selects one of the three proposals as the chosen content mainline. The system confirms the selection, persists the chosen outline as the authoritative artifact for Phase 1, and displays the advance button for the next phase. The selected outline becomes the foundation for script writing in Phase 2.

**Why this priority**: Selection is the gate that concludes Phase 1 and produces the artifact that Phase 2 depends on. Without selection, the pipeline stalls.

**Independent Test**: Can be tested by clicking the select button on a proposal, verifying the system confirms the selection, the proposal is marked as selected, and the advance button becomes active.

**Acceptance Scenarios**:

1. **Given** three proposals are displayed with a review verdict of PASS, **When** the user clicks "选择方案B" on the second proposal card, **Then** a confirmation message appears: "确认选择方案B作为内容主线？" with "确认" and "取消" buttons.
2. **Given** the user confirms the selection, **When** the system processes it, **Then** the selected proposal is persisted as the Phase 1 artifact (`outline.json`), the other two proposals are archived for reference, the selected proposal card is highlighted with a "已选择" badge, and the advance button becomes active.
3. **Given** a proposal is selected, **When** the user views the phase navigation, **Then** Phase 1 shows the selected proposal name and a green checkmark.
4. **Given** a review verdict of FAIL, **When** the user attempts to select a proposal, **Then** the system shows a warning: "审核未通过，建议先处理审核意见再选择" but still allows selection (the user can override the review).

---

### Edge Cases

- What happens when the OutlineAgent fails to generate three substantially different proposals (e.g., all three are very similar)? The review agent flags the differentiation check as FAIL, and the system suggests the user request regeneration with specific guidance on what kind of variety to expect.
- What happens when the user's requirements are extremely minimal (e.g., very short description with few concrete viewpoints)? The OutlineAgent produces proposals based on what is available, expanding minimally specified topics with reasonable inferences. The review agent notes the limited input in its assessment.
- What happens when the user switches between proposals rapidly with multiple revise commands? The system processes them sequentially, each targeting the specified proposal and triggering re-review only for affected proposals.
- What happens when the target duration is very short (e.g., 3 minutes) or very long (e.g., 60 minutes)? The OutlineAgent adjusts the number of main arguments and depth accordingly—shorter videos get fewer but more focused arguments, longer videos get more comprehensive argument lists.
- What happens when the user wants to mix elements from different proposals (e.g., "用方案A的开头，方案B的主体，方案C的结尾")? The system treats this as a custom composition request and generates a new merged proposal, presented as "方案D (自定义)".
- What happens when the LLM API call fails during generation? Each proposal is generated independently; if one fails, the other two are still displayed while the failed one shows a retry button. The review agent only runs when all three are successfully generated.
- What happens when the user advances without selecting a proposal? The advance button remains disabled; a proposal must be explicitly selected to advance. The system shows: "请先选择一个方案作为内容主线".

## Requirements _(mandatory)_

### Functional Requirements

**Proposal Generation**

- **FR-001**: System MUST automatically invoke an AI agent (OutlineAgent) to generate three narrative outline proposals when Phase 1 becomes active, using the confirmed Phase 0 requirements artifact as input.
- **FR-002**: Each proposal MUST include: an opening design, a main argument list, and a closing design.
- **FR-003**: The opening design MUST specify: type (e.g., 数据冲击型, 故事引入型, 问题引导型, 观点直给型), specific approach description (concrete execution plan, not generic label), and expected duration percentage of total video length.
- **FR-004**: The main argument list MUST contain at least 2 and at most 8 arguments. Each argument MUST include: title, core evidence (the central claim or reasoning), supporting data (specific facts, statistics, or examples), duration percentage, and transition description (how this argument connects to the next).
- **FR-005**: The closing design MUST specify: type (e.g., 总结升华型, 行动号召型, 开放式结尾型, 回扣开头型), specific approach description, and the closing message or call to action.
- **FR-006**: Each proposal MUST include a proposal rationale ("提案澄清") explaining: why this narrative structure was chosen, its target audience fit, its strengths, and how it differs from the other proposals.
- **FR-007**: The sum of all section duration percentages within a proposal MUST approximate the target video duration from the requirements (within ±15% tolerance).
- **FR-008**: The three proposals MUST use substantially different narrative approaches—different opening types, different argument organization logic, and different closing strategies. Superficial wording changes alone do not satisfy this requirement.

**Proposal Display**

- **FR-009**: System MUST display the three proposals as structured cards in the chat interface, each labeled with a distinct identifier (方案A, 方案B, 方案C).
- **FR-010**: Proposal cards MUST default to a summary view showing the opening type, argument count, total duration, and a one-sentence description. Users can expand any card to view full details.
- **FR-011**: When expanded, a proposal card MUST show all opening design fields, the complete main argument list with all sub-fields, the closing design, and the proposal rationale.

**Review Agent**

- **FR-012**: System MUST automatically invoke a review agent (OutlineReviewer) after all three proposals are successfully generated.
- **FR-013**: The OutlineReviewer MUST audit four dimensions: differentiation (are the three proposals substantially different?), logical coherence (is each proposal's argument flow sound?), topic completeness (are all user-specified topics covered?), and thematic fit (does each proposal align with the user's theme and platform context?).
- **FR-014**: The OutlineReviewer MUST output a binary verdict (PASS/FAIL) with dimension-level scores and specific findings. A FAIL on any dimension produces an overall FAIL with blocking issues listed.
- **FR-015**: On differentiation check, the reviewer MUST compare opening types, argument structures, and closing strategies across all three proposals. If any two proposals share the same opening type AND similar argument organization, the check MUST fail.
- **FR-016**: On topic completeness check, the reviewer MUST map every topic and viewpoint from the confirmed requirements artifact to coverage in each proposal. Any uncovered topic MUST be listed as a blocking issue.

**User Interaction**

- **FR-017**: System MUST allow users to interact with proposals via natural language chat input, maintaining the same dialog interface pattern as Phase 0.
- **FR-018**: A Router component MUST classify Phase 1 user messages into intents: `ask_about_proposal` (question about a specific proposal), `revise_proposal` (modify a specific proposal), `regenerate_one` (redo a single proposal), `regenerate_all` (redo all three), `select_proposal` (choose a proposal as the mainline), `mix_proposals` (combine elements from different proposals), or `clarify` (ambiguous intent).
- **FR-019**: On `revise_proposal`, the system MUST regenerate only the specified proposal with the user's feedback merged, leaving the other two proposals unchanged, and trigger re-review only for the affected proposal's dimensions.
- **FR-020**: On `regenerate_all`, the system MUST discard all current proposals, regenerate three new proposals from scratch, and re-run the full review.
- **FR-021**: On `mix_proposals`, the system MUST create a new merged proposal (labeled "方案D (自定义)") combining the specified elements, without discarding the original three proposals.

**Selection and Advancement**

- **FR-022**: System MUST allow the user to select any one proposal as the chosen content mainline via an explicit selection action.
- **FR-023**: On selection confirmation, the system MUST persist the chosen proposal as the authoritative Phase 1 artifact (`outline.json`) and mark it as selected.
- **FR-024**: A GateKeeper MUST verify before allowing advancement: outline artifact exists and passes schema validation, a proposal has been explicitly selected, the review verdict is PASS (warning if FAIL but not blocking), and all tasks are in terminal states.
- **FR-025**: If the review verdict is FAIL, the advance button MUST show a warning but remain clickable—the user may override the review.

**Artifact and State**

- **FR-026**: System MUST persist the Phase 1 artifact (`outline.json`) containing: project_id, requirements_ref (link to Phase 0 artifact), three proposals with all fields, the selected proposal reference, review verdict, and generation metadata (timestamp, model, token usage).
- **FR-027**: System MUST persist all Phase 1 dialogue history and task states for recovery on browser close/reopen or server restart.

### Key Entities

- **Narrative Outline Proposal**: A complete content mainline for a video. Contains: proposal_id, label (A/B/C/D), opening design (type, approach, duration_pct), main arguments list (each with title, core_evidence, supporting_data, duration_pct, transition), closing design (type, approach, closing_message), rationale (explanation, target_audience, strengths, differentiation), and status (active/selected/archived).
- **Opening Design**: Defines how the video begins. Fields: type (enum: data_shock, story_anecdote, question_lead, opinion_first), approach_description (concrete execution plan), duration_percentage (of total video length).
- **Main Argument**: A single viewpoint in the video body. Fields: title, core_evidence (central claim), supporting_data (facts/statistics/examples), duration_percentage, transition_description.
- **Closing Design**: Defines how the video ends. Fields: type (enum: summary_elevation, call_to_action, open_ended, callback_opening), approach_description, closing_message.
- **Phase 1 Artifact** (`outline.json`): The output of Phase 1. Contains: project_id, requirements_ref, proposals array, selected_proposal_id, review_verdict, generation_metadata.
- **Review Verdict**: The output of the OutlineReviewer. Contains: verdict (PASS/FAIL), dimension scores (differentiation, coherence, completeness, thematic_fit), notes per dimension, blocking_issues list.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: Three substantially different narrative outline proposals are generated and displayed within 60 seconds of entering Phase 1 for a typical requirements input (3-5 viewpoints, 8-15 minute target duration).
- **SC-002**: The OutlineReviewer correctly flags proposals with insufficient differentiation—proposals sharing the same opening type AND argument structure receive a FAIL on differentiation with specific comparison notes.
- **SC-003**: The topic completeness check achieves 100% coverage—every topic and viewpoint from the confirmed Phase 0 requirements is mapped to at least one argument in every proposal.
- **SC-004**: Users can complete the full Phase 1 flow (view proposals → review → optionally revise → select → advance) in under 8 minutes for a typical requirements input.
- **SC-005**: The proposal selection and advancement gate prevents advancement when no proposal is selected (zero false-positive gate passes for unselected state).
- **SC-006**: Each proposal's section duration percentages sum to within ±15% of the target video duration from the requirements.
- **SC-007**: 90% of proposal generations produce three proposals where at least two have different opening types and different argument organization strategies on the first attempt.
- **SC-008**: All Phase 1 state (proposals, selection, dialogue, tasks) is fully recoverable within 10 seconds of reopening the browser or after a server restart.

## Assumptions

- Phase 0 has been completed and a valid, confirmed `requirements.json` artifact exists for the project.
- The target video duration from Phase 0 requirements is used to calculate per-section durations; if no duration was specified, a default of 10 minutes is assumed.
- The user interacts in Chinese natural language (consistent with Phase 0).
- The OutlineAgent uses the same LLM infrastructure configured in `config/model_config.json` as Phase 0 agents.
- Section duration percentages within a proposal are advisory (guide the subsequent script-writing phase), not binding constraints.
- The proposal selection is final once confirmed—Phase 1 becomes read-only after advancement (consistent with the Phase 0 pattern).
- Proposal cards support expand/collapse interaction in the frontend chat interface.
- The review agent's FAIL verdict is advisory (warning) for advancement, not blocking—the user may override it. This differs from Phase 0 where the review gate is stricter.
- Custom composition (mixing elements from different proposals) creates a new proposal rather than modifying existing ones.
- The three-proposal count is fixed for v1; future versions may allow configurable counts.
