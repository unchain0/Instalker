# 📸 Instalker

**Instalker** is a project that automates the download of Instagram profiles, leveraging
the `instaloader` library for efficient and organized data collection.

## ✨ Main Features

* Automated Downloads: Retrieve photos and videos from profiles with just a few steps.
* Customizable Configuration: Adjust target users according to your needs.
* Efficiency: Utilizes cookies for faster performance.

## 🛠️ Requirements

1. Mozilla Firefox
2. An Instagram account
3. Python 3 installed
4. Poetry for dependency management

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
    poetry shell
    poetry install
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

    ```bash
    python main.py
    ```

    * Follow the on-screen prompts to customize your download options.
