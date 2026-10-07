# Phase 18 selected artifact workflow

Keep the selected weights ignored and preserve the original Gate B.2 artifact.
No external upload, LFS migration or automatic training fallback. Provide a small
read-only validator that checks the strict T3 manifest, expected file, byte hash
and optional full strict model/cache loading. It returns concise machine-readable
verification and actionable CLI errors without importing the transformer runtime
for a basic hash check. Track selected artifact provenance separately, describing
the original overlapping-validation selection and Phase17 retained decision.

An owner supplies the exact ignored artifact by an authorized local/private
transfer. A fresh clone checks its trusted Git manifest, hashes the supplied
bytes, prepares the pinned public config/tokenizer cache, then performs strict
loading before starting the API. Documents state exact path, bytes, SHA, owner
source, commands and lack of a repository public download URL. No archive or
installer is needed for this single-file minimum workflow; avoiding one removes
extraction/path-overwrite risks and keeps the established loader authoritative.
