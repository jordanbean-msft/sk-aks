1.  Navigate to autogen directory

    ```shell
    cd src/autogen
    ```

## Build Docker image with kubectl installed & configuration needed to login to cluster

1.  Write out a kubeconfig file for the Docker container to use to authenticate to your cluster

    ```shell
    az aks get-credentials --resource-group rg-sk-aks-eus-dev --name sk-aks --file - > ./CodeExecutor/config
    ```

1.  Build custom Docker image with kubectl installed

    ```shell
    docker build --tag code-executor:v1 ./CodeExecutor
    ```

## Setup Python environment to run Autogen

1.  Create a virtual environment

    ```shell
    python -m venv .venv
    ```

1.  Activate the virtual environment

    ```shell
    .\.venv\Scripts\activate
    ```

1.  Install all dependencies

    ```shell
    pip install -r .\requirements.txt
    ```

## Run Autogen program

1.  Run autogen script

    ```shell
    python app.py
    ```