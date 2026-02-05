import "@azure-tools/typespec-client-generator-core";
import "./main.tsp";

using Azure.ClientGenerator.Core;

@@clientName(Azure.AI.Projects, "AIProjectClient");

// Shorter method names for SDK datasets operations
@@clientName(Azure.AI.Projects.Datasets.listLatest, "list");
@@clientName(Azure.AI.Projects.Datasets.getVersion, "get");
@@clientName(Azure.AI.Projects.Datasets.deleteVersion, "delete");
@@clientName(Azure.AI.Projects.Datasets.createOrUpdateVersion,
  "createOrUpdate"
);
@@clientName(Azure.AI.Projects.Datasets.startPendingUploadVersion,
  "pendingUpload"
);

// Shorter method names for SDK Index operations
@@clientName(Azure.AI.Projects.Indexes.listLatest, "list");
@@clientName(Azure.AI.Projects.Indexes.getVersion, "get");
@@clientName(Azure.AI.Projects.Indexes.deleteVersion, "delete");
@@clientName(Azure.AI.Projects.Indexes.createOrUpdateVersion, "createOrUpdate");

// Less generic names
@@clientName(Azure.AI.Projects.Sku, "ModelDeploymentSku");
@@clientName(Azure.AI.Projects.SasCredential, "BlobReferenceSasCredential"); // Not to be confused with class "SASCredentials"

// More accurate naming
@@clientName(Azure.AI.Projects.AssetCredentialResponse, "DatasetCredential");

// Less generic names for C# SDK (avoid one-word class names)
@@clientName(Azure.AI.Projects.BlobReference,
  "AIProjectBlobReference",
  "csharp"
);
@@clientName(Azure.AI.Projects.Connection, "AIProjectConnection", "csharp");
@@clientName(Azure.AI.Projects.Deployment, "AIProjectDeployment", "csharp");
@@clientName(Azure.AI.Projects.DeploymentType,
  "AIProjectDeploymentType",
  "csharp"
);
@@clientName(Azure.AI.Projects.FieldMapping,
  "AIProjectIndexFieldMapping",
  "csharp"
);
@@clientName(Azure.AI.Projects.Index, "AIProjectIndex", "csharp");
@@clientName(Azure.AI.Projects.CosmosDBIndex,
  "AIProjectCosmosDBIndex",
  "csharp"
);
@@clientName(Azure.AI.Projects.BaseCredentials,
  "AIProjectConnectionBaseCredential",
  "csharp"
);
@@clientName(Azure.AI.Projects.ApiKeyCredentials,
  "AIProjectConnectionApiKeyCredential",
  "csharp"
);
@@clientName(Azure.AI.Projects.CustomCredential,
  "AIProjectConnectionCustomCredential",
  "csharp"
);
@@clientName(Azure.AI.Projects.EntraIDCredentials,
  "AIProjectConnectionEntraIdCredential",
  "csharp"
);
@@clientName(Azure.AI.Projects.SASCredentials,
  "AIProjectConnectionSasCredential",
  "csharp"
);
@@clientName(Azure.AI.Projects.DatasetVersion, "AIProjectDataset", "csharp");
@@clientName(Azure.AI.Projects.FileDatasetVersion, "FileDataset", "csharp");
@@clientName(Azure.AI.Projects.FolderDatasetVersion, "FolderDataset", "csharp");

// Do not use terms "request" or "response" in C# class names as these are REST API terms
@@clientName(Azure.AI.Projects.PendingUploadRequest,
  "PendingUploadConfiguration",
  "csharp"
);
@@clientName(Azure.AI.Projects.PendingUploadResponse,
  "PendingUploadResult",
  "csharp"
);

// Less generic names for C# subclients
@@clientName(Azure.AI.Projects.Connections,
  "AIProjectConnectionsOperations",
  "csharp"
);
@@clientName(Azure.AI.Projects.Datasets,
  "AIProjectDatasetsOperations",
  "csharp"
);
@@clientName(Azure.AI.Projects.Deployments,
  "AIProjectDeploymentsOperations",
  "csharp"
);
@@clientName(Azure.AI.Projects.Indexes, "AIProjectIndexesOperations", "csharp");

