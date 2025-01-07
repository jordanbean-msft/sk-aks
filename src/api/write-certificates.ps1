[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$resourceGroupName,
    [Parameter(Mandatory = $true)]
    [string]$aksClusterName
)

Import-Module powershell-yaml

# Define the paths
$basePath = Join-Path -Path $PSScriptRoot -ChildPath "app/data"
$clusterPath = Join-Path -Path $basePath -ChildPath $aksClusterName
$kubeconfigPath = Join-Path -Path $clusterPath -ChildPath "config"
$outputCaPemPath = Join-Path -Path $clusterPath -ChildPath "ca.pem"
$outputCertPemPath = Join-Path -Path $clusterPath -ChildPath "cert.pem"
$outputKeyPemPath = Join-Path -Path $clusterPath -ChildPath "key.pem"

# Create the directory for the cluster
New-Item -Path $clusterPath -ItemType Directory -Force

# Get the AKS credentials and write to the kubeconfig file
az aks get-credentials --resource-group $resourceGroupName --name $aksClusterName --file - | Out-File -FilePath $kubeconfigPath -Force

# Read the kubeconfig file
$kubeconfig = Get-Content -Path $kubeconfigPath -Raw | ConvertFrom-Yaml

# Extract the CA certificate
$caCertificate = $kubeconfig.clusters[0].cluster."certificate-authority-data"
$decodedCaCertificate = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($caCertificate))
Set-Content -Path $outputCaPemPath -Value $decodedCaCertificate

# Extract the client certificate
$clientCertificate = $kubeconfig.users[0].user."client-certificate-data"
$decodedClientCertificate = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($clientCertificate))
Set-Content -Path $outputCertPemPath -Value $decodedClientCertificate

# Extract the client key
$clientKey = $kubeconfig.users[0].user."client-key-data"
$decodedClientKey = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($clientKey))
Set-Content -Path $outputKeyPemPath -Value $decodedClientKey

Write-Host "CA certificate has been extracted to $outputCaPemPath"
Write-Host "Client certificate has been extracted to $outputCertPemPath"
Write-Host "Client key has been extracted to $outputKeyPemPath"