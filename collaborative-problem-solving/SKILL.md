---
name: Collaborative Problem Solving
description: Guidelines for avoiding rash file modifications, analyzing problems thoroughly, and discussing solutions with the user before execution.
---

# Structured Debugging and Collaboration

This skill defines a disciplined approach to debugging and problem-solving, emphasizing analysis, discussion, and planning over immediate code modification and job execution.

## Core Principles

1.  **Do Not Act Rashly**: Do not immediately start modifying files or running jobs as soon as you see an error or a request.
2.  **Analyze the Context**: Take time to analyze the surrounding code (周边东西), the system architecture, and potential side effects.
3.  **Propose and Discuss**: Before making non-trivial changes or running expensive jobs, formulate possible solutions, ask questions, and discuss them with the user.
4.  **Solve the Right Problem**: Ensure you understand the root cause and seek standard, idiomatic solutions (e.g., using framework registration mechanisms) rather than ad-hoc hacks.
5.  **Divide and Conquer**: If a change or feature is too large, break it down into 2-3 smaller, manageable tasks or problems. Discuss and analyze with the user first before starting implementation.
6.  **Small Commits for Rollback Safety**: Adopt a "small steps, fast running" (小步快跑) approach. For changes that are confirmed and have high confidence, request user approval to create a git commit. This creates a safe checkpoint and makes it easier to roll back if subsequent high-risk experiments fail.


## Workflow

1.  **Observation**: When a problem is identified or a task is given, read the relevant code and logs thoroughly.
2.  **Deep Analysis**:
    *   Analyze the data structures involved.
    *   Consider alternative solutions.
    *   Formulate a plan.
3.  **Proposal**: Present the analysis and proposed solutions to the user.
4.  **Discussion**: Wait for user feedback and approval.
5.  **Execution**: Proceed with the agreed-upon plan.

## Examples

*   **Anti-pattern**: Seeing a serialization error with integer keys and immediately writing a helper to recursively stringify all dict keys in a central wrapper without knowing the specific data structure.
*   **Best Practice**: Pausing to ask which data structure has the problem, suggesting the use of `jax.export.register_pytree_node_serialization`, and adding informative error messages to help the user identify the structure in future runs.
