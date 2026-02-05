import "@azure-tools/typespec-client-generator-core";
import "./main.tsp";

using Azure.ClientGenerator.Core;
using Azure.Cosmos;

@TypeSpec.Versioning.useDependency(Azure.Cosmos.Versions.v2024_05_15)
namespace ClientCustomizations;

// Ensure CosmosDict is accessible and exported in the Python SDK's __init__.py
// This addresses the APIView feedback that CosmosDict should be listed in the root __init__.py
@@access(CosmosDict, Access.public);

// Mark CosmosDict as both input and output to ensure it's exported
@@usage(CosmosDict, Usage.input | Usage.output);
