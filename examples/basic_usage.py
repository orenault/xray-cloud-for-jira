from xray_cloud_for_jira import XrayCloudClient


def main() -> None:
    client = XrayCloudClient(debug=True)
    print(client.get_test("HHELIA-6"))


if __name__ == "__main__":
    main()
