import "@azure-tools/typespec-client-generator-core";
import "./main.tsp";
import "../Azure.AI.Agents/main.tsp";

using Azure.ClientGenerator.Core;
using Azure.AI.Agents;

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

// ================================================================================
// Python-specific customizations to address APIView feedback for azure-ai-projects
// APIView URL: https://spa.apiview.dev/review/a8bd55fd470240e29e7648d13a7882eb
// ================================================================================

// ---------------------------------------------------------------------------------
// Python Built-in Shadowing - Rename 'type' discriminators (Lines 760, 1470, 1956, etc.)
// ---------------------------------------------------------------------------------

// Azure.AI.Projects namespace models
@@clientName(Azure.AI.Projects.SasCredential.type, "type_", "python");
@@clientName(Azure.AI.Projects.AzureAISearchIndex.type, "index_type", "python");
@@clientName(Azure.AI.Projects.CosmosDBIndex.type, "index_type", "python");
@@clientName(Azure.AI.Projects.ManagedAzureAISearchIndex.type, "index_type", "python");
@@clientName(Azure.AI.Projects.FileDatasetVersion.type, "data_type", "python");
@@clientName(Azure.AI.Projects.FolderDatasetVersion.type, "data_type", "python");

// Azure.AI.Agents namespace models - Line 3160: Rename 'object' to 'status'
@@clientName(Azure.AI.Agents.AgentDeletionStatus.object, "status", "python");

// Line 4434: Rename FunctionToolDefinition.type field to avoid shadowing built-in
@@clientName(Azure.AI.Agents.FunctionToolDefinition.type, "type_", "python");

// Additional Tool definitions with 'type' discriminators that shadow Python built-ins
@@clientName(Azure.AI.Agents.CodeInterpreterToolDefinition.type, "type_", "python");
@@clientName(Azure.AI.Agents.FileSearchToolDefinition.type, "type_", "python");
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

// Connection credential models with 'type' discriminators
@@clientName(Azure.AI.Projects.BaseCredentials.type, "credential_type", "python");
@@clientName(Azure.AI.Projects.ApiKeyCredentials.type, "credential_type", "python");
@@clientName(Azure.AI.Projects.EntraIDCredentials.type, "credential_type", "python");
@@clientName(Azure.AI.Projects.CustomCredential.type, "credential_type", "python");
@@clientName(Azure.AI.Projects.SASCredentials.type, "credential_type", "python");
@@clientName(Azure.AI.Projects.NoAuthenticationCredentials.type, "credential_type", "python");

// Connection model has 'type' field for ConnectionType
@@clientName(Azure.AI.Projects.Connection.type, "connection_type", "python");

// Message models with 'type' discriminators
@@clientName(Azure.AI.Agents.MessageInputTextBlock.type, "type_", "python");
@@clientName(Azure.AI.Agents.MessageInputImageFileBlock.type, "type_", "python");
@@clientName(Azure.AI.Agents.MessageInputImageUrlBlock.type, "type_", "python");
@@clientName(Azure.AI.Agents.MessageTextContent.type, "type_", "python");
@@clientName(Azure.AI.Agents.MessageImageFileContent.type, "type_", "python");

// Run step models with 'type' discriminators
@@clientName(Azure.AI.Agents.RunStepDeltaMessageCreation.type, "type_", "python");
@@clientName(Azure.AI.Agents.RunStepDeltaToolCallObject.type, "type_", "python");
@@clientName(Azure.AI.Agents.RunStepDeltaMCPObject.type, "type_", "python");
@@clientName(Azure.AI.Agents.RunStepDeltaOpenAPIObject.type, "type_", "python");

// ---------------------------------------------------------------------------------
// Make Internal Classes (Lines 1852, 8591, 10120)
// ---------------------------------------------------------------------------------

// Note: LRO polling method classes are typically auto-generated
// Line 1852, 8591: AsyncUpdateMemoriesLROPollingMethod and UpdateMemoriesLROPollingMethod
// should be internal - these may need to be addressed at SDK generation level

// Line 10120: trace_function - mark as internal if it exists
// This may need to be addressed at the SDK generation level

// ---------------------------------------------------------------------------------
// Optional Fields (Lines 3939, 4052, 4054, 4058)
// ---------------------------------------------------------------------------------

// The TypeSpec definitions already use optional (?:) syntax for these fields
// via the AssetBase alias, so they should already be optional in the generated SDK

// ---------------------------------------------------------------------------------
// Parameter Renames for Operations (Lines 9784, 10087)
// ---------------------------------------------------------------------------------

// Note: Operation parameter renames may need to be done through operation-level decorators
// if such operations exist in the TypeSpec

// ---------------------------------------------------------------------------------
// Model Naming Improvements (Lines 8360, 8380, 8406)
// ---------------------------------------------------------------------------------

// These would require model-level renames which may have broader impact
// Deferring to spec owners for approval

// ---------------------------------------------------------------------------------
// Additional Comments from Feedback
// ---------------------------------------------------------------------------------

// Line 2316: Duplicate mapping overload - needs investigation in generated code
// Line 756: list_latest_versions should perhaps be named just "list"
// Line 4460: GrammarSyntax1 suffix - needs investigation
// Line 8259: Summary.type discriminator - needs investigation
// Line 7799: RankerVersionType.DEFAULT2024_11_15 capitalization
// Line 2737: Connection.credentials Optional based on include_credentials
// Line 6369: ItemResourceMcpApprovalResponseResource - long name
// Line 6572: keys_property conflict - needs property rename
