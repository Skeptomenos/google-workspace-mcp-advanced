# Comparison with Upstream

This document summarizes how `google-workspace-mcp-advanced` differs from `taylorwilsdon/google_workspace_mcp`.

## At a Glance

| Area | Upstream | This Project |
|---|---|---|
| Service coverage | Broad Google Workspace coverage | Same core service breadth plus extension work |
| Tooling style | Mature MCP toolset | Expanded toolset and advanced sync workflows |
| Drive workflows | Standard file operations | Bidirectional/local-drive sync oriented workflows |
| Docs rendering focus | General support | Strong Markdown-to-Google-Docs rendering focus |
| Safety defaults | Depends on tool | Mutating flows standardized around dry-run defaults |
| Architecture evolution | Upstream structure | Additional modularization and execution hardening |

## Key Practical Differences

### 1. Sync-first Drive workflows

This project emphasizes local/remote synchronization patterns for Drive and Docs, including workflows designed for ongoing local editing loops.

### 2. Markdown rendering quality for Google Docs

The Docs pipeline is tuned for high-fidelity Markdown conversion and validated against a kitchen-sink style test document.

### 3. Safety for agent-driven writes

Mutating operations use dry-run-first behavior to reduce accidental writes during exploratory prompting.

### 4. Distribution approach

Primary distribution path is `uvx` from PyPI with pinned version support for deterministic team rollouts.

## Who Should Choose This Project

Choose `google-workspace-mcp-advanced` if you need:

- stronger Markdown-to-Docs output quality,
- sync-heavy Drive/Docs workflows,
- safety-oriented defaults for autonomous agent usage,
- pinned uvx-based deployment for predictable team environments.
