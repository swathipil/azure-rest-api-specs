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

// --------------------------------------------------------------------------------
// Python-specific customizations for APIView feedback
// --------------------------------------------------------------------------------

// Line 2287: BlobReferenceSasCredential (SasCredential) - rename 'type' parameter
@@clientName(Azure.AI.Projects.SasCredential.type, "credentialType", "python");

// Line 1956, 3964: Rename 'type' parameters in Dataset models to avoid shadowing built-in
@@clientName(Azure.AI.Projects.DatasetVersion.type, "dataType", "python");

// Line 1956: AzureAISearchIndex - rename 'type' parameter
@@clientName(Azure.AI.Projects.Index.type, "indexType", "python");

// Line 7184: ModelDeployment - rename 'type' parameter
@@clientName(Azure.AI.Projects.Deployment.type, "deploymentType", "python");

// Line 7278: NoAuthenticationCredentials - rename 'type' parameter  
@@clientName(Azure.AI.Projects.NoAuthenticationCredentials.type, "credentialType", "python");

// Rename 'type' in other credential models for consistency
@@clientName(Azure.AI.Projects.BaseCredentials.type, "credentialType", "python");
@@clientName(Azure.AI.Projects.ApiKeyCredentials.type, "credentialType", "python");
@@clientName(Azure.AI.Projects.EntraIDCredentials.type, "credentialType", "python");
@@clientName(Azure.AI.Projects.CustomCredential.type, "credentialType", "python");
@@clientName(Azure.AI.Projects.SASCredentials.type, "credentialType", "python");

// Evaluations - rename 'type' discriminators
@@clientName(Azure.AI.Projects.EvaluationTarget.type, "targetType", "python");
@@clientName(Azure.AI.Projects.InputData.type, "dataType", "python");

// Red Teams - rename 'type' discriminator
@@clientName(Azure.AI.Projects.TargetConfig.type, "configType", "python");

// Line 2737: Connection.credentials should be Optional (mark as optional in Python)
// Note: This is handled by the TypeSpec definition already having credentials as required
// If this needs adjustment, it should be done in the model definition itself

// Line 3939, 4058: FileDatasetVersion.tags and FolderDatasetVersion.tags should be Optional
// Note: These inherit from AssetBase where tags is already optional
