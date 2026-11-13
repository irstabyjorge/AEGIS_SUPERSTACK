# Hugging Face protection deployment

The protection pipeline runs validation on pushes/manual dispatch and a scheduled read-only inventory on Mondays. Add a repository Actions secret named `HF_TOKEN` containing a **read-only** Hugging Face token scoped to the intended model, dataset and Space repositories. Do not use a write token for the scheduled inventory job.

The pull-request validation job does not receive the Hugging Face secret. The inventory job never publishes, edits, deletes, or changes repository settings. It produces a downloadable GitHub Actions artifact.

After the first inventory, review the evidence and preserve a copy outside the same GitHub account. Only then consider optional manifest publication from a trusted local environment using a write-scoped token and explicit `--confirm-write` action. The workflow deliberately has no automatic write/publish stage.
