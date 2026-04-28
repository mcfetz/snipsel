# AGENTS.md

## Purpose
This file defines the mandatory workflow for working in this repository with OpenCode.

## Mandatory Rules

### 1. Analyze the project first with `mcp jcodemunch`
Before making any significant change, always use `mcp jcodemunch` to understand the codebase, project structure, dependencies, and relevant files.

**Required behavior:**
- Run `mcp jcodemunch` before starting implementation work.
- Use it to inspect the affected modules, entry points, and architecture.
- Base changes on the discovered project structure instead of assumptions.

**Example:**
```bash
mcp jcodemunch analyze --project-path .
```

---

### 2. Send a notification with `mcp notify` when work is done
When the assigned work is completed, always send a notification using `mcp notify`.

**Required behavior:**
- Notify after the work is finished and pushed.
- Include a short summary of what was done.
- If available, include the branch name, commit SHA, or PR reference.

**Example:**
```bash
mcp notify --message "Work completed and pushed: implemented feature X, fixed issue Y."
```

---

### 3. Always validate changed code with linting or compilation
Every code change must be verified before committing.

**Required behavior:**
- Run the appropriate linter, compiler, build, or equivalent validation step after changes.
- Do not commit code that fails linting, build, or compilation checks.
- If multiple validation steps exist, run the relevant ones for the affected code.

**Examples:**
```bash
npm run lint
npm run build
```

or

```bash
make lint
make test
```

or

```bash
cargo check
```

---

### 4. Always commit and push your work
Completed work must always be committed and pushed to the remote repository.

**Required behavior:**
- Create a commit for every completed logical unit of work.
- Push the commit(s) after validation succeeds.
- Do not leave completed work only in the local working tree.

**Typical flow:**
```bash
git add .
git commit -m "feat: add example change"
git push
```

---

### 5. Commit messages must always be in English
All commit messages must be written in English only.

**Required behavior:**
- Use clear, concise English commit messages.
- Prefer imperative style.
- If the repository uses Conventional Commits, follow them.

**Good examples:**
```text
fix: correct null handling in user service
feat: add project analysis command
refactor: simplify notification workflow
```

---

## Standard Workflow

Follow this sequence for every task:

1. Analyze the repository and affected area with `mcp jcodemunch`.
2. Implement the requested change.
3. Run linting, compilation, build, or other relevant validation.
4. Commit the changes.
5. Push the changes.
6. Send a completion notification with `mcp notify`.

---

## Non-Negotiable Requirements
- Do not skip `mcp jcodemunch` before substantial work.
- Do not skip validation after code changes.
- Do not leave finished work uncommitted or unpushed.
- Do not write commit messages in any language other than English.
- Do not send the final completion update without using `mcp notify`.
