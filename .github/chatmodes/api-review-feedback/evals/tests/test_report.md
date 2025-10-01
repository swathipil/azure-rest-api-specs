
# TypeSpec Chatmode Evaluation Report

## Summary
- **Total Tests**: 1
- **Passed**: 0 ✅
- **Failed**: 1 ❌
- **Success Rate**: 0.0%

## Test Results

### ivar_renaming_python - ❌ FAILED
**Message**: Output mismatch: Missing in generated: root['other'][0] = {"detected_language": "python", "confidence": 0.95}
Extra in generated: root['imports'][0] = import "./main.tsp"
Extra in generated: root['imports'][1] = import "@azure-tools/typespec-client-generator-core"
Extra in generated: root['using_statements'][0] = using Azure.ClientGenerator.Core
Extra in generated: root['using_statements'][1] = using Language.QuestionAnswering
Extra in generated: root['decorators'][0] = @@clientName(AnswersOptions.confidenceScoreThreshold, "confidenceThreshold", "python")
Extra in generated: root['decorators'][1] = @@clientName(ShortAnswerOptions.confidenceScoreThreshold, "confidenceThreshold", "python" ); Compilation failed; Missing decorators: @@clientName(AnswersOptions.confidenceScoreThreshold, "confidenceThreshold", "python"), @@clientName(ShortAnswerOptions.confidenceScoreThreshold, "confidenceThreshold", "python")

**Diff**:
```diff
--- expected/client.tsp+++ results/client.tsp@@ -1,12 +1 @@-import "./main.tsp";
-import "@azure-tools/typespec-client-generator-core";
-
-using Azure.ClientGenerator.Core;
-using Language.QuestionAnswering;
-
-namespace ClientCustomizations;
-
-@@clientName(AnswersOptions.confidenceScoreThreshold, "confidenceThreshold", "python");
-@@clientName(ShortAnswerOptions.confidenceScoreThreshold,
-  "confidenceThreshold", "python"
-);+{"detected_language": "python", "confidence": 0.95}
```

**Compilation Result**:
```
STDOUT:
TypeSpec compiler v0.65.3

tspconfig.yaml:2:3 - error invalid-schema: Schema violation: must be object (/options/emit)
> 2 |   emit:
    |   ^^^^

Found 1 error.


STDERR:

```
