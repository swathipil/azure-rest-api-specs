# Azure Cosmos DB NoSQL API

This directory contains the TypeSpec specification for the Azure Cosmos DB NoSQL API.

## About

The Azure Cosmos DB NoSQL API allows you to work with documents and collections using a flexible schema.

## TypeSpec Structure

- `main.tsp` - Main service definition including models and operations
- `client.tsp` - Client customizations for SDK generation
- `tspconfig.yaml` - TypeSpec compiler configuration
- `examples/` - Example files for the API

## Models

### CosmosDict

`CosmosDict` is a dictionary type representing Cosmos DB document properties. It is a type alias for `Record<string>` and is exported in generated SDKs.

## Client Customizations

The `client.tsp` file contains customizations to ensure proper SDK generation:

- **CosmosDict Export**: Marked with `@@access(CosmosDict, Access.public)` to ensure it's exported in the root `__init__.py` of generated SDKs
- **Usage Markers**: Marked with `@@usage(CosmosDict, Usage.input | Usage.output)` to indicate it's used in both requests and responses

## Generating SDKs

To compile the TypeSpec and generate OpenAPI specs:

```bash
npx tsp compile specification/cosmos-db/data-plane/NoSQL
```

## APIView Feedback

This specification addresses APIView feedback to ensure `CosmosDict` is properly listed in the root `__init__.py` of the Python SDK.

For more information on TypeSpec client customizations, see:
https://github.com/Azure/azure-rest-api-specs/blob/main/eng/common/knowledge/customizing-client-tsp.md
