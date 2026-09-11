# Edge case: a plan mixing modeled and unmodeled resources

Real plans rarely contain only the handful of resource types
`infra-contract` currently models (`aws_db_instance`, `aws_s3_bucket`,
`aws_security_group`, `aws_iam_policy`, `aws_ecs_service`,
`aws_lambda_function`, `aws_instance`, `aws_elasticache_*`, ...). A typical
plan also touches things like `aws_cloudfront_distribution`,
`aws_sqs_queue`, or `aws_route53_record`, none of which have a policy
opinion today.

This example is a reminder of what happens at that boundary, per the
[Scope](../../README.md#scope) section: **an unmodeled resource type
produces no finding at all — not a pass, not a failure.** Given a plan with
one wildcard IAM policy and two unmodeled resources:

```bash
infra-contract check --plan tfplan.json --contract examples/unknown-resource-types/infra-contract.yaml
```

the result reports exactly one violation (`security.no-wildcard-iam`) for
the IAM policy. The CDN distribution and SQS queue are silently omitted
from the report — `infra-contract` never fabricates an opinion about a
resource type it doesn't understand.

Why this matters in practice:

- A clean `infra-contract check` result means "nothing modeled violated the
  contract," **not** "this infrastructure is safe." Unmodeled resource
  types are outside the tool's opinion entirely.
- This is intentional: guessing at unfamiliar attributes would risk both
  false failures (blocking a safe change) and false passes (waving through
  an unsafe one). Staying silent is the conservative choice.
- Pair `infra-contract` with cloud-native controls (SCPs, Config rules,
  IAM boundaries) and code review for resource types it doesn't cover, and
  treat new resource types in a plan as a signal to check whether policy
  coverage needs to grow.
