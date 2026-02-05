import "@azure-tools/typespec-client-generator-core";
import "./main.tsp";
import "../Azure.AI.Agents/main.tsp";
import "../OpenAI.Assistants/main.tsp";

using Azure.ClientGenerator.Core;
using Azure.AI.Agents;
using Azure.AI.OpenAI.Assistants;

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

// ========================================================================
// Python-specific customizations to address APIView feedback
// ========================================================================

// Rename 'object' property in AgentDeletionStatus to avoid built-in conflict (LineNo 3160)
@@clientName(Azure.AI.Agents.AgentDeletionStatus.object, "deleted", "python");

// Rename 'type' properties in models to 'type_' to avoid shadowing built-in (Python convention)
// SasCredential model (LineNo 2287 - BlobReferenceSasCredential)
@@clientName(Azure.AI.Projects.SasCredential.type, "type_", "python");

// FileDatasetVersion (LineNo 3964)
@@clientName(Azure.AI.Projects.FileDatasetVersion.type, "type_", "python");

// FolderDatasetVersion
@@clientName(Azure.AI.Projects.FolderDatasetVersion.type, "type_", "python");

// DatasetVersion (base model)
@@clientName(Azure.AI.Projects.DatasetVersion.type, "type_", "python");

// Index models (LineNo 1956 - AzureAISearchIndex)
@@clientName(Azure.AI.Projects.Index.type, "type_", "python");
@@clientName(Azure.AI.Projects.AzureAISearchIndex.type, "type_", "python");
@@clientName(Azure.AI.Projects.ManagedAzureAISearchIndex.type, "type_", "python");
@@clientName(Azure.AI.Projects.CosmosDBIndex.type, "type_", "python");

// Connection models (LineNo 2737)
@@clientName(Azure.AI.Projects.Connection.type, "type_", "python");
@@clientName(Azure.AI.Projects.BaseCredentials.type, "type_", "python");
@@clientName(Azure.AI.Projects.ApiKeyCredentials.type, "type_", "python");
@@clientName(Azure.AI.Projects.EntraIDCredentials.type, "type_", "python");
@@clientName(Azure.AI.Projects.CustomCredential.type, "type_", "python");
@@clientName(Azure.AI.Projects.SASCredentials.type, "type_", "python");
@@clientName(Azure.AI.Projects.NoAuthenticationCredentials.type, "type_", "python");

// Deployment models (LineNo 7184 - ModelDeployment)
@@clientName(Azure.AI.Projects.Deployment.type, "type_", "python");
@@clientName(Azure.AI.Projects.ModelDeployment.type, "type_", "python");

// Evaluation models
@@clientName(Azure.AI.Projects.InputData.type, "type_", "python");
@@clientName(Azure.AI.Projects.InputDataset.type, "type_", "python");
@@clientName(Azure.AI.Projects.EvaluationTarget.type, "type_", "python");

// Red-team models
@@clientName(Azure.AI.Projects.TargetConfig.type, "type_", "python");

// Azure.AI.Agents Tool definitions - rename 'type' discriminator property
@@clientName(Azure.AI.Agents.ToolDefinition.type, "type_", "python");
@@clientName(Azure.AI.Agents.CodeInterpreterToolDefinition.type, "type_", "python");
@@clientName(Azure.AI.Agents.FileSearchToolDefinition.type, "type_", "python");
@@clientName(Azure.AI.Agents.FunctionToolDefinition.type, "type_", "python");
@@clientName(Azure.AI.Agents.BingGroundingToolDefinition.type, "type_", "python");
@@clientName(Azure.AI.Agents.MicrosoftFabricToolDefinition.type, "type_", "python");
@@clientName(Azure.AI.Agents.SharepointToolDefinition.type, "type_", "python");
@@clientName(Azure.AI.Agents.AzureAISearchToolDefinition.type, "type_", "python");
@@clientName(Azure.AI.Agents.OpenApiToolDefinition.type, "type_", "python");
@@clientName(Azure.AI.Agents.BingCustomSearchToolDefinition.type, "type_", "python");
@@clientName(Azure.AI.Agents.ConnectedAgentToolDefinition.type, "type_", "python");
@@clientName(Azure.AI.Agents.DeepResearchToolDefinition.type, "type_", "python");
@@clientName(Azure.AI.Agents.MCPToolDefinition.type, "type_", "python");
@@clientName(Azure.AI.Agents.ComputerUseToolDefinition.type, "type_", "python");
@@clientName(Azure.AI.Agents.AzureFunctionToolDefinition.type, "type_", "python");
@@clientName(Azure.AI.Agents.BrowserAutomationToolDefinition.type, "type_", "python");

// ========================================================================
// APIView Feedback Summary
// ========================================================================
// This file addresses APIView feedback for azure-ai-projects (Python) package
// APIView URL: https://spa.apiview.dev/review/a8bd55fd470240e29e7648d13a7882eb
//
// ADDRESSED via TypeSpec customizations (renamed 'type' to 'type_', 'object' to 'deleted'):
// - All discriminator properties named 'type' in Azure.AI.Projects models (14 models)
// - All discriminator properties named 'type' in Azure.AI.Agents ToolDefinition models (18 models)
// - AgentDeletionStatus.object property renamed to 'deleted'
//
// CANNOT BE ADDRESSED from TypeSpec (Python SDK generation or hand-written code):
// - Duplicate mapping overloads (LineNo 1960, 2316, 8186)
// - Optional type annotations (LineNo 3939, 4052, 4054, 4058) 
// - Operations that don't exist in TypeSpec (EvaluatorsOperations, InsightsOperations, SchedulesOperations)
// - Python telemetry/instrumentation code (LineNo 10120, 10125)
// - LRO metadata properties (LineNo 1840, 1841, 1852, 8591)
// - Many parameter type changes to Literal types (require model definition changes)
// - Some model naming issues for generated types (GrammarSyntax1, etc.)
// - Most feedback items are about Python SDK code generation patterns that are not controlled
//   by TypeSpec but by the Python emitter or hand-written SDK code
