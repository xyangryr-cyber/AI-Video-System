# Feature Specification: Phase 0 - AI Video Requirements Definition

**Feature Branch**: `001-phase-0-requirements`
**Created**: 2026-05-02
**Status**: Draft
**Input**: User description: "用户在前端创建项目 可以AI识别视频需求 与用户确认 用户可以修改 核实完信息保存进入下一环节"

## Clarifications

### Session 2026-05-02

- Q: User Story 4 - Extract and Confirm Learning Preferences → A: Removed from this version; preference extraction is deferred to a future release.
- Q: FR-020 task list display behavior → A: Default collapsed view showing only the currently executing task; expandable to show all tasks.
- Q: inject_subtask scope → A: Keep as recognized intent but not implemented; respond with "此功能暂未开放" placeholder.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create Project and Get AI Requirements (Priority: P1)

A content creator opens the app, navigates to the new project page, enters a video title and natural language description of what they want to create, and submits. The system immediately creates the project and an AI agent analyzes the description to produce a structured set of video production requirements (topic, target duration, platform, category, word count). The creator sees the AI's understanding displayed as a structured summary card in a chat-like interface.

**Why this priority**: This is the entry point. Without project creation and AI requirements generation, nothing else in the pipeline can function.

**Independent Test**: Can be fully tested by submitting a title and description on the new project page, then verifying that a structured requirements summary card appears in the project detail view within 30 seconds.

**Acceptance Scenarios**:

1. **Given** a user on the new project page, **When** they enter a valid title (non-empty) and description (>=10 characters) and click submit, **Then** a project is created, the user is redirected to the project detail page showing Phase 0 as active, and an AI agent begins analyzing the description.
2. **Given** a newly created project, **When** the RequirementsAgent completes its analysis, **Then** a structured summary card appears in the chat area showing: extracted topic, target duration (if mentioned), platform with technical specs, content category, target word count, and any clarification questions for missing information.
3. **Given** a user entering only a title with no description, **When** they click submit, **Then** submission is blocked with a message "描述不能少于 10 个字".
4. **Given** a user entering only a description with no title, **When** they click submit, **Then** submission is blocked with a message "标题不能为空".

---

### User Story 2 - Review Requirements and Confirm Accuracy (Priority: P1)

After the AI generates requirements, the system automatically runs a completeness review. The content creator sees the review result and can confirm the requirements are correct, or modify them through natural language conversation. The creator can instruct the AI to revise specific fields ("改成8-12分钟", "换个技术角度"), or request a full regeneration.

**Why this priority**: Without review and confirmation, the system has no quality gate and would advance with potentially wrong requirements.

**Independent Test**: Can be tested by having the AI generate requirements, then verifying the review runs automatically and the user can issue revise/regenerate commands through the chat input.

**Acceptance Scenarios**:

1. **Given** the RequirementsAgent has completed, **When** the CompletenessReviewer finishes its audit, **Then** the task list shows the review as passed (PASS) or failed (FAIL), and the requirements card reflects the verdict.
2. **Given** a review verdict of FAIL, **When** the user types a revision command like "改成8-12分钟", **Then** the Router identifies the intent as `revise`, the RequirementsAgent regenerates with the user's feedback merged, a new version of requirements is created, the old review is superseded, and a new review task is automatically triggered.
3. **Given** a review verdict of PASS, **When** the user types "确认无误" or "下一步", **Then** the system highlights the "确认进入下一阶段" button but does not automatically advance—the user must click the physical button.
4. **Given** the user is unsatisfied with the entire result, **When** they type "重做", **Then** the Router identifies the intent as `regenerate`, the current requirements are discarded, and the AI regenerates from scratch.

---

### User Story 3 - Clarify Missing Information (Priority: P2)

When the AI cannot determine certain video parameters from the user's description (e.g., specific angle, target duration, platform), it raises targeted clarification questions rather than guessing. The content creator can answer these questions inline—either by selecting quick-reply options or typing free-text responses. Each answer triggers a revision that merges the new information into the requirements without changing fields the user already confirmed.

**Why this priority**: Clarifications prevent the system from making wrong assumptions that would cascade through the entire production pipeline.

**Independent Test**: Can be tested by submitting a vague description (e.g., "做一个金融分析视频"), verifying that clarification questions appear for missing dimensions, and confirming that answering them updates the requirements.

**Acceptance Scenarios**:

1. **Given** a user description that lacks specific angle, duration, or platform, **When** the RequirementsAgent generates requirements, **Then** the summary card shows a "需要你补充" section with specific clarification questions and quick-reply option buttons.
2. **Given** clarification questions displayed, **When** the user clicks a quick-reply option (e.g., "技术角度"), **Then** the Router identifies the intent as `revise`, the AI merges the selected answer into the requirements, and the clarification question disappears from the updated card.
3. **Given** all clarification questions have been answered, **When** the requirements are regenerated, **Then** the `clarification_needed` array is empty and no new clarification questions appear for already-answered dimensions.

