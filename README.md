# 📸 Instalker

**Instalker** é um projeto que automatiza o download de perfis do Instagram,
utilizando a biblioteca `instaloader` para uma coleta eficiente e organizada de
dados.

## ✨ Funcionalidades Principais

- **Downloads Automatizados**: Obtenha fotos e vídeos de perfis com apenas
  alguns passos.
- **Configuração Personalizável**: Ajuste os usuários conforme suas necessidades.
- **Eficiência**: Usa cookies para um desempenho mais ágil.

## 🛠️ Requisitos

1. [Mozilla Firefox](https://www.mozilla.org/pt-BR/firefox/new/)
2. Conta no Instagram

## 🚀 Configuração

1. Clone o repositório:

    ```bash
    git clone --depth=1 https://github.com/bysedd/Instalker.git
    ```

2. Abra o projeto no seu editor de código.
3. Faça login no Instagram pelo Firefox.
   - **Nota**: Mantenha os cookies salvos no seu perfil do Firefox.
4. Siga as instruções abaixo.

## 📝 Instruções

1. Instale as dependências (com [Poetry](https://python-poetry.org/docs/#installation)):

    ```bash
    poetry install
    ```

2. Crie e configure os usuários-alvo:
   - Copie e cole o arquivo `users-example.json` na mesma pasta
   e renomeie a cópia para `users.json`.
   - Adicione os nomes de usuário do Instagram, seguindo o padrão do exemplo.

3. Execute o script:

    ```bash
    python main.py
    ```
