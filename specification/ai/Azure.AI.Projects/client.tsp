import "@azure-tools/typespec-client-generator-core";
import "./main.tsp";
import "../Azure.AI.Agents/main.tsp";
import "../OpenAI.Assistants/main.tsp";

using Azure.ClientGenerator.Core;

@@clientName(Azure.AI.Projects, "AIProjectClient");

// ================================================================================
// Python-specific customizations to address APIView feedback
// ================================================================================

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

// ================================================================================
// Python-specific customizations to address APIView feedback
// ================================================================================

// Rename 'type' discriminator properties to 'type_' to avoid shadowing Python built-in (multiple feedback items)
@@clientName(Azure.AI.Projects.Index.type, "type_", "python");
@@clientName(Azure.AI.Projects.AzureAISearchIndex.type, "type_", "python");
@@clientName(Azure.AI.Projects.ManagedAzureAISearchIndex.type, "type_", "python");
@@clientName(Azure.AI.Projects.CosmosDBIndex.type, "type_", "python");
@@clientName(Azure.AI.Projects.DatasetVersion.type, "type_", "python");
@@clientName(Azure.AI.Projects.FileDatasetVersion.type, "type_", "python");
@@clientName(Azure.AI.Projects.FolderDatasetVersion.type, "type_", "python");
@@clientName(Azure.AI.Projects.InputData.type, "type_", "python");
@@clientName(Azure.AI.Projects.InputDataset.type, "type_", "python");
@@clientName(Azure.AI.Projects.Connection.type, "type_", "python");
@@clientName(Azure.AI.Projects.Deployment.type, "type_", "python");
@@clientName(Azure.AI.Projects.ModelDeployment.type, "type_", "python");
@@clientName(Azure.AI.Projects.BaseCredentials.type, "type_", "python");
@@clientName(Azure.AI.Projects.ApiKeyCredentials.type, "type_", "python");
@@clientName(Azure.AI.Projects.CustomCredential.type, "type_", "python");
@@clientName(Azure.AI.Projects.EntraIDCredentials.type, "type_", "python");
@@clientName(Azure.AI.Projects.SASCredentials.type, "type_", "python");
@@clientName(Azure.AI.Projects.NoAuthenticationCredentials.type, "type_", "python");
@@clientName(Azure.AI.Projects.SasCredential.type, "type_", "python");

// Additional Python-specific customizations addressing APIView feedback comments
// The azure-ai-projects Python package includes types from Azure.AI.Agents and OpenAI.Assistants,
// so we apply Python customizations to those types here.

// Note: Many of the specific models mentioned in the APIView feedback (like AgentTaxonomyInput, 
// ClickParam, BrowserAutomationPreviewTool, etc.) may be defined in Azure.AI.Agents or 
// OpenAI.Assistants namespaces. Without being able to see their exact definitions in those specs,
// we cannot add customizations for them here. Those customizations should be added to the 
// respective namespace client.tsp files (Azure.AI.Agents/client.tsp or OpenAI.Assistants/client.tsp)
// with Python scope, and they will be picked up when the azure-ai-projects package is generated.
