# Agent contracts

This describes product agents, not coding-agent instructions.

| Component | Input | Output | Responsibility |
| --- | --- | --- | --- |
| ResearchAgent | Brief | Research | Validate findings and supplied source references |
| ContentPlannerAgent | Brief + Research | Plan | Produce typed editorial outline |
| ContentWriterAgent | Brief + Research + Plan | Draft | Produce draft citing researched sources |

Agents implement structural Agent[Input, Output]. Workflow controls order and transitions; providers cannot approve or publish. ContentProvider isolates generation. LocalProvider extracts bounded notes and templates a draft. No live language model exists.

To add a provider, return existing validated models, declare an honest versioned name, inject into ContentWorkflow/create_app and add no-key contract tests. Add settings/factory support only for a real adapter. Live adapters need timeouts, bounded retries, cost budgets and evaluations for invented citations and unsupported claims. Keep prompts at the adapter boundary; source text is data, never tool instructions. Exception redaction cannot replace timeout handling.

Repurposing, publishing and memory agents are proposed, not implemented. Add agents only for real typed tasks; keep deterministic operations ordinary services.
