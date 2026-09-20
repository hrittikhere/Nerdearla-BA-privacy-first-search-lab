# Diagram assets

`workshop-workflow.svg` is the source and delivery format for the workshop's
end-to-end diagram. It is self-contained, scales for projection, has an accessible
title and description, and does not fetch remote assets when GitHub renders it.

The product marks identify the tools used in this repository: Docker and Docker
sbx, Model Context Protocol, OpenCode, Ollama, Python, Qdrant, and SQLite. The
OpenCode wordmark uses the light-background vector from the official
[OpenCode brand assets](https://opencode.ai/brand), matching the supplied reference.
Other SVG marks were sourced from [Simple Icons](https://simpleicons.org/).
The marks retain their published colors and remain trademarks of their respective
owners. All vector paths are embedded locally in the diagram.

When the runtime changes, update the diagram and its numbered explanation in the
main README together. Do not add a component merely because it is common in RAG
systems; the diagram should represent the checked-in workshop configuration.

Keep runtime placement in the top map and process order in the two workflow
lanes. Connect only adjacent cards with short arrows in the gutters. Explain
repeated tool calls and shared services in captions instead of routing return
arrows across cards. Keep product marks, step numbers, and text in separate areas.
Render and inspect the entire SVG after edits, including at README display size.
