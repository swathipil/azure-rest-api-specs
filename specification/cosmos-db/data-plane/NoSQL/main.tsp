import "@typespec/http";
import "@typespec/rest";
import "@typespec/versioning";
import "@azure-tools/typespec-azure-core";

using TypeSpec.Http;
using TypeSpec.Rest;
using TypeSpec.Versioning;
using Azure.Core;

@service(#{
  title: "Azure Cosmos DB NoSQL API",
})
@versioned(Versions)
@server(
  "{endpoint}",
  "Azure Cosmos DB NoSQL API endpoint",
  {
    @doc("Cosmos DB account endpoint URL")
    endpoint: url,
  }
)
@useAuth(ApiKeyAuth<ApiKeyLocation.header, "Authorization">)
namespace Azure.Cosmos;

@doc("Service API versions")
enum Versions {
  @doc("API version 2024-05-15")
  v2024_05_15: "2024-05-15",
}

@doc("A dictionary type representing Cosmos DB document properties")
model CosmosDict is Record<string>;

@doc("Represents a Cosmos DB document")
model Document {
  @doc("Document id")
  id: string;

  @doc("Document properties")
  properties?: CosmosDict;
}

@doc("Error response")
model ErrorResponse {
  @doc("Error details")
  error: ErrorDetail;
}

@doc("Error detail")
model ErrorDetail {
  @doc("Error code")
  code: string;

  @doc("Error message")
  message: string;
}
