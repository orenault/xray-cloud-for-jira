# xray-cloud-for-jira

Python client for Xray Cloud (GraphQL + REST) with automatic Jira issueId resolution.

## Why this package exists

Xray Cloud is not just a classic Jira REST client problem:

- Xray Cloud uses its own authentication model
- GraphQL is the primary API for many operations
- Jira keys and Xray issue IDs are not the same thing
- imports and evidences use separate REST endpoints

This package isolates that complexity in a single reusable Python client.

## Main features

- OAuth2 authentication for Xray Cloud using `client_id` / `client_secret`
- GraphQL helper with optional list-to-query conversion
- automatic Jira key → Xray issue ID resolution
- support for:
  - test retrieval
  - test plan retrieval
  - test execution retrieval
  - test run listing
  - test execution creation
  - adding tests to a test plan
  - test run status updates
  - Robot / JUnit / Cucumber imports
  - evidence upload

## Installation

```bash
pip install xray-cloud-for-jira
```

or with uv:

```bash
uv add xray-cloud-for-jira
```

## Package structure

```text
xray-cloud-for-jira/
├── src/xray_cloud_for_jira/
│   ├── __init__.py
│   └── client.py
├── examples/
├── pyproject.toml
├── README.md
├── LICENSE
└── .gitignore
```

## Quick start

### 1. Environment variables

```bash
export XRAY_CLIENT_ID="your-client-id"
export XRAY_CLIENT_SECRET="your-client-secret"
```

### 2. Python example

```python
from xray_cloud_for_jira import XrayCloudClient

client = XrayCloudClient(debug=True)

test = client.get_test("HHELIA-6")
print(test)

tests = client.get_tests_with_test_plan("HHELIA-10")
print(tests)
```

## Explicit connection

```python
from xray_cloud_for_jira import XrayCloudClient

client = XrayCloudClient(
    client_id="your-client-id",
    client_secret="your-client-secret",
    verify_ssl=False,
    timeout=30,
    debug=False,
)
```

## GraphQL examples

### Simple string query

```python
query = '''
query($issueId: String!) {
  getTest(issueId: $issueId) {
    issueId
    jira(fields:["key","summary"])
  }
}
'''

result = client.graphql(query, {"issueId": "66925"})
print(result)
```

### Multi-line list query

```python
query = [
    "query($issueId: String!) {",
    "  getTest(issueId: $issueId) {",
    '    jira(fields:["key","summary"])',
    "  }",
    "}",
]

result = client.graphql(query, {"issueId": "66925"})
```

## Automatic Jira → Xray mapping

One of the most important features of this package is the automatic resolution from a Jira key such as:

```text
HHELIA-6
```

to the Xray internal issue ID required by GraphQL operations.

This lets you work with natural Jira references in your code instead of manually resolving IDs everywhere.

## Supported methods

### Lookup and search

- `get_test_id(ticket_ref)`
- `get_test_plan_id(ticket_ref)`
- `get_test_execution_id(ticket_ref)`
- `get_tests_by_jql(jql, limit=10)`
- `get_test_plans_by_jql(jql, limit=10)`
- `get_test_executions_by_jql(jql, limit=10)`

### Entity retrieval

- `get_test(ticket_ref)`
- `get_tests_with_test_plan(ticket_ref)`
- `get_tests_with_test_execution(ticket_ref)`
- `get_test_runs(ticket_ref)`

### Write operations

- `create_test_execution(project_key, summary)`
- `add_tests_to_test_plan(plan_ref, test_refs)`
- `update_test_run_status(run_id, status)`

### Imports

- `import_robot_results(file_path, project_key=None)`
- `import_junit_results(file_path)`
- `import_cucumber_results(file_path)`

### Evidences

- `add_evidence_to_test_run(run_id, file_path)`

## Example: create execution

```python
execution = client.create_test_execution(
    project_key="HHELIA",
    summary="Execution created from xray-cloud-for-jira",
)
print(execution)
```

## Example: add tests to a test plan

```python
result = client.add_tests_to_test_plan(
    "HHELIA-10",
    ["HHELIA-6", "HHELIA-7"],
)
print(result)
```

## Example: import Robot results

```python
result = client.import_robot_results(
    "output.xml",
    project_key="HHELIA",
)
print(result)
```

## Example: add evidence

```python
result = client.add_evidence_to_test_run(
    run_id="123456",
    file_path="screenshot.png",
)
print(result)
```

## Error handling philosophy

The client keeps things intentionally simple:

- authentication errors raise HTTP errors
- GraphQL errors are surfaced as assertion failures with the raw `errors` payload
- file imports raise `FileNotFoundError` if the local file is missing
- failing imports raise a `RuntimeError` with the response payload

## SSL note

For local validation or lab environments, `verify_ssl=False` can be useful.

For production usage, enable certificate verification whenever possible.

## Typical use cases

- standalone Python automation
- CI/CD steps importing execution results
- Jira/Xray utility scripts
- higher-level wrappers such as Robot Framework libraries
- future packaging inside a broader QA / TestOps platform

## Development install

```bash
git clone https://github.com/orenault/xray-cloud-for-jira.git
cd xray-cloud-for-jira
pip install -e .
```

or with uv:

```bash
uv sync
```

## Build

```bash
uv build
```

## Publish to PyPI

```bash
uv publish
```

## License

MIT
