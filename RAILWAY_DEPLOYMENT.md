# AEGIS OMEGA SUPERSTACK — Railway foundation

## Scope

This is a deliberately bounded API foundation. It exposes a public,
non-sensitive health check and authenticated status/formula endpoints. It is
not the full AEGIS/PETS stack and does not provide host telemetry, security
scanning, forensic acquisition, device control, automated blocking, or
persistent evidence storage.

## Endpoints

- `GET /healthz`: public, non-sensitive health response.
- `GET /api/v1/status`: authenticated read-only application status.
- `POST /api/v1/formula/evaluate`: authenticated, bounded PETS Universal
  Formula objective evaluation using the repository's existing
  `run_objective` / `ExecutionEngine` and Sacred Atom specialists.

The formula endpoint accepts an objective, up to 25 provenance-labelled
evidence records, up to 8 domains, and up to 8 options. Evidence submitted to
this endpoint is marked `unverified`; presence of an ID and source is not
proof that a claim is true. It runs nine deterministic task stages with a
five-worker ceiling. It does not call external model providers, access the
network, mutate source files, write canonical memory, or persist submissions.

Interactive API documentation is disabled.

## Required Railway configuration

- Build: repository Dockerfile.
- Start command: Dockerfile CMD.
- Port: Railway-provided `PORT` (defaults to 8080 locally).
- Secret: configure `AEGIS_API_TOKEN` using Railway's secret-variable UI.
  Generate a high-entropy token outside source control. Never commit it or put
  it in logs, issues, screenshots, or this repository.
- Do not add database credentials until a reviewed persistence migration exists.

## Safety and release gates

1. Run `python -m unittest railway_app.test_main -v`.
2. Verify `/healthz`, token enforcement, input validation, and all nine formula
   task stages.
3. Configure the secret in Railway; authenticated endpoints fail closed with
   HTTP 503 until configured.
4. Keep the service private until authentication and network access policies
   have been checked in Railway.
5. Review runtime logs for accidental secret or personal-data disclosure.
6. Confirm cost limits and resource sizing before production operation.

## Deferred integrations

PostgreSQL, object storage, long-running workers, Android bridge, and the legacy
AEGIS API are intentionally not provisioned by this change. Each requires its
own data model, threat model, access policy, backup/restore test, and review.
Legacy routes that perform scans, forensic capture, password auditing, or
blocking must not be exposed through this service.

## License

This addition does not change the repository's existing licensing terms.
Review `LICENSE` and `COMMERCIAL_LICENSE.md` before commercial distribution.
