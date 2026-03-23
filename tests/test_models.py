import json


from claude_teams.models import (
    COLOR_PALETTE,
    IdleNotification,
    InboxMessage,
    LeadMember,
    SendMessageResult,
    ShutdownApproved,
    ShutdownRequest,
    SpawnResult,
    SubAgent,
    SubAgentConfig,
    TaskAssignment,
    TaskFile,
    TeamConfig,
    TeamCreateResult,
    TeamDeleteResult,
    TeammateMember,
)


class TestColorPalette:
    def test_has_8_colors(self):
        assert len(COLOR_PALETTE) == 8

    def test_blue_first(self):
        assert COLOR_PALETTE[0] == "blue"

    def test_all_expected_colors_present(self):
        expected = {
            "blue",
            "green",
            "yellow",
            "purple",
            "orange",
            "pink",
            "cyan",
            "red",
        }
        assert set(COLOR_PALETTE) == expected


class TestLeadMember:
    def test_serializes_with_camel_case_aliases(self):
        lead = LeadMember(
            agent_id="team-lead@my-team",
            name="team-lead",
            agent_type="team-lead",
            model="claude-opus-4-6",
            joined_at=1770398183858,
            tmux_pane_id="",
            cwd="/tmp/work",
        )
        data = lead.model_dump(by_alias=True)
        assert data["agentId"] == "team-lead@my-team"
        assert data["agentType"] == "team-lead"
        assert data["joinedAt"] == 1770398183858
        assert data["tmuxPaneId"] == ""
        assert data["subscriptions"] == []

    def test_deserializes_from_camel_case_json(self):
        raw = {
            "agentId": "team-lead@my-team",
            "name": "team-lead",
            "agentType": "team-lead",
            "model": "claude-opus-4-6",
            "joinedAt": 1770398183858,
            "tmuxPaneId": "",
            "cwd": "/tmp/work",
            "subscriptions": [],
        }
        lead = LeadMember.model_validate(raw)
        assert lead.agent_id == "team-lead@my-team"
        assert lead.joined_at == 1770398183858

    def test_default_tmux_pane_id_is_empty(self):
        lead = LeadMember(
            agent_id="team-lead@t",
            name="team-lead",
            agent_type="team-lead",
            model="sonnet",
            joined_at=0,
            cwd="/tmp",
        )
        assert lead.tmux_pane_id == ""


class TestTeammateMember:
    def test_serializes_with_all_fields(self):
        mate = TeammateMember(
            agent_id="worker@my-team",
            name="worker",
            agent_type="general-purpose",
            model="sonnet",
            prompt="Do the work",
            color="blue",
            plan_mode_required=False,
            joined_at=1770398210601,
            tmux_pane_id="%34",
            cwd="/tmp/work",
            backend_type="tmux",
            is_active=False,
        )
        data = mate.model_dump(by_alias=True)
        assert data["agentId"] == "worker@my-team"
        assert data["planModeRequired"] is False
        assert data["tmuxPaneId"] == "%34"
        assert data["backendType"] == "tmux"
        assert data["isActive"] is False

    def test_defaults(self):
        mate = TeammateMember(
            agent_id="w@t",
            name="w",
            agent_type="general-purpose",
            model="sonnet",
            prompt="p",
            color="blue",
            joined_at=0,
            tmux_pane_id="%1",
            cwd="/tmp",
        )
        assert mate.plan_mode_required is False
        assert mate.backend_type == "claude-code"
        assert mate.is_active is False
        assert mate.subscriptions == []


class TestTeamConfig:
    def test_round_trip_with_lead_only(self):
        lead = LeadMember(
            agent_id="team-lead@test",
            name="team-lead",
            agent_type="team-lead",
            model="claude-opus-4-6",
            joined_at=1770398183858,
            cwd="/tmp",
        )
        config = TeamConfig(
            name="test",
            description="A test team",
            created_at=1770398183858,
            lead_agent_id="team-lead@test",
            lead_session_id="abc-123",
            members=[lead],
        )
        raw = json.loads(config.model_dump_json(by_alias=True))
        assert raw["createdAt"] == 1770398183858
        assert raw["leadAgentId"] == "team-lead@test"
        assert raw["leadSessionId"] == "abc-123"
        assert len(raw["members"]) == 1

    def test_deserializes_mixed_members(self):
        raw = {
            "name": "test",
            "description": "",
            "createdAt": 100,
            "leadAgentId": "team-lead@test",
            "leadSessionId": "sid",
            "members": [
                {
                    "agentId": "team-lead@test",
                    "name": "team-lead",
                    "agentType": "team-lead",
                    "model": "opus",
                    "joinedAt": 100,
                    "tmuxPaneId": "",
                    "cwd": "/tmp",
                    "subscriptions": [],
                },
                {
                    "agentId": "worker@test",
                    "name": "worker",
                    "agentType": "general-purpose",
                    "model": "sonnet",
                    "prompt": "do stuff",
                    "color": "blue",
                    "planModeRequired": False,
                    "joinedAt": 200,
                    "tmuxPaneId": "%5",
                    "cwd": "/tmp",
                    "subscriptions": [],
                    "backendType": "tmux",
                    "isActive": False,
                },
            ],
        }
        config = TeamConfig.model_validate(raw)
        assert len(config.members) == 2
        assert isinstance(config.members[0], LeadMember)
        assert isinstance(config.members[1], TeammateMember)


