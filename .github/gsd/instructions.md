# GSD Skill Instructions

Use the GSD methodology for all complex tasks. Treat commands like `/gsd-plan` or `gsd-execute` as signals to load the corresponding spec files.

## Core Rules

1. **Spec-Driven Development**: Every non-trivial task MUST start with a `requirements.md` (or `spec.md`) and a `plan.md`. No code should be written until the plan is approved.
2. **Context Engineering**: Before starting work, load `.planning/project.md`, `.planning/roadmap.md`, and `.planning/state.md` to ensure full context.
3. **Phase-Based Workflow**:
    - **Discuss**: Understand the goal and constraints.
    - **Plan**: Create `requirements.md` and `plan.md`.
    - **Execute**: Implement the changes.
    - **Verify**: Validate the work against the success criteria.
4. **Persistent Memory**: Always update `.planning/state.md` after every session or major milestone.
5. **Quality Assurance**: Every major update MUST be checked with `ruff` (linting/formatting) and `pyright` (type checking) to ensure production-grade code quality.

## GSD Documents

- **Project Spec (`.planning/project.md`)**: The "North Star" of the project. High-level goals, tech stack, and core architecture.
- **Roadmap (`.planning/roadmap.md`)**: The list of phases and steps to reach the project goals.
- **State (`.planning/state.md`)**: Long-term memory of recent changes, current blockers, and next steps.
- **Requirements (`.planning/requirements.md`)**: Specific, atomic specs for a feature or bug fix.
- **Plan (`.planning/plan.md`)**: Technical steps to implement the requirements.

## Behavior

- When the user asks for "GSD" or uses a `gsd-*` command, switch to the appropriate phase.
- Prefer spawning specialized subagents for research, planning, or execution if the task is large.
- Always provide a "Next Step" suggestion after completing a task.

## Target Folder Structure

├── tests/              → agent unit tests + evaluation dataset
├── pyproject.toml      → Ruff and Pyright configuration
└── .env                → Environment variables
