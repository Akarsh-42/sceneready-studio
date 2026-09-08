# Security policy

## Reporting a vulnerability

Do not open a public issue containing secrets, private screenplay text, exploit details, or personal
information. Contact the repository owner privately through their GitHub profile and include only
the minimum reproduction information needed.

## Credential handling

- Store the Parallel API key and studio access code in Google Secret Manager.
- Never commit credentials, place them in screenshots, or send them in issue comments.
- Use a unique studio code of at least 24 characters and rotate it if exposure is suspected.
- Grant the runtime service account access only to the required secrets and Vertex AI role.
- Do not grant project-wide Owner permissions to solve build or runtime errors.

## Current security scope

SceneReady protects paid API routes with a shared bearer code, bounds request sizes and concurrency,
escapes rendered content, disables interactive API documentation, and sends restrictive response
headers. It does not currently provide individual accounts, durable audit logs, malware scanning,
or enterprise access controls. Treat it as a hackathon demonstration rather than a production legal
or studio compliance system.