class TestTaskFile:
    def test_initial_task_excludes_none_fields(self):
        task = TaskFile(id="1", subject="Do thing", description="Details")
        data = task.model_dump(by_alias=True, exclude_none=True)
        assert "owner" not in data
        assert "metadata" not in data
        assert data["id"] == "1"
        assert data["status"] == "pending"
        assert data["blockedBy"] == []

    def test_task_with_owner_includes_it(self):
        task = TaskFile(id="2", subject="s", description="d", owner="worker")
        data = task.model_dump(by_alias=True, exclude_none=True)
        assert data["owner"] == "worker"

    def test_id_is_string(self):
        task = TaskFile(id="1", subject="s", description="d")
        assert isinstance(task.id, str)


class TestInboxMessage:
    def test_serializes_with_from_alias(self):
        msg = InboxMessage(
            from_="team-lead",
            text="hello",
            timestamp="2026-02-06T17:18:04.701Z",
            read=False,
            summary="greeting",
        )
        data = msg.model_dump(by_alias=True, exclude_none=True)
        assert data["from"] == "team-lead"
        assert "color" not in data
        assert data["summary"] == "greeting"

    def test_optional_fields_excluded_when_none(self):
        msg = InboxMessage(
            from_="w",
            text="t",
            timestamp="ts",
        )
        data = msg.model_dump(by_alias=True, exclude_none=True)
        assert "summary" not in data
        assert "color" not in data

    def test_with_color(self):
        msg = InboxMessage(
            from_="worker",
            text="done",
            timestamp="ts",
            color="blue",
            summary="status",
        )
        data = msg.model_dump(by_alias=True, exclude_none=True)
        assert data["color"] == "blue"


class TestStructuredMessages:
    def test_idle_notification(self):
        notification = IdleNotification(
            from_="worker",
            timestamp="2026-02-06T17:18:04.701Z",
        )
        data = json.loads(notification.model_dump_json(by_alias=True))
        assert data["type"] == "idle_notification"
        assert data["from"] == "worker"
        assert data["idleReason"] == "available"

    def test_task_assignment(self):
        assignment = TaskAssignment(
            task_id="1",
            subject="Do thing",
            description="Details",
            assigned_by="team-lead",
            timestamp="2026-02-06T17:18:04.701Z",
        )
        data = json.loads(assignment.model_dump_json(by_alias=True))
        assert data["type"] == "task_assignment"
        assert data["taskId"] == "1"
        assert data["assignedBy"] == "team-lead"

    def test_shutdown_request(self):
        request = ShutdownRequest(
            request_id="shutdown-1770398300000@worker",
            from_="team-lead",
            reason="Done",
            timestamp="ts",
        )
        data = json.loads(request.model_dump_json(by_alias=True))
        assert data["type"] == "shutdown_request"
        assert data["requestId"] == "shutdown-1770398300000@worker"
        assert data["from"] == "team-lead"

    def test_shutdown_approved(self):
        approval = ShutdownApproved(
            request_id="shutdown-123@worker",
            from_="worker",
            timestamp="ts",
            pane_id="%34",
            backend_type="tmux",
        )
        data = json.loads(approval.model_dump_json(by_alias=True))
        assert data["type"] == "shutdown_approved"
        assert data["paneId"] == "%34"
        assert data["backendType"] == "tmux"


class TestToolReturnModels:
    def test_team_create_result(self):
        result = TeamCreateResult(
            team_name="t",
            team_file_path="/p",
            lead_agent_id="team-lead@t",
        )
        assert result.team_name == "t"

    def test_team_delete_result(self):
        result = TeamDeleteResult(
            success=True,
            message='Cleaned up directories and worktrees for team "t"',
            team_name="t",
        )
        assert result.success is True

    def test_spawn_result(self):
        result = SpawnResult(agent_id="w@t", name="w", team_name="t")
        assert (
            result.message
            == "The agent is now running and will receive instructions via mailbox."
        )

    def test_send_message_result(self):
        result = SendMessageResult(success=True, message="sent")
        data = result.model_dump(exclude_none=True)
        assert "routing" not in data
        assert "request_id" not in data


