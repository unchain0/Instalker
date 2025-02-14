# 📸 Instalker

**Instalker** is a project that automates the download of Instagram profiles, leveraging
the `instaloader` library for efficient and organized data collection.

## ⚠️ Warnings

Some considerations and recommendations when using this project.

1. I don't recommend having more than 200 targets, due to Instagram's own limitations;
2. Downloading highlights slows down downloads a LOT, especially if you have a large list of users;
3. There's no problem using your main Instagram account, I've been using mine for a few months now and the most that's happened is a few warnings where I had to solve a captcha to unlock the account.
    3.1 If you use a recent account (no followers, no following, etc...) it can be blocked quickly by Instagram, but after a while you can recover it.
4. I don't recommend downloading `tagged` on a large list of users, making it impossible to use the bot for a few hours, after which it returns to normal.

## ✨ Main Features

* Automated Downloads: Retrieve photos and videos from profiles with just a few steps.
* Customizable Configuration: Adjust target users according to your needs.
* Efficiency: Utilizes cookies for faster performance.

## 🛠️ Requirements

1. [Mozilla Firefox](https://www.mozilla.org/en-US/firefox/download/thanks/) installed
2. An [Instagram account](https://www.instagram.com/)
3. [Python 3](https://www.python.org/downloads/) installed
4. [uv](https://docs.astral.sh/uv/#installation) for dependency management

## 🚀 Setup

1. **Clone the repository:**

    ```bash
    git clone --depth=1 https://github.com/bysedd/Instalker.git
    ```

2. **Navigate to the project directory:**

    ```bash
    cd Instalker
    ```

3. **Log in to Instagram via Firefox:**
    * Open Firefox and log in to your Instagram account.
    * **Note**: Ensure cookies are saved in your Firefox profile.

4. **Install dependencies:**

    ```bash
    uv sync
    ```

## 📝 Instructions

1. **Configure target users:**
    * Copy the example users file:

    ```bash
    cd src/resources/target
    cp users-example.json users.json
    ```

    * Edit `users.json` and add the Instagram usernames you wish to track,
    following the format in the example.

2. **Run the script:**

    Copy the example to the main file

    ```bash
    cp example.py main.py
    ```

    Open the main file and change it according to your needs

    Then run it

    ```bash
    uv run main.py
    ```
