"""CLI commands for the pipeline feature."""

import click
from env_vault.storage import load_vault, save_vault, vault_exists
from env_vault.pipeline import build_pipeline, run_pipeline, pipeline_summary, PipelineError
from env_vault.sanitize import sanitize_vars
from env_vault.redact import redact_vars


@click.group("pipeline")
def pipeline_cmd():
    """Chain vault transformations in a pipeline."""


@pipeline_cmd.command("run")
@click.argument("vault_name")
@click.password_option(prompt="Vault password", confirmation_prompt=False)
@click.option("--sanitize", is_flag=True, default=False, help="Apply key sanitization step.")
@click.option("--redact", is_flag=True, default=False, help="Apply value redaction step.")
@click.option("--save", "do_save", is_flag=True, default=False, help="Persist result back to vault.")
def pipeline_run(vault_name, password, sanitize, redact, do_save):
    """Run a pipeline of transformations on VAULT_NAME."""
    if not vault_exists(vault_name):
        click.echo(f"Error: vault '{vault_name}' does not exist.", err=True)
        raise SystemExit(1)

    try:
        data = load_vault(vault_name, password)
    except Exception as exc:
        click.echo(f"Error loading vault: {exc}", err=True)
        raise SystemExit(1)

    steps = []
    if sanitize:
        steps.append(("sanitize", lambda d: sanitize_vars(d)))
    if redact:
        steps.append(("redact", lambda d: redact_vars(d)))

    if not steps:
        click.echo("No transformation steps selected. Use --sanitize or --redact.", err=True)
        raise SystemExit(1)

    try:
        pipeline = build_pipeline(steps)
        result, log = run_pipeline(data, pipeline)
    except PipelineError as exc:
        click.echo(f"Pipeline error: {exc}", err=True)
        raise SystemExit(1)

    click.echo(pipeline_summary(log))

    if do_save:
        try:
            save_vault(vault_name, password, result)
            click.echo("Result saved to vault.")
        except Exception as exc:
            click.echo(f"Error saving vault: {exc}", err=True)
            raise SystemExit(1)
    else:
        click.echo("Dry-run mode: use --save to persist changes.")
