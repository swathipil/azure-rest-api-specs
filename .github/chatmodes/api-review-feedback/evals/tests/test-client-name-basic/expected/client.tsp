import "./models.tsp";
import "@azure-tools/typespec-client-generator-core";

using Azure.ClientGenerator.Core;
using TypeSpec.Versioning;
using Language.QuestionAnswering;    // OPTIONAL

@useDependency(Versions.v2025_05_15_preview)    // OPTIONAL
namespace ClientCustomizations;

@@clientName(AnswersOptions.confidenceScoreThreshold, "confidenceThreshold", "python");
@@clientName(ShortAnswerOptions.confidenceScoreThreshold, "confidenceThreshold", "python");
