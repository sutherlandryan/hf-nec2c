# Engineering execution policy

Every task must declare its class and a concrete scope ceiling before work begins. The task ends
when its stated question is answered; available token, time, or dollar budget is not a reason to
consume more of it.

## Task classes

### DECISION

Use for architecture, licensing, domain contracts, provenance boundaries, and other choices that
are expensive or difficult to reverse. Analyze the evidence and consequences deeply before
implementation. Independent review is appropriate when the decision is consequential.

### RECONNAISSANCE

Use for cheap, reversible experiments that falsify assumptions or identify the first real
blocker. State strict cost and scope ceilings, stop at the first proven blocker or when the
question is answered, and do not add release-grade attestation. Broad hostile review is not
warranted unless reconnaissance code is later proposed as durable infrastructure.

### PRODUCTIONIZATION

Use only after a route works. This class may establish reproducible builds, package and dependency
attestation, process containment, security hardening, release manifests, and complete regression
and qualification appropriate to the intended claim.

## Governing rules

- Analyze irreversible decisions deeply.
- Falsify reversible assumptions cheaply.
- Do not build release infrastructure around an unproven route.
- Make review depth proportional to permanence and consequence.
- Promote successful reconnaissance into durable infrastructure only through a separate
  productionization task.
- State the task class, the exact question, authorized paths, prohibited actions, file/change
  ceiling, experiment ceiling, validation ceiling, and stop condition.
- Describe only the result actually established by the declared class.
- Stop when the stated question is answered.