---

### User Story 4 - Advance to Next Phase (Priority: P1)

Once requirements are complete and reviewed, the content creator clicks a physical "确认进入下一阶段" button. The system runs a programmatic gate check (GateKeeper) verifying: the requirements artifact exists and is valid, the review passed, and no tasks are still running. If all checks pass, Phase 0 is marked complete, the pipeline advances to Phase 1, and the frontend navigation updates to reflect the new state.

**Why this priority**: Advancing is the gate that transitions work from one phase to the next—without it, the pipeline stalls.

**Independent Test**: Can be tested by completing all Phase 0 requirements, clicking the advance button, and verifying the phase status changes to "done", the navigation shows Phase 0 with a green checkmark, and Phase 1 becomes active.

**Acceptance Scenarios**:

1. **Given** all GateKeeper conditions are met (artifact valid, review passed, no running tasks), **When** the user clicks "确认进入下一阶段", **Then** Phase 0 is marked done, and the system transitions to Phase 1.
2. **Given** the review has failed (verdict = FAIL), **When** the user views the advance button, **Then** it is disabled and shows the reason: "审核未通过" with specific blocking issues listed.
3. **Given** tasks are still running, **When** the user views the advance button, **Then** it is disabled and shows: "仍有任务正在执行中，请等待完成".
4. **Given** Phase 0 is marked done, **When** the user views the phase navigation, **Then** Phase 0 shows a green checkmark and Phase 1 is highlighted as active.

---

### Edge Cases

- What happens when the user closes the browser mid-generation? On re-opening, the system recovers the full project state from persistent storage and renders the current state including any in-progress tasks.
- What happens when the RequirementsAgent produces valid JSON but the content is nonsensical? The CompletenessReviewer catches semantic issues (e.g., empty topic, missing identifiable viewpoint) and returns FAIL with specific reasons.
- What happens when the user rapidly sends multiple revise commands? The system processes them sequentially (each triggering a new task and review), with later commands superseding earlier in-progress tasks.
- What happens when the description is extremely long (e.g., 5000 characters)? The system accepts it but the AI extraction may take longer; frontend shows a loading indicator.
- What happens when the LLM API call fails (network error, timeout)? The task is marked as `failed` in the task ledger, an error message is displayed, and the user can retry via the `regenerate` command.
- What happens when the user switches to another phase tab and then back to Phase 0? The phase content is read-only (completed phases cannot be modified), but Phase 0 remains interactive if still in progress.
- What happens when the user clicks the advance button while the review is still running? The advance button remains disabled with the message "仍有任务正在执行中，请等待完成".

## Requirements *(mandatory)*

### Functional Requirements

**Project Creation**
- **FR-001**: System MUST allow users to create a new project by providing a non-empty title and a natural language description of at least 10 characters.
- **FR-002**: System MUST validate title (non-empty) and description (>=10 chars) on the frontend before sending any API request.
- **FR-003**: System MUST generate a unique project ID in the format `proj_YYYYMMDD_NNN` on project creation.
- **FR-004**: System MUST initialize the project's current phase to 0 (Phase 0 entry point) with status `active` on creation.

**AI Requirements Generation**
- **FR-005**: System MUST automatically invoke an AI agent (RequirementsAgent) to analyze the user's natural language description and produce structured video production requirements after project creation.
- **FR-006**: The AI agent MUST extract from the user description: video topic, core viewpoints/content framework, target duration range (if mentioned), and target platform (if mentioned).
- **FR-007**: The AI agent MUST supplement extracted information by looking up platform technical specifications (resolution, bitrate, format) from the platform configuration and matching the content to the best-fit category from the category classification tree.
- **FR-008**: The AI agent MUST calculate target word count range from target duration using the formula: min = duration_min × speech_rate × 0.8, max = duration_max × speech_rate × 1.2, where speech_rate defaults to 240 characters/minute.
- **FR-009**: The AI agent MUST produce a `requirements.json` artifact containing: project_id, title, topic, user_input_content, target_duration_minutes, target_word_count, platform (primary, secondary, specs), category (level1, level2), clarification_needed array, and created_at timestamp.

**Clarification Handling**
- **FR-010**: When critical dimensions are missing from the user's description (specific angle, duration, platform, category), the AI agent MUST mark them in the `clarification_needed` array rather than fabricating values.
- **FR-011**: System MUST display clarification questions in the requirements summary card with quick-reply option buttons where applicable.
- **FR-012**: When the user responds to clarification questions, the system MUST merge only the newly provided information into existing requirements without altering already-confirmed fields.

**Completeness Review**
- **FR-013**: System MUST automatically trigger a CompletenessReviewer audit after each requirements generation or revision.
- **FR-014**: The CompletenessReviewer MUST verify: topic non-empty (>=5 chars), user input content non-empty with at least one identifiable viewpoint, duration constraints valid (min >= 0, max >= min), word count consistent with duration, platform exists in configuration, video specs match platform configuration, category exists in classification tree, and clarification_needed values are valid dimension keys.
- **FR-015**: The CompletenessReviewer MUST output a binary verdict (PASS/FAIL) with notes and blocking issues list.

