# xray-cloud-for-jira

Python client for Xray Cloud (GraphQL + REST) with automatic Jira issueId resolution.

## Features

- GraphQL + REST support
- OAuth2 authentication
- automatic Jira key → Xray ID resolution
- support for test, test plan, and execution operations
- import Robot / JUnit / Cucumber results

## Example

```python
from xray_cloud_for_jira import XrayCloudClient

client = XrayCloudClient()

test = client.get_test("DEMO-123")
print(test)
```

## License

MIT
