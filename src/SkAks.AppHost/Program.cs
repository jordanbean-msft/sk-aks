var builder = DistributedApplication.CreateBuilder(args);

var azureOpenAIApiKey = builder.AddParameter(name: "AzureOpenAIApiKey", secret: true);
var azureOpenAIEndpoint = builder.AddParameter(name: "AzureOpenAIEndpoint", secret: true);
var azureOpenAIChatDeploymentName = builder.AddParameter(name: "AzureOpenAIChatDeploymentName", secret: true);
var azureOpenAIEmbeddingDeploymentName = builder.AddParameter(name: "AzureOpenAIEmbeddingDeploymentName", secret: true);
var azureOpenAIApiVersion = builder.AddParameter(name: "AzureOpenAIApiVersion", secret: true);

// var otel = builder.AddContainer("otel", "otel/opentelemetry-collector-contrib", "0.117.0")
//     .WithHttpEndpoint(targetPort: 4317, name: "grpc", env: "PORT_GRPC")
//     .WithHttpEndpoint(targetPort: 4318, name: "http", env: "PORT_HTTP")
//     .WithHttpEndpoint(targetPort: 8888, name: "metrics")
//     .WithBindMount("Configuration/otel/config.yaml", "/etc/otelcol-contrib/config.yaml")
//     .WithEnvironment("ASPIRE_API_KEY", builder.Configuration["AppHost:OtlpApiKey"])
//     .WithOtlpExporter()
//     ;

var apiApp = builder.AddDockerfile("api", "../api", "Dockerfile")
    .WithHttpEndpoint(port: 8001, targetPort: 80, "api")
    .WithExternalHttpEndpoints()
    .WithEnvironment("AZURE_OPENAI_API_KEY", azureOpenAIApiKey)
    .WithEnvironment("AZURE_OPENAI_ENDPOINT", azureOpenAIEndpoint)
    .WithEnvironment("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", azureOpenAIChatDeploymentName)
    .WithEnvironment("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME", azureOpenAIEmbeddingDeploymentName)
    .WithEnvironment("AZURE_OPENAI_API_VERSION", azureOpenAIApiVersion)
    .WithEnvironment("OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED", "true")
    //.WithEnvironment("OTEL_EXPORTER_OTLP_ENDPOINT", otel.GetEndpoint("grpc"))
    //.WaitFor(otel)
    .WithOtlpExporter();
    
var webApp = builder.AddDockerfile("web", "../web", "Dockerfile")
    .WithHttpEndpoint(port: 8000, targetPort: 8501)
    .WithExternalHttpEndpoints()
    .WaitFor(apiApp)
    .WithReference(apiApp.GetEndpoint("api"))
    //.WithEnvironment("OTEL_EXPORTER_OTLP_ENDPOINT", otel.GetEndpoint("grpc"))
    //.WaitFor(otel)
    .WithOtlpExporter();

builder.Build().Run();
