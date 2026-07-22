# Security Policy

## Supported versions

Only the latest released version is supported with security fixes.

## Reporting a vulnerability

Please do **not** open a public issue for a suspected vulnerability.

Use **Security → Report a vulnerability** in this GitHub repository. Include:

- affected integration version and Home Assistant version;
- a minimal reproduction;
- the expected and observed security impact;
- logs with URLs, location names, tokens, and other personal data removed.

Reports will be acknowledged as soon as practical. Please allow time for a fix and coordinated disclosure before publishing details.

## Data and privacy boundaries

The integration sends HTTPS requests to `weather.yahoo.co.jp`. Yahoo can observe the requester IP address, selected municipality page, request time, and User-Agent. Diagnostics intentionally exclude the municipality name, source URL, and forecast contents.
