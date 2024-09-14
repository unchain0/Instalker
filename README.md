# Instalker

## About the project

Instalker is a tool designed to automate the download of Instagram profiles.
Using the instaloader library, the project allows users to log in to their Instagram accounts and download information from specific profiles in an efficient and organized way.
The tool is configurable and can be customized to meet users' specific needs.

## Setup

1. Clone this repo

    ```bash
    git clone --depth=1 https://github.com/bysedd/Instalker.git
    ```

2. Open folder in your code editor preferred
3. Follow the instructions bellow

## Instructions

1. Install environment (make sure you have [poetry](https://python-poetry.org/docs/#installation) installed)

    ```bash
    poetry install
    ```

2. Rename `.env-example` to `.env` and change credentials.
3. Open `constants.py` in utils folder and add the desired Instagram users.
4. Run `main.py` and enjoy.
