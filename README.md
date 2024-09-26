# 📸 Instalker

**Instalker** é um projeto que automatiza o download de perfis do Instagram, utilizando a biblioteca `instaloader` para uma coleta eficiente e organizada de dados.

## ✨ Funcionalidades Principais

- **Downloads Automatizados**: Obtenha fotos e vídeos de perfis com apenas alguns passos.
- **Configuração Personalizável**: Ajuste alvos conforme suas necessidades.
- **Eficiência**: Usa cookies para uma performance mais ágil.

## 🛠️ Requisitos

1. [Mozilla Firefox](https://www.mozilla.org/pt-BR/firefox/new/)
2. Conta no Instagram (alternativa)

## 🚀 Configuração

1. Clone o repositório:

    ```bash
    git clone --depth=1 https://github.com/bysedd/Instalker.git
    ```

2. Abra o projeto no seu editor de código preferido.
3. Faça login no Instagram pelo Firefox.
   - **Nota**: Mantenha os cookies para facilitar os downloads.
4. Siga as instruções abaixo.

## 📝 Instruções

1. Instale as dependências (com [Poetry](https://python-poetry.org/docs/#installation)):

    ```bash
    poetry install
    ```

2. Crie e configure os usuários-alvo:
   - Copie o arquivo `target_users-example.json` e renomeie para `target_users.json`.
   - Adicione os nomes de usuário do Instagram (sem o símbolo `@`).

3. Execute o script:

    ```bash
    python main.py
    ```

---

Bom uso! 😎
