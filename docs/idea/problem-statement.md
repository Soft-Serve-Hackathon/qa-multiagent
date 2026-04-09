# Problem Statement

## Initial idea
An SRE agent that converts multimodal incident reports (text + error image + log file) into enriched Trello tickets with automatic analysis of the e-commerce application codebase, notifies the technical team via Slack and the reporter via email, and closes the loop when the incident is resolved.

## Main problem
In engineering teams operating e-commerce applications, manual incident triage takes between **15 and 45 minutes per incident**. The on-call engineer must:

1. Read and understand the user report (which can be ambiguous or incomplete)
2. Correlate the error with system logs
3. Search the codebase for the affected module or service
4. Create a ticket with enough technical context for another engineer to act
5. Manually notify the correct team channel
6. Remember to update the reporter when the issue is resolved

Each of these steps is manual, repetitive, and prone to classification errors. In e-commerce, **every minute of downtime carries direct costs in lost sales and brand reputation damage**.

## Who is affected

### SRE on-call engineer
The most affected. They receive alerts at any hour, often with incomplete information. They must rebuild the problem context before acting. In high-severity incidents (P1/P2), this triage time is critical.

### Incident reporter
This can be an end user, an internal developer, or an automated monitor. They do not know if their report was received, who is handling it, or when to expect a resolution. The lack of confirmation creates noise: duplicate reports, unnecessary escalations, incomplete tickets.

### Engineering manager / Tech lead
They lack real-time visibility into the status of active incidents. Trello tickets are often created late, with insufficient context, or not created at all if the on-call engineer resolves the problem quickly but does not document it.

## Impact
Without a solution:
- **High MTTR**: average resolution time increases due to manual triage overhead
- **On-call fatigue**: low-value repetitive tasks consume cognitive energy during high-pressure moments
- **Incomplete tickets**: without enough technical context, tickets block later investigation
- **Open loop**: the reporter does not know their incident was resolved unless someone remembers to notify them
- **No traceability**: without structured logs for the triage process, it is impossible to audit what happened and when

## Signals of value
We will know the solution is worthwhile when:
- Triage time drops from ~30 minutes to ~2 minutes (the agent generates the analysis and ticket in seconds)
- The reporter receives automatic confirmation with a ticket number within 60 seconds of submitting the report
- The Trello ticket contains enough technical context (affected module, severity, relevant codebase files) for an engineer to act without back-and-forth with the reporter
- Observability logs allow reconstructing exactly what the agent did at each stage of the pipeline
- The on-call team can operate with `MOCK_INTEGRATIONS=true` in environments without configured credentials and the system still functions
