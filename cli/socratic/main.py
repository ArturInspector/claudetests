from __future__ import annotations

import json
from pathlib import Path

import click

from .client import APIClient
from .config import CLIConfig, load_config, save_config


def _get_client(cfg: CLIConfig) -> APIClient:
    if not cfg.token:
        click.echo("You are not logged in. Run `socratic login` first.")
        raise click.Abort()
    return APIClient(cfg.base_url, token=cfg.token)


@click.group()
@click.option(
    "--base-url",
    default=None,
    help="API base URL (default: value from config or http://localhost:8000/api/v1)",
)
@click.pass_context
def cli(ctx: click.Context, base_url: str | None) -> None:
    """Socratic CLI for interacting with the learning API."""
    cfg = load_config()
    if base_url:
        cfg.base_url = base_url.rstrip("/")
        save_config(cfg)
    ctx.obj = cfg


@cli.command()
@click.option("--email", prompt=True)
@click.option("--password", prompt=True, hide_input=True)
@click.pass_obj
def login(cfg: CLIConfig, email: str, password: str) -> None:
    """Authenticate and store the access token."""
    client = APIClient(cfg.base_url)
    token = client.login(email=email, password=password)
    cfg.token = token
    cfg.email = email
    save_config(cfg)
    click.echo("Login successful. Token saved.")


@cli.command("start")
@click.argument("topic")
@click.option("--level", default=None, help="Optional level hint (e.g., beginner)")
@click.pass_obj
def start_session(cfg: CLIConfig, topic: str, level: str | None) -> None:
    """Start a new learning session."""
    client = _get_client(cfg)
    session = client.start_session(topic=topic, level=level)
    click.echo(f"Started session #{session['id']} on '{session['topic']}'.")


@cli.command("list")
@click.pass_obj
def list_sessions(cfg: CLIConfig) -> None:
    """List your sessions."""
    client = _get_client(cfg)
    sessions = client.list_sessions()
    if not sessions:
        click.echo("No sessions found.")
        return
    for item in sessions:
        click.echo(
            f"#{item['id']} | {item['topic']} | iterations={item.get('iteration_count', 0)}"
        )


@cli.command()
@click.argument("session_id", type=int)
@click.option("--question", prompt="Question")
@click.option("--answer", prompt="Answer", help="Your answer to the question")
@click.pass_obj
def answer(cfg: CLIConfig, session_id: int, question: str, answer: str) -> None:
    """Submit an answer and get feedback."""
    client = _get_client(cfg)
    result = client.answer(session_id=session_id, question=question, answer=answer)
    feedback = result["iteration"]["feedback"] or "No feedback returned."
    click.echo("Feedback:\n" + feedback)
    if result.get("similar_context"):
        click.echo("\nSimilar past answers:")
        for i, item in enumerate(result["similar_context"], start=1):
            click.echo(f"{i}. {item}")


@cli.command()
@click.argument("session_id", type=int)
@click.pass_obj
def analyze(cfg: CLIConfig, session_id: int) -> None:
    """Generate a session summary."""
    client = _get_client(cfg)
    result = client.analyze(session_id=session_id)
    click.echo(result.get("summary", "No summary returned."))


@cli.command()
@click.argument("session_id", type=int)
@click.option("--format", "out_format", type=click.Choice(["json", "md"]), default="md")
@click.option("--output", type=click.Path(path_type=Path), default=None)
@click.pass_obj
def export(cfg: CLIConfig, session_id: int, out_format: str, output: Path | None) -> None:
    """Export a session with iterations."""
    client = _get_client(cfg)
    detail = client.session_detail(session_id=session_id)

    if out_format == "json":
        content = json.dumps(detail, indent=2, ensure_ascii=False)
    else:
        lines = [
            f"# Session {detail['id']}: {detail['topic']}",
            f"Level: {detail.get('level') or '-'}",
            "",
        ]
        iterations = detail.get("iterations") or []
        if not iterations:
            lines.append("_No iterations yet._")
        else:
            for it in iterations:
                lines.append(f"## Iteration {it['number']}")
                lines.append(f"**Question:** {it['question']}")
                lines.append(f"**Answer:** {it['answer']}")
                feedback = it.get("feedback") or "—"
                lines.append(f"**Feedback:** {feedback}")
                lines.append("")
        content = "\n".join(lines)

    if output:
        output.write_text(content)
        click.echo(f"Wrote export to {output}")
    else:
        click.echo(content)


if __name__ == "__main__":
    cli()

