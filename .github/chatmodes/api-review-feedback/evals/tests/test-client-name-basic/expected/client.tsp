import "./models.tsp";
import "@azure-tools/typespec-client-generator-core";

using Azure.ClientGenerator.Core;
using TypeSpec.Versioning;    // OPTIONAL

@useDependency(Versions.v2025_05_15_preview)    // OPTIONAL
namespace ClientCustomizations;

@@clientName(Language.QuestionAnswering.AnswersOptions.confidenceScoreThreshold, "confidenceThreshold", "python");
@@clientName(Language.QuestionAnswering.ShortAnswerOptions.confidenceScoreThreshold, "confidenceThreshold", "python");
