# sk-aks

![architecture](./.img/architecture.drawio.svg)

## Disclaimer

**THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.**

## Prerequisites

- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
- Azure subscription & resource group
- [Python](https://www.python.org/downloads/)
- [Docker](https://docs.docker.com/desktop/setup/install/windows-install/)

## Deployment

## Local

Perform each of the following sections in a new shell window.

### Api

1.  Navigate into the `src/api` directory

    ```shell
    cd src/api
    ```

1.  Create a `.env` file with the following values.

    ```txt
    AZURE_OPENAI_MODEL_DEPLOYMENT_NAME=
    AZURE_AI_AGENT_PROJECT_CONNECTION_STRING=
    APPLICATION_INSIGHTS_CONNECTION_STRING=
    CLIENT_ID=
    CLIENT_SECRET=
    TENANT_ID=
    AZURE_MONITOR_QUERY_ENDPOINT=
    ```

1.  Create a virtual environment

    ```shell
    python -m venv .venv
    ```

1.  Activate the virtual environment (Windows)

    ```shell
    ./.venv/Scripts/activate
    ```

1.  Install the prerequisites

    ```shell
    pip install -r .\requirements.txt
    ```

1.  Run the API

    ```shell
    python -m uvicorn app.main:app --env-file .env --log-level debug
    ```

### Web

1.  Open a new shell

1.  Navigate to the `src/web` directory

    ```shell
    cd src/web
    ```

1.  Create a virtual environment

    ```shell
    python -m venv .venv
    ```

1.  Activate the virtual environment (Windows)

    ```shell
    ./.venv/Scripts/activate
    ```

1.  Install the prerequisites

    ```shell
    pip install -r .\requirements.txt
    ```

1.  Set an environment variable with the URL & port of the API (PowerShell)

    ```shell
    $env:services__api__api__0="http://127.0.0.1:8000"
    ```

1.  Run the web app

    ```shell
    streamlit run ./app.py
    ```

1.  Navigate to the URL that is printed

## Links
