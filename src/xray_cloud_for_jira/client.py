from __future__ import annotations

import os
from typing import Any, Dict, Iterable, List, Optional

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class XrayCloudClient:
    """Standalone Xray Cloud client for Jira-backed Xray projects."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        base_url: str = "https://xray.cloud.getxray.app",
        verify_ssl: bool = False,
        timeout: int = 30,
        debug: bool = False,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id or os.getenv("XRAY_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("XRAY_CLIENT_SECRET")
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.debug = debug

        if not self.client_id or not self.client_secret:
            raise ValueError(
                "You must provide client_id and client_secret, or set "
                "XRAY_CLIENT_ID / XRAY_CLIENT_SECRET."
            )

        self.token = self._authenticate()

    def _log(self, *parts: Any) -> None:
        if self.debug:
            print(*parts)

    def _authenticate(self) -> str:
        url = f"{self.base_url}/api/v2/authenticate"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        response = requests.post(
            url,
            json=payload,
            timeout=self.timeout,
            verify=self.verify_ssl,
        )
        response.raise_for_status()
        token = response.json()
        if isinstance(token, str):
            return token
        if isinstance(token, dict) and "token" in token:
            return str(token["token"])
        raise RuntimeError("Unable to retrieve Xray Cloud token")

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def graphql(self, query: Any, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if isinstance(query, list):
            query = "\n".join(str(x) for x in query)

        if isinstance(variables, dict):
            variables = {
                key: (int(value) if key in ("limit", "start") and str(value).isdigit() else value)
                for key, value in variables.items()
            }

        url = f"{self.base_url}/api/v2/graphql"
        payload = {"query": query, "variables": variables or {}}

        self._log("XRAY GRAPHQL URL =", url)
        self._log("XRAY GRAPHQL QUERY =", query)
        self._log("XRAY GRAPHQL VARIABLES =", variables)

        response = requests.post(
            url,
            headers=self.headers,
            json=payload,
            timeout=self.timeout,
            verify=self.verify_ssl,
        )

        self._log("XRAY GRAPHQL STATUS =", response.status_code)
        self._log("XRAY GRAPHQL RESPONSE =", response.text)

        response.raise_for_status()
        return response.json()

    def post(
        self,
        path: str,
        *,
        data: Any = None,
        json_data: Any = None,
        files: Any = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        effective_headers = (
            headers if headers is not None
            else self.headers if files is None
            else {"Authorization": f"Bearer {self.token}"}
        )

        response = requests.post(
            url,
            headers=effective_headers,
            data=data,
            json=json_data,
            files=files,
            params=params,
            timeout=self.timeout,
            verify=self.verify_ssl,
        )
        response.raise_for_status()
        if response.text:
            try:
                return response.json()
            except Exception:
                return response.text
        return {}

    def _extract(self, result: Dict[str, Any], path: Optional[List[str]] = None) -> Any:
        if not isinstance(result, dict):
            return result
        if "errors" in result and result["errors"]:
            raise AssertionError(f"Xray GraphQL error: {result['errors']}")
        data = result.get("data")
        if path is None:
            return data
        current: Any = data
        for key in path:
            if current is None:
                return None
            if not isinstance(current, dict):
                return current
            current = current.get(key)
        return current

    @staticmethod
    def _is_numeric_id(value: Any) -> bool:
        return str(value).isdigit()

    def _resolve_xray_issue_id(self, entity_name: str, ticket_ref: Any) -> str:
        ticket_ref = str(ticket_ref)

        single_queries = {
            "testPlan": """
                query($issueId: String!) {
                  getTestPlan(issueId: $issueId) {
                    issueId
                    jira(fields:["key"])
                  }
                }
            """,
            "test": """
                query($issueId: String!) {
                  getTest(issueId: $issueId) {
                    issueId
                    jira(fields:["key"])
                  }
                }
            """,
            "testExecution": """
                query($issueId: String!) {
                  getTestExecution(issueId: $issueId) {
                    issueId
                    jira(fields:["key"])
                  }
                }
            """,
        }

        single_paths = {
            "testPlan": ["getTestPlan"],
            "test": ["getTest"],
            "testExecution": ["getTestExecution"],
        }

        search_queries = {
            "testPlan": """
                query($jql: String!, $limit: Int!) {
                  getTestPlans(jql: $jql, limit: $limit) {
                    total
                    results {
                      issueId
                      jira(fields:["key","summary"])
                    }
                  }
                }
            """,
            "test": """
                query($jql: String!, $limit: Int!) {
                  getTests(jql: $jql, limit: $limit) {
                    total
                    results {
                      issueId
                      jira(fields:["key","summary"])
                    }
                  }
                }
            """,
            "testExecution": """
                query($jql: String!, $limit: Int!) {
                  getTestExecutions(jql: $jql, limit: $limit) {
                    total
                    results {
                      issueId
                      jira(fields:["key","summary"])
                    }
                  }
                }
            """,
        }

        search_paths = {
            "testPlan": ["getTestPlans"],
            "test": ["getTests"],
            "testExecution": ["getTestExecutions"],
        }

        if self._is_numeric_id(ticket_ref):
            result = self.graphql(single_queries[entity_name], {"issueId": ticket_ref})
            found = self._extract(result, single_paths[entity_name])
            if found and found.get("issueId"):
                return str(found["issueId"])

        result = self.graphql(
            search_queries[entity_name],
            {"jql": f'key = "{ticket_ref}"', "limit": 2},
        )
        found = self._extract(result, search_paths[entity_name])

        if not found or not found.get("results"):
            raise AssertionError(
                f"Unable to resolve Xray {entity_name} from ticket reference '{ticket_ref}'"
            )

        return str(found["results"][0]["issueId"])

    def _resolve_xray_issue_ids(self, entity_name: str, ticket_refs: Iterable[Any]) -> List[str]:
        return [self._resolve_xray_issue_id(entity_name, ref) for ref in ticket_refs]

    def get_test_id(self, ticket_ref: Any) -> str:
        return self._resolve_xray_issue_id("test", ticket_ref)

    def get_test_plan_id(self, ticket_ref: Any) -> str:
        return self._resolve_xray_issue_id("testPlan", ticket_ref)

    def get_test_execution_id(self, ticket_ref: Any) -> str:
        return self._resolve_xray_issue_id("testExecution", ticket_ref)

    def get_tests_by_jql(self, jql: str, limit: int = 10) -> Any:
        query = """
        query($jql: String!, $limit: Int!) {
          getTests(jql: $jql, limit: $limit) {
            total
            results {
              issueId
              jira(fields:["key","summary"])
            }
          }
        }
        """
        result = self.graphql(query, {"jql": jql, "limit": limit})
        return self._extract(result, ["getTests"])

    def get_test_plans_by_jql(self, jql: str, limit: int = 10) -> Any:
        query = """
        query($jql: String!, $limit: Int!) {
          getTestPlans(jql: $jql, limit: $limit) {
            total
            results {
              issueId
              jira(fields:["key","summary"])
            }
          }
        }
        """
        result = self.graphql(query, {"jql": jql, "limit": limit})
        return self._extract(result, ["getTestPlans"])

    def get_test_executions_by_jql(self, jql: str, limit: int = 10) -> Any:
        query = """
        query($jql: String!, $limit: Int!) {
          getTestExecutions(jql: $jql, limit: $limit) {
            total
            results {
              issueId
              jira(fields:["key","summary"])
            }
          }
        }
        """
        result = self.graphql(query, {"jql": jql, "limit": limit})
        return self._extract(result, ["getTestExecutions"])

    def get_test(self, ticket_ref: Any) -> Any:
        xray_id = self.get_test_id(ticket_ref)
        query = """
        query($issueId: String!) {
          getTest(issueId: $issueId) {
            issueId
            jira(fields:["key","summary"])
          }
        }
        """
        result = self.graphql(query, {"issueId": xray_id})
        return self._extract(result, ["getTest"])

    def get_tests_with_test_plan(self, ticket_ref: Any) -> Any:
        xray_id = self.get_test_plan_id(ticket_ref)
        query = """
        query($issueId: String!) {
          getTestPlan(issueId: $issueId) {
            tests(limit: 100) {
              total
              results {
                issueId
                jira(fields:["key","summary"])
              }
            }
          }
        }
        """
        result = self.graphql(query, {"issueId": xray_id})
        return self._extract(result, ["getTestPlan", "tests"])

    def get_tests_with_test_execution(self, ticket_ref: Any) -> Any:
        xray_id = self.get_test_execution_id(ticket_ref)
        query = """
        query($issueId: String!) {
          getTestExecution(issueId: $issueId) {
            tests(limit: 100) {
              total
              results {
                issueId
                jira(fields:["key","summary"])
              }
            }
          }
        }
        """
        result = self.graphql(query, {"issueId": xray_id})
        return self._extract(result, ["getTestExecution", "tests"])

    def get_test_runs(self, ticket_ref: Any) -> Any:
        xray_id = self.get_test_id(ticket_ref)
        query = """
        query($issueId: String!) {
          getTest(issueId:$issueId) {
            testRuns(limit:100) {
              total
              results {
                id
                status { name }
              }
            }
          }
        }
        """
        result = self.graphql(query, {"issueId": xray_id})
        return self._extract(result, ["getTest", "testRuns"])

    def create_test_execution(self, project_key: str, summary: str) -> Any:
        query = """
        mutation($projectKey:String!, $summary:String!) {
          createTestExecution(
            testExecution:{
              jira:{
                fields:{
                  project:{key:$projectKey}
                  summary:$summary
                }
              }
            }
          ) {
            testExecution {
              issueId
              jira(fields:["key"])
            }
          }
        }
        """
        result = self.graphql(query, {"projectKey": project_key, "summary": summary})
        return self._extract(result, ["createTestExecution", "testExecution"])

    def add_tests_to_test_plan(self, plan_ref: Any, test_refs: Iterable[Any]) -> Any:
        plan_id = self.get_test_plan_id(plan_ref)
        test_ids = self._resolve_xray_issue_ids("test", test_refs)

        query = """
        mutation($issueId:String!, $tests:[String!]!) {
          addTestsToTestPlan(issueId:$issueId, testIssueIds:$tests) {
            addedTests
            warning
          }
        }
        """
        result = self.graphql(query, {"issueId": plan_id, "tests": test_ids})
        return self._extract(result, ["addTestsToTestPlan"])

    def update_test_run_status(self, run_id: Any, status: str) -> Any:
        query = """
        mutation($runId:String!, $status:String!) {
          updateTestRunStatus(id:$runId, status:$status) {
            id
            status { name }
          }
        }
        """
        result = self.graphql(query, {"runId": str(run_id), "status": status})
        return self._extract(result, ["updateTestRunStatus"])

    def _import_execution_results(
        self,
        *,
        file_path: str,
        endpoint: str,
        content_type: str,
        error_label: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        if not file_path or not os.path.isfile(file_path):
            raise FileNotFoundError(f"{error_label} file not found: {file_path}")

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": content_type,
            "Accept": "application/json",
        }

        with open(file_path, "rb") as f:
            payload = f.read()

        response = requests.post(
            url,
            headers=headers,
            params=params or None,
            data=payload,
            timeout=self.timeout,
            verify=self.verify_ssl,
        )

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError(
                f"Xray {error_label} import failed [{response.status_code}] {url} -> {response.text}"
            ) from e

        if not response.text:
            return {}

        try:
            return response.json()
        except Exception:
            return response.text

    def import_robot_results(self, file_path: str, project_key: Optional[str] = None) -> Any:
        params: Dict[str, Any] = {}
        if project_key:
            params["projectKey"] = project_key

        return self._import_execution_results(
            file_path=file_path,
            endpoint="/api/v2/import/execution/robot",
            content_type="text/xml",
            error_label="Robot",
            params=params,
        )

    def import_junit_results(self, file_path: str) -> Any:
        return self._import_execution_results(
            file_path=file_path,
            endpoint="/api/v2/import/execution/junit",
            content_type="text/xml",
            error_label="JUnit",
        )

    def import_cucumber_results(self, file_path: str) -> Any:
        return self._import_execution_results(
            file_path=file_path,
            endpoint="/api/v2/import/execution/cucumber",
            content_type="application/json",
            error_label="Cucumber",
        )

    def add_evidence_to_test_run(self, run_id: Any, file_path: str) -> Any:
        with open(file_path, "rb") as fh:
            return self.post(f"/api/v2/testruns/{run_id}/evidences", files={"file": fh})
