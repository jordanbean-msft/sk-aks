using Microsoft.Extensions.Hosting;

var builder = DistributedApplication.CreateBuilder(args);

var azureOpenAiApiKey = builder.AddParameter("AzureOpenAiApiKey", true);
var azureOpenAiEndpoint = builder.AddParameter("AzureOpenAiEndpoint", true);
var azureOpenAiChatDeploymentName = builder.AddParameter("AzureOpenAiChatDeploymentName", true);
var azureOpenAiEmbeddingDeploymentName = builder.AddParameter("AzureOpenAiEmbeddingDeploymentName", true);
var azureOpenAiApiVersion = builder.AddParameter("AzureOpenAiApiVersion", true);
var azureKubernetesBaseUrl = builder.AddParameter("AzureKubernetesBaseUrl", true);

#pragma warning disable ASPIREHOSTINGPYTHON001
var api = builder.AddDockerfile("api", "../api")
    .WithEnvironment("AZURE_OPENAI_API_KEY", azureOpenAiApiKey)
    .WithEnvironment("AZURE_OPENAI_ENDPOINT", azureOpenAiEndpoint)
    .WithEnvironment("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", azureOpenAiChatDeploymentName)
    .WithEnvironment("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME", azureOpenAiEmbeddingDeploymentName)
    .WithEnvironment("AZURE_OPENAI_API_VERSION", azureOpenAiApiVersion)
    .WithEnvironment("AZURE_KUBERNETES_BASE_URL", azureKubernetesBaseUrl)
    .WithHttpEndpoint(targetPort: 80)
    .WithExternalHttpEndpoints()
    .WithOtlpExporter();
#pragma warning restore ASPIREHOSTINGPYTHON001

if(builder.ExecutionContext.IsRunMode && builder.Environment.IsDevelopment())
{
    api.WithEnvironment("DEBUG", "True");
    api.RunWithHttpsDevCertificate("HTTPS_CERT_FILE", "HTTPS_CERT_KEY_FILE");
}

#pragma warning disable ASPIREHOSTINGPYTHON001
var web = builder.AddDockerfile("web", "../web")
    .WithEnvironment("API_BASE_URL", api.GetEndpoint("http"))
    .WithHttpEndpoint(targetPort: 8501)
    .WithExternalHttpEndpoints()
    .WithOtlpExporter();
#pragma warning restore ASPIREHOSTINGPYTHON001

if(builder.ExecutionContext.IsRunMode && builder.Environment.IsDevelopment())
{
    web.WithEnvironment("DEBUG", "True");
    web.RunWithHttpsDevCertificate("HTTPS_CERT_FILE", "HTTPS_CERT_KEY_FILE");
}

builder.Build().Run();
