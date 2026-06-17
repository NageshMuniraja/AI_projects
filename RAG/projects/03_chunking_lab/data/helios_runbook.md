# Helios Cloud — Engineering Runbook (sample)

> Fictional content for the RAG course. Distinct topics make chunking effects easy to see.

## Architecture Overview

Helios Cloud runs three core services. Helios Compute schedules virtual servers across a fleet of bare-metal hosts using a custom scheduler called Orbit. Helios Store is an object store backed by a distributed log named Ledger. Helios Pipe is a streaming data pipeline built on a message bus named Relay. The control plane coordinates all three through a service called Sol, which holds the source of truth for account state and routing.

## Orbit Scheduler

Orbit places virtual servers onto hosts based on available CPU, memory, and a noisy-neighbor score. When a host exceeds 85 percent CPU for five minutes, Orbit marks it as hot and stops scheduling new servers there. If a host fails a health check three times in a row, Orbit drains it: existing servers are live-migrated to healthy hosts, and the failed host is quarantined for inspection. Live migration copies memory pages in rounds until the remaining dirty set is small enough to pause-and-copy in under 300 milliseconds.

## Ledger Storage Engine

Ledger stores every object write as an append to a replicated log, then compacts logs into immutable segments. Each segment is replicated three times across availability zones. Reads first check a memory cache called Halo; on a miss they read the newest segment containing the key. Compaction runs hourly and merges small segments, dropping superseded versions. If compaction falls behind by more than six hours, an alert pages the storage on-call engineer because read latency degrades as the number of segments grows.

## Relay Message Bus

Relay delivers events at least once and preserves per-key ordering. Producers write to partitions chosen by a hash of the event key. Consumers commit offsets after processing. If a consumer group lags by more than one million events, Relay triggers autoscaling of consumer workers. Poison messages that fail processing five times are routed to a dead-letter topic named Abyss for manual review.

## Sol Control Plane

Sol stores account state, billing status, and routing rules in a replicated relational database. Every request to Compute, Store, or Pipe first authorizes against Sol. If Sol is unreachable, the data services fall back to a cached authorization snapshot that is at most ten minutes old, allowing reads to continue while writes are blocked. This fail-static behavior protects customers during control-plane incidents.

## Incident Response

On any customer-facing incident, the on-call engineer opens an incident channel, assigns an incident commander, and posts updates every fifteen minutes. Severity one incidents (full outage of a service) require paging the engineering manager and posting a public status page update within ten minutes. After resolution, a blameless postmortem is written within five business days and reviewed by the whole team.

## Deployment Process

Code is deployed through a pipeline that runs unit tests, integration tests, and a canary stage. The canary serves one percent of traffic for thirty minutes while error rate and latency are watched. If the canary error rate exceeds 0.5 percent, the deploy is rolled back automatically. Full rollout proceeds region by region, never to more than one region at a time, so a bad deploy can affect at most one region.

## On-Call and Escalation

Each service has a primary and secondary on-call engineer rotating weekly. Pages unacknowledged for ten minutes escalate to the secondary, then to the engineering manager after twenty minutes. On-call engineers are expected to acknowledge within five minutes during business hours and within fifteen minutes overnight. A weekly handoff meeting reviews open issues and recent pages.

## Backup and Disaster Recovery

Ledger segments are backed up daily to a separate cloud provider for defense in depth. Sol's database is backed up every six hours with point-in-time recovery for the last fourteen days. A full disaster-recovery drill is run quarterly: a region is failed over to its standby, and the recovery time objective is two hours with a recovery point objective of fifteen minutes.
