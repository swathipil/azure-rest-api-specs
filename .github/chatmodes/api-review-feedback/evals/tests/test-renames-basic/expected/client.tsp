import "./main.tsp";
import "@azure-tools/typespec-client-generator-core";

using Azure.ClientGenerator.Core;
using Language.QuestionAnswering;

namespace ClientCustomizations;

@@clientName(AnswersOptions.confidenceScoreThreshold, "confidenceThreshold", "python");
@@clientName(ShortAnswerOptions.confidenceScoreThreshold, "confidenceThreshold", "python");
