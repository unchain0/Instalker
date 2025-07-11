# 📸 Instalker

**Instalker** is an educational project that automates the download of
Instagram profile data and media, leveraging the `instaloader` library
and storing profile information in a PostgreSQL database.

## ⚠️ Warnings

Some considerations and recommendations when using this project.

1. **Large Target Lists:** Avoid excessively large target lists (e.g., >200)
   per account due to Instagram limitations. Consider splitting targets across
   multiple Instagram accounts if necessary.
2. **Highlights:** Downloading highlights significantly increases download time,
   especially with many users.
3. **Account Safety:**
   - While using a main account might work (often requiring occasional captcha
     verification), using a dedicated, established account is generally safer.
   - New/unused accounts might be flagged or blocked more quickly.
   - **Using a VPN might increase the risk of account flagging or banning.**
4. **Tagged Posts:** Downloading `tagged` posts for many users can trigger
   temporary blocks from Instagram.
5. **Database:** Ensure your PostgreSQL server is running before starting the
   application.

## ✨ Main Features

- **Automated Downloads:** Retrieve photos, videos, stories, and profile metadata.
- **Database Persistence:** Stores profile information (metadata, relationships)
  in a PostgreSQL database.
- **Session Reuse:** Utilizes Firefox session cookies for authentication,
  improving performance and reducing login prompts.
- **CLI for User Management:** Easily add, list, and remove target Instagram
  profiles directly from the command line, with data stored in PostgreSQL.

## 🛠️ Requirements

1. **[Mozilla Firefox](https://www.mozilla.org/en-US/firefox/download/thanks/)**:
   Required for session cookie extraction.
2. **[Instagram account](https://www.instagram.com/)**: Needed for authentication
   to access private profiles and avoid rate limits.
3. **[Python 3](https://www.python.org/downloads/)**: Python 3.10 or higher recommended.
4. **[PostgreSQL](https://www.postgresql.org/download/)**: A running PostgreSQL
   server (version 12 or higher recommended).
5. **[uv](https://docs.astral.sh/uv/#installation)**: For Python dependency management.
6. **[Typer](https://typer.tiangolo.com/)**: For building the command-line interface.
7. **[Rich](https://rich.readthedocs.io/en/stable/)**: For beautiful terminal output
   in the CLI.
8. **[SQLAlchemy](https://www.sqlalchemy.org/)**: ORM for database interactions.
9. **[pytest](https://docs.pytest.org/en/stable/)**: For running unit tests.

## 🚀 Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/unchain0/Instalker.git
   cd Instalker
   ```

2. **Set up PostgreSQL Database:**

   - Ensure your PostgreSQL server is running.
   - Create a dedicated database for Instalker (e.g., `instalker`):

     ```sql
     CREATE DATABASE instalker;
     ```

   - Note the database user, password, host, port, and database name for the
     connection URL.

3. **Configure Environment Variables:**

   - Copy the example environment file:

     ```bash
     cp .env.example .env
     ```

   - Edit the `.env` file and set the `DATABASE_URL` variable with your
     PostgreSQL connection details:

     ```dotenv
     DATABASE_URL="postgresql+psycopg2://YOUR_USER:YOUR_PASSWORD@YOUR_HOST:YOUR_PORT/YOUR_DB_NAME"
     ```

4. **Install Dependencies:**

   - Using `uv`:

     ```bash
     uv sync
     ```

5. **Log in to Instagram via Firefox:**
   - Open Firefox and log in to the Instagram account you intend to use.
   - Ensure the login session is saved (cookies are stored).

## 📝 Instructions

### Managing Target Users (CLI)

Use the `cli.py` script to manage your target Instagram profiles directly in the
PostgreSQL database.

- **List all users:**

  ```bash
  python cli.py list
  ```

- **Add a public user:**

  ```bash
  python cli.py add <username>
  ```

- **Add a private user:**

  ```bash
  python cli.py add <username> --private
  ```

- **Remove a user:**

  ```bash
  python cli.py remove <username>
  ```

### Running the Main Application

Execute `main.py` to start the profile checking and download process. The
application will fetch target users directly from the PostgreSQL database.

```bash
# Using uv (if configured)
uv run python main.py

# Or directly using Python
python main.py
```

## 🧑‍💻 Development Setup

This project uses `pre-commit` hooks to ensure code quality and consistency.
The following tools are integrated:

- **[Ruff](https://docs.astral.sh/ruff/)**: For linting and formatting Python code.
- **[Mypy](https://mypy.readthedocs.io/en/stable/)**: For static type checking.
- **[pytest](https://docs.pytest.org/en/stable/)**: For running unit tests.
- **[markdownlint-cli](https://github.com/igorshubovych/markdownlint-cli)**: For
  linting Markdown files.

To set up the pre-commit hooks, run:

```bash
pre-commit install
pre-commit autoupdate
```
