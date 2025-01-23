[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$resourceGroupName,
    [Parameter(Mandatory = $true)]
    [string]$aksClusterName
)

Import-Module powershell-yaml

# Define the paths
$apiBasePath = Join-Path -Path $PSScriptRoot -ChildPath "api/app/data"
$webBasePath = Join-Path -Path $PSScriptRoot -ChildPath "web/data"

$kubeconfigFilename = "config"
$outputCaPemFilename = "ca.pem"
$outputCertPemFilename = "cert.pem"
$outputKeyPemFilename = "key.pem"

function Get-CertificateData {
    param (
        [string]$kubeconfigPath
    )

    $kubeconfig = Get-Content -Path $kubeconfigPath -Raw | ConvertFrom-Yaml

    return @{
        caCertificate = $kubeconfig.clusters[0].cluster."certificate-authority-data"
        clientCertificate = $kubeconfig.users[0].user."client-certificate-data"
        clientKey = $kubeconfig.users[0].user."client-key-data"
    }
}

function Write-Certificates {
    param (
        [string]$clusterPath
    )

    # Create the directory for the cluster
    New-Item -Path $clusterPath -ItemType Directory -Force

    $kubeconfigPath = Join-Path -Path $clusterPath -ChildPath $kubeconfigFilename

    # Get the AKS credentials and write to the kubeconfig file
    az aks get-credentials --resource-group $resourceGroupName --name $aksClusterName --file - | Out-File -FilePath $kubeconfigPath -Force

    $certData = Get-CertificateData -kubeconfigPath $kubeconfigPath

    # Extract the CA certificate
    $decodedCaCertificate = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($certData.caCertificate))
    $outputCaPemPath = Join-Path -Path $clusterPath -ChildPath $outputCaPemFilename
    Set-Content -Path $outputCaPemPath -Value $decodedCaCertificate

    # Extract the client certificate
    $decodedClientCertificate = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($certData.clientCertificate))
    $outputCertPemPath = Join-Path -Path $clusterPath -ChildPath $outputCertPemFilename
    Set-Content -Path $outputCertPemPath -Value $decodedClientCertificate

    # Extract the client key
    $decodedClientKey = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($certData.clientKey))
    $outputKeyPemPath = Join-Path -Path $clusterPath -ChildPath $outputKeyPemFilename
    Set-Content -Path $outputKeyPemPath -Value $decodedClientKey

    Write-Host "CA certificate has been extracted to $outputCaPemPath"
    Write-Host "Client certificate has been extracted to $outputCertPemPath"
    Write-Host "Client key has been extracted to $outputKeyPemPath"
}

$apiClusterPath = Join-Path -Path $apiBasePath -ChildPath $aksClusterName

Write-Certificates `
    -clusterPath $apiClusterPath

$webClusterPath = Join-Path -Path $webBasePath -ChildPath $aksClusterName

Write-Certificates `
    -clusterPath $webClusterPath
