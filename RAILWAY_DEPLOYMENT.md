# AEGIS OMEGA SUPERSTACK — Railway foundation

## Scope

The `railway_app` directory is a deliberately minimal, read-only HTTP
foundation. It is not the full AEGIS/PETS stack and does not claim to provide
host telemetry, security scanning, forensic acquisition, device control,
automated blocking, or persistent evidence storage.

## Endpoints

- `GET /healthz`: public, non-sensitive health response.
- `GET /api/v1/status`: read-only application status; requires a Bearer token.

Interactive API documentation is disabled in this deployment foundation.

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
2. Verify `/healthz` and all authentication tests.
3. Configure the secret in Railway; the authenticated endpoint fails closed
   with HTTP 503 until configured.
4. Keep the service private until authentication and network access policies
   have been checked in Railway.
5. Review runtime logs for accidental secret or personal-data disclosure.
6. Confirm cost limits and resource sizing before accepting a production deploy.

## Deferred integrations

PostgreSQL, object storage, workers, Android bridge, and the legacy AEGIS API
are intentionally not provisioned by this change. Each requires its own data
model, threat model, access policy, backup/restore test, and explicit review.
Legacy API routes that perform scans, forensic capture, password auditing,
or blocking must not be exposed through this service.

## License

This addition does not change the repository's existing licensing terms.
Review `LICENSE` and `COMMERCIAL_LICENSE.md` before commercial distribution.
