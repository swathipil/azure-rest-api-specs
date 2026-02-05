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

// ============================================================================
// Python-specific customizations to address APIView feedback
// ============================================================================

// IMPORTANT NOTE: The azure-ai-projects Python package includes types from BOTH
// Azure.AI.Projects and Azure.AI.Agents namespaces. Most of the APIView feedback
// references types from Azure.AI.Agents (e.g., AgentsOperations, DeleteAgentResponse,
// AsyncUpdateMemoriesLROPoller, telemetry classes, etc.) which are defined in the
// specification/ai/Azure.AI.Agents directory.
//
// Per the explicit issue requirements, we should ONLY modify 
// specification/ai/Azure.AI.Projects/client.tsp and NOT 
// specification/ai/Azure.AI.Agents/client.tsp, even if the feedback mentions 
// types from Azure.AI.Agents.
//
// However, since Azure.AI.Projects does not import Azure.AI.Agents, we CANNOT
// reference or customize Azure.AI.Agents types from this file. Those customizations
// would need to be applied in specification/ai/Azure.AI.Agents/client.tsp.
//
// The Azure.AI.Projects namespace only defines the following interfaces:
// - Connections, Evaluations, Deployments, Datasets, RedTeams, Indexes
//
// Therefore, most of the APIView feedback items CANNOT be addressed in this file.
// They would need to be addressed in Azure.AI.Agents/client.tsp (which is outside 
// the scope of this issue per the requirements).
//
// For a comprehensive analysis of which feedback items can/cannot be addressed,
// see the PR description summary table.

// ============================================================================
// Addressable items from APIView feedback (Azure.AI.Projects types only)
// ============================================================================

// NOTE: After thorough analysis, there are NO feedback items that can be addressed
// via TypeSpec client customizations in Azure.AI.Projects/client.tsp because:
//
// 1. Most feedback references Azure.AI.Agents types (outside scope per requirements)
// 2. The few feedback items that reference Azure.AI.Projects types (like InputData.type)
//    cannot be changed via client.tsp customizations because:
//    - Discriminator properties must be named "type" (TypeSpec requirement)
//    - Property Optional qualifiers require changes to main TypeSpec files (not client.tsp)
//    - Duplicate mapping overloads are emitter-generated (cannot be controlled via client.tsp)
//    - Literal type parameters require changes to main TypeSpec files (not client.tsp)
//
// All addressable feedback items would require either:
// - Modifications to Azure.AI.Agents/client.tsp (explicitly forbidden by issue requirements)
// - Changes to main TypeSpec model/operation definitions (beyond client.tsp scope)
// - Code customizations in Python SDK (beyond TypeSpec scope)
