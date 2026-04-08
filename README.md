# xray-cloud-for-jira

## 🚀 Overview

Python client for Xray Cloud (GraphQL + REST) with automatic Jira issueId resolution.

---

## 🎯 Problem

Xray Cloud differs significantly from Jira APIs:

- GraphQL-first API model
- OAuth2 authentication (client_id / client_secret)
- Jira keys != Xray internal IDs
- mixed GraphQL + REST endpoints

This creates friction for automation and integration.

---

## 💡 Solution

This library provides:

- a unified client
- automatic Jira → Xray ID resolution
- GraphQL + REST abstraction
- reusable Python integration layer

---

## 🔥 Core Features

- GraphQL + REST support
- automatic ID mapping
- execution creation
- test management
- imports (Robot, JUnit, Cucumber)
- evidence upload
- debug mode

---

## ⚡ Installation

```bash
pip install xray-cloud-for-jira
```

---

## 🧪 Quick Start

```python
from xray_cloud_for_jira import XrayCloudClient

client = XrayCloudClient(debug=True)

print(client.get_test("DEMO-123"))
```

---

## 🧠 Key Mechanism: ID Resolution

```
DEMO-123 → Xray issueId (internal)
```

Automatic resolution avoids manual mapping.

---

## 📊 Typical Use Cases

- CI/CD pipelines
- test automation frameworks
- data extraction / reporting
- integration platforms

---

## 🧱 Architecture

```
Your Code
   ↓
XrayCloudClient
   ↓
GraphQL / REST APIs
   ↓
Xray Cloud
```

---

## 📥 Imports

```python
client.import_robot_results("output.xml", project_key="DEMO")
```

---

## 🧪 Advanced Example

```python
tests = client.get_tests_with_test_plan("DEMO-123")
for t in tests["results"]:
    print(t)
```

---

## 🔐 Security

- OAuth2 token handled internally
- optional SSL disable for test environments

---

## 📄 License

MIT
