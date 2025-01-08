# sk-aks

![architecture](./.img/architecture.png)

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

### Logging

1.  Run the following CLI command to enable the .NET Aspire dashboard to see the OpenTelemetry metrics

    ```shell
    docker run --rm -it -p 18888:18888 -p 4317:18889 --name aspire-dashboard mcr.microsoft.com/dotnet/aspire-dashboard:9.0
    ```

1.  Navigate to the URL (including the `t` parameter) in the browser to see the dashboard

### Api

1.  Navigate into the `src/api` directory

    ```shell
    cd src/api
    ```

1.  Create a `.env` file with the following values.

    ```txt
    AZURE_OPENAI_API_KEY=""
    AZURE_OPENAI_ENDPOINT=""
    AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=""
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=""
    AZURE_OPENAI_API_VERSION=""
    AZURE_KUBERNETES_BASE_URL=""
    ```

#### For each Kubernetes cluster

1.  Generate the authentication certificate files from your AKS cluster. These certificates are used by the
    `src/api/app/plugins/kubernetes_rest_api_plugin` to authenticate to your cluser.

    ```powershell
    .\write-certificates.ps1 -resourceGroupName <resource-group-name> -aksClusterName <aks-cluster-name>
    ```

1.  Create a virtual environment

    ```shell
    python -m venv .venv
    ```

1.  Activate the virtual environment (Windows)

    ```shell
    ./.venv/Scripts/activate
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

1.  Set an environment variable with the URL & port of the API (PowerShell)

    ```shell
    $env:API_BASE_URL="http://127.0.0.1:8000"
    ```

1.  Run the web app

    ```shell
    streamlit run ./app.py
    ```

1.  Navigate to the URL that is printed

## Links