class TestSubAgentConfig:
    def test_defaults(self):
        config = SubAgentConfig()
        assert config.enabled is True
        assert config.max_sub_agents == 5
        assert config.default_model == "fast"
        assert "general-purpose" in config.allowed_types

    def test_serializes_camel_case(self):
        config = SubAgentConfig(max_sub_agents=3)
        data = config.model_dump(by_alias=True)
        assert data["maxSubAgents"] == 3
        assert data["defaultModel"] == "fast"
        assert data["allowedTypes"] == ["general-purpose", "code-reviewer", "research"]

    def test_deserializes_from_camel_case(self):
        raw = {
            "enabled": False,
            "maxSubAgents": 10,
            "defaultModel": "balanced",
            "allowedTypes": ["research"],
        }
        config = SubAgentConfig.model_validate(raw)
        assert config.enabled is False
        assert config.max_sub_agents == 10
        assert config.default_model == "balanced"
        assert config.allowed_types == ["research"]


class TestSubAgent:
    def test_serializes_with_camel_case(self):
        sub = SubAgent(
            agent_id="helper@team",
            parent_name="worker",
            team_name="team",
            agent_type="code-reviewer",
            task_id="task-123",
            status="running",
            created_at=1000,
            process_handle="%5",
            backend_type="claude-code",
        )
        data = sub.model_dump(by_alias=True)
        assert data["agentId"] == "helper@team"
        assert data["parentName"] == "worker"
        assert data["agentType"] == "code-reviewer"
        assert data["taskId"] == "task-123"
        assert data["processHandle"] == "%5"
        assert data["backendType"] == "claude-code"

    def test_defaults(self):
        sub = SubAgent(
            agent_id="s@t",
            parent_name="p",
            team_name="t",
        )
        assert sub.agent_type == "general-purpose"
        assert sub.status == "running"
        assert sub.task_id == ""
        assert sub.process_handle == ""

    def test_round_trip(self):
        sub = SubAgent(
            agent_id="s@t",
            parent_name="p",
            team_name="t",
            agent_type="research",
            task_id="task-1",
            prompt="analyze data",
            status="completed",
            created_at=1000,
            process_handle="%10",
            backend_type="claude-code",
            model="haiku",
        )
        raw = json.loads(sub.model_dump_json(by_alias=True))
        restored = SubAgent.model_validate(raw)
        assert restored.agent_id == sub.agent_id
        assert restored.status == "completed"
        assert restored.model == "haiku"


class TestTeammateMemberSubAgentFields:
    def test_teammate_has_subagent_config(self):
        mate = TeammateMember(
            agent_id="w@t",
            name="w",
            agent_type="general-purpose",
            model="sonnet",
            prompt="p",
            color="blue",
            joined_at=0,
            tmux_pane_id="%1",
            cwd="/tmp",
        )
        assert mate.subagent_config.enabled is True
        assert mate.subagent_config.max_sub_agents == 5
        assert mate.sub_agents == []

    def test_teammate_serializes_subagent_fields(self):
        mate = TeammateMember(
            agent_id="w@t",
            name="w",
            agent_type="general-purpose",
            model="sonnet",
            prompt="p",
            color="blue",
            joined_at=0,
            tmux_pane_id="%1",
            cwd="/tmp",
            sub_agents=[
                SubAgent(
                    agent_id="s@t",
                    parent_name="w",
                    team_name="t",
                    status="running",
                )
            ],
        )
        data = mate.model_dump(by_alias=True)
        assert "subagentConfig" in data
        assert data["subagentConfig"]["enabled"] is True
        assert len(data["subAgents"]) == 1
        assert data["subAgents"][0]["parentName"] == "w"

    def test_teammate_round_trip_with_subagents(self):
        mate = TeammateMember(
            agent_id="w@t",
            name="w",
            agent_type="general-purpose",
            model="sonnet",
            prompt="p",
            color="blue",
            joined_at=0,
            tmux_pane_id="%1",
            cwd="/tmp",
            subagent_config=SubAgentConfig(enabled=True, max_sub_agents=3),
            sub_agents=[
                SubAgent(
                    agent_id="s1@t",
                    parent_name="w",
                    team_name="t",
                    agent_type="research",
                    task_id="task-1",
                    status="running",
                    created_at=1000,
                ),
                SubAgent(
                    agent_id="s2@t",
                    parent_name="w",
                    team_name="t",
                    agent_type="code-reviewer",
                    task_id="task-2",
                    status="completed",
                    created_at=2000,
                ),
            ],
        )
        raw = json.loads(mate.model_dump_json(by_alias=True))
        restored = TeammateMember.model_validate(raw)
        assert restored.subagent_config.max_sub_agents == 3
        assert len(restored.sub_agents) == 2
        assert restored.sub_agents[0].agent_type == "research"
        assert restored.sub_agents[1].status == "completed"
