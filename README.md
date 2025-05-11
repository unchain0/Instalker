# 📸 Instalker

**Instalker** is an educational project that automates the download of Instagram profile data and media,
leveraging the `instaloader` library and storing profile information in a PostgreSQL database.

## ⚠️ Warnings

Some considerations and recommendations when using this project.

1. **Large Target Lists:** Avoid excessively large target lists (e.g., >200) per account due to Instagram limitations. Consider splitting targets across multiple Instagram accounts if necessary.
2. **Highlights:** Downloading highlights significantly increases download time, especially with many users.
3. **Account Safety:**
    * While using a main account might work (often requiring occasional captcha verification), using a dedicated, established account is generally safer.
    * New/unused accounts might be flagged or blocked more quickly.
    * **Using a VPN might increase the risk of account flagging or banning.**
4. **Tagged Posts:** Downloading `tagged` posts for many users can trigger temporary blocks from Instagram.
5. **Database:** Ensure your PostgreSQL server is running before starting the application.

## ✨ Main Features

* **Automated Downloads:** Retrieve photos, videos, stories, and profile metadata.
* **Database Persistence:** Stores profile information (metadata, relationships) in a PostgreSQL database.
* **Session Reuse:** Utilizes Firefox session cookies for authentication, improving performance and reducing login prompts.
* **Configurable:** Target specific users or groups (all, public, private) via database entries or runtime flags.
* **Initial Import:** Can populate the database initially from user lists in JSON files.

## 🛠️ Requirements

1. **[Mozilla Firefox](https://www.mozilla.org/en-US/firefox/download/thanks/)**: Required for session cookie extraction.
2. **[Instagram account](https://www.instagram.com/)**: Needed for authentication to access private profiles and avoid rate limits.
3. **[Python 3](https://www.python.org/downloads/)**: Python 3.10 or higher recommended.
4. **[PostgreSQL](https://www.postgresql.org/download/)**: A running PostgreSQL server (version 12 or higher recommended).
5. **[uv](https://docs.astral.sh/uv/#installation)** (or pip): For Python dependency management.

## 🚀 Setup

1. **Clone the repository:**

    ```bash
    git clone https://github.com/unchain0/Instalker.git
    cd Instalker
    ```

2. **Set up PostgreSQL Database:**
    * Ensure your PostgreSQL server is running.
    * Create a dedicated database for Instalker (e.g., `instalker`):

        ```sql
        CREATE DATABASE instalker;
        ```

    * Note the database user, password, host, port, and database name for the connection URL.

3. **Configure Environment Variables:**
    * Copy the example environment file:

        ```bash
        cp .env.example .env
        ```

    * Edit the `.env` file and set the `DATABASE_URL` variable with your PostgreSQL connection details:

        ```dotenv
        DATABASE_URL="postgresql+psycopg2://YOUR_USER:YOUR_PASSWORD@YOUR_HOST:YOUR_PORT/YOUR_DB_NAME"
        ```

4. **Install Dependencies:**
    * Using `uv` (if `pyproject.toml` is configured):

        ```bash
        uv sync
        ```

5. **Log in to Instagram via Firefox:**
    * Open Firefox and log in to the Instagram account you intend to use.
    * Ensure the login session is saved (cookies are stored).

## 📝 Instructions

1. **(Optional) Initial User Import from JSON:**
    * If you have existing user lists in `src/resources/target/public_users.json` and/or `src/resources/target/private_users.json`, you can perform an initial import.
    * The main script (`main.py`) will **automatically** run this import **only if** the `profiles` table in your database is empty on the first run.
    * Alternatively, you can run the import script manually *before* the first run of `main.py`:

        ```bash
        # Ensure dependencies are installed and .env is configured
        python src/core/import_users.py
        ```

    * Going forward, add/manage users directly in the database or modify the application logic if needed.

2. **Run the Main Script:**
    * Execute `main.py` to start the profile checking and download process:

        ```bash
        # Using uv (if configured)
        uv run python main.py

        # Or directly using Python
        python main.py
        ```

    * The script will connect to the database, fetch target users (based on the `target_users` parameter in `main.py`), check their profiles, update the database, and download new content.