// Need to explicitly make all get and list methods include the object name for C#
@@clientName(Azure.AI.Projects.Connections.get, "getConnection", "csharp");
@@clientName(Azure.AI.Projects.Connections.getWithCredentials,
  "getConnectionWithCredentials",
  "csharp"
);
@@clientName(Azure.AI.Projects.Connections.list, "listConnections", "csharp");
@@clientName(Azure.AI.Projects.Datasets.getVersion, "getDataset", "csharp");
@@clientName(Azure.AI.Projects.Datasets.listLatest, "listDatasets", "csharp");
@@clientName(Azure.AI.Projects.Datasets.listVersions,
  "listDatasetVersions",
  "csharp"
);
@@clientName(Azure.AI.Projects.Deployments.get, "getDeployment", "csharp");
@@clientName(Azure.AI.Projects.Deployments.list, "listDeployments", "csharp");
@@clientName(Azure.AI.Projects.Indexes.getVersion, "getIndex", "csharp");
@@clientName(Azure.AI.Projects.Indexes.listLatest, "listIndexes", "csharp");
@@clientName(Azure.AI.Projects.Indexes.listVersions,
  "listIndexVersions",
  "csharp"
);

// Make these two internal, since all SDKs hand-write a single public method with boolean "includeCredentials"
// input parameter that calls either on these two.
@@access(Azure.AI.Projects.Connections.get, Access.internal);
@@access(Azure.AI.Projects.Connections.getWithCredentials, Access.internal);

// Python-specific customizations to address APIView feedback
// Rename parameters that shadow Python built-ins

// Line 1956: AzureAISearchIndex - rename 'type' parameter to avoid shadowing built-in
// Note: This applies to the model's discriminator property which becomes a parameter in __init__
// The 'type' property in Index models should be renamed to 'index_type' for Python
@@clientName(Azure.AI.Projects.Index.type, "index_type", "python");
@@clientName(Azure.AI.Projects.AzureAISearchIndex.type, "index_type", "python");
@@clientName(Azure.AI.Projects.CosmosDBIndex.type, "index_type", "python");
@@clientName(Azure.AI.Projects.ManagedAzureAISearchIndex.type, "index_type", "python");

// Line 3964: FileDatasetVersion - rename 'type' parameter to 'data_type'
@@clientName(Azure.AI.Projects.DatasetVersion.type, "data_type", "python");
@@clientName(Azure.AI.Projects.FileDatasetVersion.type, "data_type", "python");
@@clientName(Azure.AI.Projects.FolderDatasetVersion.type, "data_type", "python");

// Line 7184: ModelDeployment - rename 'type' parameter
@@clientName(Azure.AI.Projects.ModelDeployment.type, "deployment_type", "python");

// Line 2737: Connection.credentials - The 'type' discriminator in credentials
@@clientName(Azure.AI.Projects.BaseCredentials.type, "credential_type", "python");
@@clientName(Azure.AI.Projects.ApiKeyCredentials.type, "credential_type", "python");
@@clientName(Azure.AI.Projects.EntraIDCredentials.type, "credential_type", "python");
@@clientName(Azure.AI.Projects.CustomCredential.type, "credential_type", "python");
@@clientName(Azure.AI.Projects.SASCredentials.type, "credential_type", "python");
@@clientName(Azure.AI.Projects.NoAuthenticationCredentials.type, "credential_type", "python");

// Rename 'type' discriminator in other models
@@clientName(Azure.AI.Projects.InputData.type, "data_type", "python");
@@clientName(Azure.AI.Projects.InputDataset.type, "data_type", "python");
@@clientName(Azure.AI.Projects.EvaluationTarget.type, "target_type", "python");
@@clientName(Azure.AI.Projects.modelResponseGenerationTarget.type, "target_type", "python");
