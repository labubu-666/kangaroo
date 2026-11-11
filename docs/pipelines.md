# Pipelines

A pipeline is a container that orchestrates saved functions to reach a business goal. Each step in a pipeline is a saved function, referred to by its name, and each step says which steps run next.

## Definition

A pipeline is a map from step name to a step. Each step refers to a saved function by its ID, and names the steps that run on each outcome:

```json
{
  "fetch": {
    "function_id": "01a1…",
    "on_success": ["summarize"],
    "on_failure": ["notify"]
  },
  "summarize": { "function_id": "01a2…", "on_success": [], "on_failure": [] },
  "notify": { "function_id": "01a3…", "on_success": [], "on_failure": [] }
}
```

The step name identifies the step within the pipeline, so it can differ from the function's name. The same function can appear in several steps, each with its own name. A step with no reference for an outcome ends the run when it has that outcome.

## Running

A run executes the first step, then at each finished step it runs the steps reached by its outcome. A step runs only after all its parents have finished, and it runs when at least one parent reached it. A step that no finished parent reached is skipped, and skipping passes on to its own steps.

A run is SUCCESS when no step failed and FAILURE otherwise. Each step is PENDING, RUNNING, SUCCESS, FAILURE or SKIPPED.
