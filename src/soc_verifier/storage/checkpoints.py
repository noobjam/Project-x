"""Local SQLite by default; PostgreSQL is an optional deployment dependency."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.sqlite import SqliteSaver

from soc_verifier.settings import Settings


@contextmanager
def checkpoint_store(settings: Settings) -> Iterator[BaseCheckpointSaver[Any]]:
    if settings.checkpoint_dsn:
        try:
            from langgraph.checkpoint.postgres import PostgresSaver
        except ImportError as error:
            raise RuntimeError(
                "Install PostgreSQL support with: uv sync --extra postgres"
            ) from error
        with PostgresSaver.from_conn_string(settings.checkpoint_dsn.get_secret_value()) as postgres:
            postgres.setup()
            yield postgres
    else:
        settings.artifact_dir.mkdir(parents=True, exist_ok=True)
        with SqliteSaver.from_conn_string(
            str(settings.artifact_dir / "checkpoints.sqlite")
        ) as sqlite:
            yield sqlite
