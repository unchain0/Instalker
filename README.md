# Instalker

## About the project

Instalker is a tool designed to automate the download of Instagram profiles.
Using the instaloader library, the project allows users to log in to their Instagram accounts and download information from specific profiles in an efficient and organized way.
The tool is configurable and can be customized to meet users' specific needs.

## Requirements

1. [Mozilla Firefox](https://www.mozilla.org/pt-BR/firefox/new/)
2. Instagram account

## Setup

1. Clone this repo.

    ```bash
    git clone --depth=1 https://github.com/bysedd/Instalker.git
    ```

2. Open folder in your code editor preferred.
3. Log in to your Instagram account via Firefox.
    * The project uses cookies to make downloads more efficient. So **don't use** the option to delete cookies when you exit Firefox.
4. Follow the instructions bellow.

## Instructions

1. Install environment (make sure you have [poetry](https://python-poetry.org/docs/#installation) installed)

    ```bash
    poetry install
    ```

2. Open `target_users-example.json` and add the desired Instagram users.
    * Do not include @ symbol.
3. Rename `target_users-example.json` to `target_users.json`
4. Run `main.py` and enjoy.
