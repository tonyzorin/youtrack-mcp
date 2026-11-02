"""Regression coverage for the field shapes used by the live DEV project."""

import json
from unittest.mock import Mock

import pytest

from youtrack_mcp.api.issues import Issue, IssuesClient
from youtrack_mcp.tools.issues.dedicated_updates import DedicatedUpdates

pytestmark = pytest.mark.unit


def test_direct_state_update_sends_typed_field_and_checks_persisted_value():
    client = Mock()
    client.get.return_value = {"customFields": [{"name": "State", "value": {"name": "Done"}}]}
    issues = IssuesClient(client)

    assert issues._apply_direct_state_update("DEV-2312", "Done") is True
    client.post.assert_called_once_with(
        "issues/DEV-2312",
        data={"customFields": [{"name": "State", "$type": "StateIssueCustomField",
                                "value": {"name": "Done", "$type": "StateBundleElement"}}]},
    )


def test_direct_state_update_does_not_claim_success_when_state_stays_old():
    client = Mock()
    client.get.return_value = {"customFields": [{"name": "State", "value": {"name": "In Progress"}}]}

    assert IssuesClient(client)._apply_direct_state_update("DEV-2312", "Done") is False


def test_state_command_uses_readable_id_and_does_not_claim_unpersisted_success():
    issues = Mock()
    issues._apply_direct_state_update.return_value = False
    issues.client.post.return_value = {}
    issues.client.get.return_value = {"customFields": [{"name": "State", "value": {"name": "In Progress"}}]}

    result = json.loads(DedicatedUpdates(issues, Mock()).update_issue_state("DEV-2312", "Done"))

    issues.client.post.assert_called_once_with(
        "commands", data={"query": 'State "Done"', "issues": [{"idReadable": "DEV-2312"}]}
    )
    assert result.get("status") != "success"
    assert "In Progress" in result["error"]


def test_product_update_uses_owned_bundle_element():
    client = Mock()
    issues = IssuesClient(client)
    issues.get_issue = Mock(return_value=Issue(id="2-2312", project={"id": "0-66"}))
    issues._validate_custom_field_value = Mock(return_value=True)
    client.get.return_value = [{"field": {"name": "Product"}, "bundle": {
        "values": [{"name": "~Datalake", "id": "151-172"}]}}]

    issues.update_issue_custom_fields("DEV-2312", {"Product": "~Datalake"}, validate=False)

    payload = client.post.call_args.kwargs["data"]["customFields"][0]
    assert payload == {"name": "Product", "$type": "SingleOwnedIssueCustomField",
                       "value": {"id": "151-172", "$type": "OwnedBundleElement"}}
