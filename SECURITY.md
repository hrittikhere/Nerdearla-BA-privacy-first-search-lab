# Security scope

This is an educational single-user system for fictional agreements. It demonstrates
local data flow, explicit provenance, bounded read-only tools, and sandbox policy
inspection. It is not a regulatory certification, hardened multi-tenant service,
or guarantee that all generated answers are correct.

Threats considered: accidental cloud-provider selection, overly broad egress,
untrusted instructions in retrieved documents, arbitrary file/URL tool access,
stale vectors, incompatible embedding models, and accidental publication of data.

Controls include local endpoint validation, no cloud fallback, a credential-free
sandbox kit, loopback MCP publication, DNS-rebinding validation, private database
networking, source hashes, readiness checks, and explicit tool bounds. OpenCode
permissions and read-only tool annotations supplement these controls; they do not
replace operating-system or network enforcement.

The model endpoint outside sbx is part of the local trust boundary. The operator
is responsible for host security, disk encryption, backups, process ownership,
and retention of source files and generated session data.

If reporting a vulnerability, describe the issue without posting credentials,
private documents, or exploitable sensitive outputs in a public issue. Use GitHub
private vulnerability reporting when available on the repository.
