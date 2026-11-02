"""Regression coverage for issue state and owned custom field updates."""

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

    assert issues._apply_direct_state_update("DEMO-123", "Done") is True
    client.post.assert_called_once_with(
        "issues/DEMO-123",
        data={"customFields": [{"name": "State", "$type": "StateIssueCustomField",
                                "value": {"name": "Done", "$type": "StateBundleElement"}}]},
    )


def test_direct_state_update_does_not_claim_success_when_state_stays_old():
    client = Mock()
    client.get.return_value = {"customFields": [{"name": "State", "value": {"name": "In Progress"}}]}

    assert IssuesClient(client)._apply_direct_state_update("DEMO-123", "Done") is False


def test_state_command_uses_readable_id_and_does_not_claim_unpersisted_success():
    issues = Mock()
    issues._apply_direct_state_update.return_value = False
    issues.client.post.return_value = {}
    issues.client.get.return_value = {"customFields": [{"name": "State", "value": {"name": "In Progress"}}]}

    result = json.loads(DedicatedUpdates(issues, Mock()).update_issue_state("DEMO-123", "Done"))

    issues.client.post.assert_called_once_with(
        "commands", data={"query": 'State "Done"', "issues": [{"idReadable": "DEMO-123"}]}
    )
    assert result.get("status") != "success"
    assert "In Progress" in result["error"]


def test_product_update_uses_owned_bundle_element():
    client = Mock()
    issues = IssuesClient(client)
    issues.get_issue = Mock(return_value=Issue(id="2-2312", project={"id": "0-66"}))
    issues._validate_custom_field_value = Mock(return_value=True)
    client.get.return_value = [{"field": {"name": "Product"}, "bundle": {
        "values": [{"name": "Platform", "id": "151-172"}]}}]

    issues.update_issue_custom_fields("DEMO-123", {"Product": "Platform"}, validate=False)

    payload = client.post.call_args.kwargs["data"]["customFields"][0]
    assert payload == {"name": "Product", "$type": "SingleOwnedIssueCustomField",
                       "value": {"id": "151-172", "$type": "OwnedBundleElement"}}


def test_product_update_accepts_case_insensitive_field_name():
    client = Mock()
    issues = IssuesClient(client)
    issues.get_issue = Mock(return_value=Issue(id="2-2312", project={"id": "0-66"}))
    client.get.return_value = [{"field": {"name": "Product"}, "bundle": {
        "values": [{"name": "Platform", "id": "151-172"}]}}]

    issues.update_issue_custom_fields("DEMO-123", {"product": "Platform"}, validate=False)

    payload = client.post.call_args.kwargs["data"]["customFields"][0]
    assert payload["name"] == "Product"


def test_state_command_fallback_requires_persisted_state():
    client = Mock()
    issues = IssuesClient(client)
    issues._apply_direct_state_update = Mock(return_value=False)
    client.get.side_effect = [
        {"customFields": [{"name": "State", "value": {"name": "In Progress"}}]},
        [],
    ]

    assert issues._handle_state_transition("DEMO-123", "Done", use_commands=True) is False
    client.post.assert_called_once_with(
        "commands", data={"query": 'State "Done"', "issues": [{"idReadable": "DEMO-123"}]}
    )


def test_state_command_fallback_accepts_persisted_state():
    client = Mock()
    issues = IssuesClient(client)
    issues._apply_direct_state_update = Mock(return_value=False)
    client.get.return_value = {
        "customFields": [{"name": "State", "value": {"name": "Done"}}]
    }

    assert issues._handle_state_transition("DEMO-123", "Done", use_commands=True) is True


def test_state_command_fallback_accepts_internal_issue_id():
    client = Mock()
    issues = IssuesClient(client)
    issues._apply_direct_state_update = Mock(return_value=False)
    client.get.return_value = {
        "customFields": [{"name": "State", "value": {"name": "Done"}}]
    }

    assert issues._handle_state_transition("2-123", "Done", use_commands=True) is True
    client.post.assert_called_once_with(
        "commands", data={"query": 'State "Done"', "issues": [{"id": "2-123"}]}
    )


def test_dedicated_state_fallback_accepts_internal_issue_id():
    issues = Mock()
    issues._apply_direct_state_update.return_value = False
    issues.get_issue.return_value = {"id": "2-123", "idReadable": "DEMO-123"}
    issues.client.get.return_value = {
        "customFields": [{"name": "State", "value": {"name": "Done"}}]
    }

    result = json.loads(DedicatedUpdates(issues, Mock()).update_issue_state("2-123", "Done"))

    assert result["status"] == "success"
    issues.client.post.assert_called_once_with(
        "commands", data={"query": 'State "Done"', "issues": [{"id": "2-123"}]}
    )
