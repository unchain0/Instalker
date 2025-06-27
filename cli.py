from datetime import timedelta
from typing import Annotated, Optional

import typer
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
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
        Optional[str],
        typer.Argument(help="The Instagram username to remove (optional).", show_default=False),
    ] = None,
) -> None:
    """Removes a user from the database."""
    with _get_db_session() as db:
        selected_username = username
        if not selected_username:
            profiles = db.query(Profile.username).all()
            usernames = [p.username for p in profiles]

            if not usernames:
                console.print("[bold red]Error:[/] No users found in the database to remove.")
                raise typer.Exit()

            username_completer = WordCompleter(usernames, ignore_case=True)
            selected_username = prompt("Username to remove: ", completer=username_completer)

        if not selected_username:
            console.print("[bold red]Error:[/] No username provided or selected.")
            raise typer.Exit()

        profile_to_remove = db.query(Profile).filter_by(username=selected_username).first()
        if profile_to_remove:
            db.delete(profile_to_remove)
            db.commit()
            console.print(f"[bold green]Success:[/] User '[cyan]{selected_username}[/]' removed from the database.")
        else:
            console.print(f"[bold red]Error:[/] User '[cyan]{selected_username}[/]' not found in the database.")


@app.command(help="Update a target user's information.")
def update(
    username: Annotated[
        Optional[str],
        typer.Argument(help="The Instagram username to update (optional).", show_default=False),
    ] = None,
    full_name: Annotated[
        Optional[str],
        typer.Option(
            "--full-name",
            "-n",
            help="The new full name for the user.",
            rich_help_panel="Updatable Fields",
        ),
    ] = None,
    biography: Annotated[
        Optional[str],
        typer.Option(
            "--biography",
            "-b",
            help="The new biography for the user.",
            rich_help_panel="Updatable Fields",
        ),
    ] = None,
    is_private: Annotated[
        Optional[bool],
        typer.Option(
            "--private/--no-private",
            "-p/-P",
            help="Set the user's profile to private or public.",
            rich_help_panel="Updatable Fields",
        ),
    ] = None,
) -> None:
    """Updates a user's information in the database.
    If the username is not provided, it will prompt for it interactively.
    """
    with _get_db_session() as db:
        selected_username = username
        if not selected_username:
            profiles = db.query(Profile.username).all()
            usernames = [p.username for p in profiles]

            if not usernames:
                console.print("[bold red]Error:[/] No users found in the database to update.")
                raise typer.Exit()

            username_completer = WordCompleter(usernames, ignore_case=True)
            selected_username = prompt("Username to update: ", completer=username_completer)

        if not selected_username:
            console.print("[bold red]Error:[/] No username provided or selected.")
            raise typer.Exit()

        profile_to_update = db.query(Profile).filter_by(username=selected_username).first()

        if not profile_to_update:
            console.print(f"[bold red]Error:[/] User '[cyan]{selected_username}[/]' not found in the database.")
            raise typer.Exit()

        updated_fields = []
        if full_name is not None:
            profile_to_update.full_name = full_name
            updated_fields.append(f"Full Name to '[green]{full_name}[/]'")
        if biography is not None:
            profile_to_update.biography = biography
            updated_fields.append(f"Biography to '[green]{biography}[/]'")
        if is_private is not None:
            profile_to_update.is_private = is_private
            privacy_str = "Private" if is_private else "Public"
            updated_fields.append(f"Privacy to '[magenta]{privacy_str}[/]'")

        if not updated_fields:
            console.print("[bold yellow]Warning:[/] No fields were provided to update.")
            raise typer.Exit()

        db.commit()
        console.print(f"[bold green]Success:[/] User '[cyan]{selected_username}[/]' updated.")
        for field in updated_fields:
            console.print(f"  - Set {field}")


@app.command(help="Rename a target user.")
def rename(
    old_username: Annotated[
        Optional[str],
        typer.Argument(help="The current username of the user (optional).", show_default=False),
    ] = None,
    new_username: Annotated[
        str,
        typer.Argument(help="The new username for the user.", show_default=False),
    ] = None,
) -> None:
    """Renames a user in the database.
    If the old username is not provided, it will prompt for it interactively.
    """
    with _get_db_session() as db:
        selected_username = old_username
        if not selected_username:
            profiles = db.query(Profile.username).all()
            usernames = [p.username for p in profiles]

            if not usernames:
                console.print("[bold red]Error:[/] No users found in the database to rename.")
                raise typer.Exit()

            username_completer = WordCompleter(usernames, ignore_case=True)
            selected_username = prompt("Username to rename: ", completer=username_completer)

        if not selected_username:
            console.print("[bold red]Error:[/] No username provided or selected.")
            raise typer.Exit()

        if not new_username:
            new_username = prompt("New username: ")
            if not new_username:
                console.print("[bold red]Error:[/] New username cannot be empty.")
                raise typer.Exit()

        profile_to_rename = db.query(Profile).filter_by(username=selected_username).first()

        if not profile_to_rename:
            console.print(f"[bold red]Error:[/] User '[cyan]{selected_username}[/]' not found in the database.")
            raise typer.Exit()

        # Check if the new username already exists
        existing_profile = db.query(Profile).filter_by(username=new_username).first()
        if existing_profile:
            console.print(f"[bold red]Error:[/] User with username '[cyan]{new_username}[/]' already exists.")
            raise typer.Exit()

        profile_to_rename.username = new_username
        db.commit()
        console.print(
            f"[bold green]Success:[/] User '[cyan]{selected_username}[/]' renamed to '[cyan]{new_username}[/]'."
        )


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