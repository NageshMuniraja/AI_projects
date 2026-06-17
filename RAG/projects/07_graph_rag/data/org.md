# Helios Cloud — Org & Service Ownership (sample for Graph RAG)

> Facts are deliberately spread across separate sentences. Answering multi-hop questions
> requires CHAINING them — which is exactly where graph traversal beats vector similarity.

Maya Lin is the Chief Executive Officer of Helios Cloud.

Raj Patel is the VP of Engineering and reports to Maya Lin.

Lena Ortiz is an engineering manager and reports to Raj Patel.

Tom Reyes is an engineering manager and reports to Raj Patel.

The Sol control plane handles account state and billing, and is owned by Lena Ortiz.

The Ledger storage engine powers Helios Store and is owned by Tom Reyes.

The Relay message bus powers Helios Pipe and is owned by Priya Shah.

Priya Shah is an engineering manager and reports to Raj Patel.

Sam Cole is a software engineer and reports to Lena Ortiz.

Dana Kim is a software engineer and reports to Lena Ortiz.

Helios Store depends on the Ledger storage engine.

Helios Pipe depends on the Relay message bus.

The billing service depends on the Sol control plane.

Sam Cole is the primary on-call engineer for the Sol control plane.
