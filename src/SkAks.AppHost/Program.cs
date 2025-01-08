var builder = DistributedApplication.CreateBuilder(args);

var azureOpenAIApiKey = builder.AddParameter(name: "AzureOpenAIApiKey", secret: true);
var azureOpenAIEndpoint = builder.AddParameter(name: "AzureOpenAIEndpoint", secret: true);
var azureOpenAIChatDeploymentName = builder.AddParameter(name: "AzureOpenAIChatDeploymentName", secret: true);
var azureOpenAIEmbeddingDeploymentName = builder.AddParameter(name: "AzureOpenAIEmbeddingDeploymentName", secret: true);
var azureOpenAIApiVersion = builder.AddParameter(name: "AzureOpenAIApiVersion", secret: true);
var azureKubernetesBaseUrl = builder.AddParameter(name: "AzureKubernetesBaseUrl", secret: true);

var apiApp = builder.AddDockerfile("api", "../api", "Dockerfile")
    .WithHttpEndpoint(port: 8001, targetPort: 80, "api")
    .WithExternalHttpEndpoints()
    .WithEnvironment("AZURE_OPENAI_API_KEY", azureOpenAIApiKey)
    .WithEnvironment("AZURE_OPENAI_ENDPOINT", azureOpenAIEndpoint)
    .WithEnvironment("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", azureOpenAIChatDeploymentName)
    .WithEnvironment("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME", azureOpenAIEmbeddingDeploymentName)
    .WithEnvironment("AZURE_OPENAI_API_VERSION", azureOpenAIApiVersion)
    .WithEnvironment("AZURE_KUBERNETES_BASE_URL", azureKubernetesBaseUrl)
    .WithOtlpExporter();
    
var webApp = builder.AddDockerfile("web", "../web", "Dockerfile")
    .WithHttpEndpoint(port: 8000, targetPort: 8501)
    .WithExternalHttpEndpoints()
    .WaitFor(apiApp)
    .WithReference(apiApp.GetEndpoint("api"))
    .WithOtlpExporter();

builder.Build().Run();
