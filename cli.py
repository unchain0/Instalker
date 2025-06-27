from datetime import timedelta
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy.orm import Session

from src import FileManager, Instagram, get_session, setup_logging
from src.core.db import Profile, SessionLocal

app = typer.Typer(
    help="A CLI for managing Instalker target users.",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
)

console = Console()


def _get_db_session() -> Session:
    """Helper function to get a database session."""
    return SessionLocal()


@app.command(name="list", help="List all target users.")
def list_users(
    privacy: Annotated[
        str,
        typer.Option(
            "--privacy",
            "-p",
            help="Filter users by privacy type (public, private, all).",
            rich_help_panel="Filtering and Sorting",
            case_sensitive=False,
            show_default=True,
            show_choices=True,
            # Callback to validate the privacy option
            callback=lambda value: value.lower() if value else "all",
        ),
    ] = "all",
) -> None:
    """Lists all public and private target users in a table from the database."""
    with _get_db_session() as db:
        query = db.query(Profile)
        if privacy == "public":
            query = query.filter(Profile.is_private.is_(False))
        elif privacy == "private":
            query = query.filter(Profile.is_private.is_(True))
        profiles = query.all()

    table = Table(title="Target Users (from Database)")
    table.add_column("Username", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Full Name", style="green")
    table.add_column("Followers", style="blue")
    table.add_column("Last Checked", style="yellow")

    for profile in profiles:
        user_type = "Private" if profile.is_private else "Public"
        table.add_row(
            profile.username,
            user_type,
            profile.full_name or "N/A",
            str(profile.followers) if profile.followers is not None else "N/A",
            str(profile.last_checked) if profile.last_checked else "N/A",
        )

    console.print(table)


@app.command(help="Add a new target user.")
def add(
    username: Annotated[
        str,
        typer.Argument(..., help="The Instagram username to add.", show_default=False),
    ],
    private: bool = typer.Option(
        False,  # Default value
        "--private",
        "-p",
        help="Flag to mark the user as a private profile.",
    ),
) -> None:
    """Adds a user to the database."""
    with _get_db_session() as db:
        existing_profile = db.query(Profile).filter_by(username=username).first()
        if existing_profile:
            console.print(f"[bold yellow]Skipped:[/] User '[cyan]{username}[/]' already exists in the database.")
            return

        new_profile = Profile(username=username, is_private=private)
        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)

    user_type = "private" if private else "public"
    console.print(f"[bold green]Success:[/] User '[cyan]{username}[/]' added to the database as a {user_type} profile.")


@app.command(help="Remove a target user.")
def remove(
    username: Annotated[
        str,
        typer.Argument(..., help="The Instagram username to remove.", show_default=False),
    ],
) -> None:
    """Removes a user from the database."""
    with _get_db_session() as db:
        profile_to_remove = db.query(Profile).filter_by(username=username).first()
        if profile_to_remove:
            db.delete(profile_to_remove)
            db.commit()
            console.print(f"[bold green]Success:[/] User '[cyan]{username}[/]' removed from the database.")
        else:
            console.print(f"[bold red]Error:[/] User '[cyan]{username}[/]' not found in the database.")


@app.command(help="Clean old downloaded files.")
def clean(
    days: Annotated[
        int,
        typer.Option(
            "--days",
            "-d",
            help="Number of days old files to remove.",
            min=1,
            show_default=True,
        ),
    ] = 15,
) -> None:
    """Removes downloaded files older than a specified number of days."""
    logger = setup_logging()
    try:
        fm = FileManager()
        fm.remove_old_files(cutoff_delta=timedelta(days=days))
        logger.info("Cleaned files older than %d days.", days)
    except Exception:
        logger.exception("An error occurred during cleaning.")


@app.command(help="Download Instagram profiles.")
def download(
    privacy: Annotated[
        str,
        typer.Option(
            "--privacy",
            "-p",
            help="Filter users by privacy type for download (public, private, all).",
            rich_help_panel="Filtering and Sorting",
            case_sensitive=False,
            show_default=True,
            show_choices=True,
            callback=lambda value: value.lower() if value else "all",
        ),
    ] = "all",
    clean_days: Annotated[
        int,
        typer.Option(
            "--clean-days",
            "-c",
            help="Number of days old files to remove before download.",
            min=0,
            show_default=True,
        ),
    ] = 0,
) -> None:
    """Downloads Instagram profiles based on privacy settings."""
    logger = setup_logging()
    try:
        if clean_days > 0:
            fm = FileManager()
            fm.remove_old_files(cutoff_delta=timedelta(days=clean_days))
            logger.info("Cleaned files older than %d days before download.", clean_days)

        with get_session() as main_db_session:
            instagram = Instagram(
                db=main_db_session,
                highlights=False,
                privacy_filter=privacy,
            )
            instagram.run()
        logger.info("Instagram processing finished successfully.")
    except Exception:
        logger.exception("An error occurred during download.")


if __name__ == "__main__":
    app()