**User Modification**
- **FR-016**: System MUST allow users to modify requirements through natural language chat input after the initial generation.
- **FR-017**: A Router component MUST classify user chat messages into intents: `revise` (modify specific fields), `regenerate` (discard and redo from scratch), `inject_subtask` (research request — recognized but not yet implemented; system responds with placeholder message "此功能暂未开放"), `request_advance` (express desire to move forward), or `clarify` (ambiguous intent).
- **FR-018**: On `revise`, the system MUST create a new artifact version, supersede the old review, and automatically trigger a new review.
- **FR-019**: On `regenerate`, the system MUST discard the current artifact, regenerate from the original description (with any accumulated user feedback), and trigger a new review.

**Task Visibility**
- **FR-020**: System MUST display a task list showing all Phase 0 tasks (generate_artifact, review) with real-time status updates (pending, running, succeeded, failed, superseded). The task list MUST default to a collapsed view showing only the currently executing task; users can expand the list to view all tasks.
- **FR-021**: Task status MUST update in real time without requiring manual page refresh.

**Advancement Gate**
- **FR-022**: System MUST require the user to click a physical "确认进入下一阶段" button to advance—natural language expressions of intent alone must not trigger advancement.
- **FR-023**: Before advancing, a GateKeeper MUST programmatically verify: requirements artifact exists and passes schema validation, the latest review verdict is PASS, and all tasks in the task ledger are in terminal states.
- **FR-024**: If any GateKeeper check fails, the advance button MUST be disabled with a clear explanation of which conditions are not met.

**State Persistence**
- **FR-029**: System MUST persist all project state (phase status, task ledger, artifacts, dialogue history, preferences) to persistent storage as the authoritative state source, such that state survives server restarts.
- **FR-030**: System MUST support recovery of full project state on browser close/reopen and server restart by reading from persistent storage, with recovery completing within 10 seconds.

### Key Entities

- **Project**: A video production project created by a user. Key attributes: unique project_id, title, natural language description, current_phase, status, creation timestamp.
- **Requirements Artifact** (`requirements.json`): The structured video production requirements generated by the AI. Key attributes: project_id, title, topic, user_input_content, target_duration_minutes (min/max), target_word_count (min/max), platform (primary/secondary/specs), category (level1/level2), clarification_needed array, artifact version number.
- **Task**: A unit of work in the Phase 0 pipeline. Types include generate_artifact (requirements generation), review (completeness audit), user_revision (user-requested modification), research (user-requested lookup). Each task has type, status (pending/queued/running/succeeded/failed/skipped/superseded), and optional dependency on other tasks.
- **Review Verdict**: The output of the CompletenessReviewer. Contains verdict (PASS/FAIL), notes, and blocking issues list.
- **Dialogue History**: The full conversation log between the user and the AI agents during Phase 0, stored as structured messages for recovery and context.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a project and receive AI-generated structured video requirements within 30 seconds of submitting their description.
- **SC-002**: 90% of initial requirements generations produce a valid requirements JSON with all extractable fields populated and correct platform/category lookups.
- **SC-003**: Users can successfully revise requirements through natural language chat—the revised field is updated while all other fields remain unchanged.
- **SC-004**: The CompletenessReviewer catches 100% of schema-validation errors (missing required fields, invalid platform/category values) before advancement.
- **SC-005**: Users can complete the full Phase 0 flow (create -> review -> revise if needed -> confirm -> advance) in under 5 minutes for a typical video description.
- **SC-006**: Project state is fully recoverable within 10 seconds of reopening the browser or after a server restart.
- **SC-007**: The advance button is never enabled when any GateKeeper condition is unmet (zero false-positive gate passes).
- **SC-008**: Clarification questions are raised for all missing critical dimensions, and no fabricated values appear in place of genuinely unknown information.

## Assumptions

- The user has a stable internet connection and uses a modern web browser.
- The AI model (LLM) is available and configured via `config/model_config.json` with the speech rate parameter.
- Platform specifications and category classifications are maintained in `config/platforms.json` and `config/categories.json` respectively, and are available at runtime.
- The user understands Chinese natural language interaction (primary language for Phase 0 chat interface).
- Project IDs use the format `proj_YYYYMMDD_NNN` where NNN is a zero-padded sequential number per day.
- SQLite is used as the persistence layer and is available on the server filesystem.
- The system supports a single user interacting with one project at a time (no multi-user collaboration in Phase 0).
- Completed phases are read-only—users can view past phase artifacts but cannot modify them.
- The frontend communicates with a backend service that supports both request-response and real-time status updates.
- Preference extraction is deferred to a future version and is out of scope for this specification.
