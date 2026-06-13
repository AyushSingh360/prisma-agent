from unittest.mock import patch, MagicMock
from agent.sub_agents.base import create_sub_agent
from agent.sub_agents.coder import create_coder, CODER_PROMPT
from agent.sub_agents.debugger import create_debugger, DEBUGGER_PROMPT
from agent.sub_agents.searcher import create_searcher, SEARCHER_PROMPT
from agent.sub_agents.tester import create_tester, TESTER_PROMPT
from agent.sub_agents.spawner import create_spawned_agent, SPAWNER_PROMPT_TEMPLATE
from agent.tools import TOOLS


@patch("agent.sub_agents.base.ChatNVIDIA")
def test_create_sub_agent(mock_chat):
    mock_llm = MagicMock()
    mock_chat.return_value = mock_llm
    with patch("agent.sub_agents.base.create_agent") as mock_create:
        mock_create.return_value = "agent_executor"
        result = create_sub_agent(
            model="test-model",
            api_key="test-key",
            base_url="https://test.com/v1",
            system_prompt="You are a test agent",
            tools=TOOLS,
        )
        assert result == "agent_executor"
        mock_create.assert_called_once()


@patch("agent.sub_agents.coder.create_sub_agent")
def test_create_coder(mock_factory):
    mock_factory.return_value = "coder_agent"
    result = create_coder("model", "key", "url")
    assert result == "coder_agent"
    mock_factory.assert_called_once_with(
        model="model", api_key="key", base_url="url",
        system_prompt=CODER_PROMPT, tools=TOOLS,
    )


@patch("agent.sub_agents.debugger.create_sub_agent")
def test_create_debugger(mock_factory):
    from agent.tools import read_file, run_command, grep_search, glob_files, list_directory
    mock_factory.return_value = "debugger_agent"
    result = create_debugger("model", "key", "url")
    assert result == "debugger_agent"
    mock_factory.assert_called_once()


@patch("agent.sub_agents.searcher.create_sub_agent")
def test_create_searcher(mock_factory):
    from agent.tools import read_file, grep_search, glob_files, list_directory, search_web
    mock_factory.return_value = "searcher_agent"
    result = create_searcher("model", "key", "url")
    assert result == "searcher_agent"
    mock_factory.assert_called_once()
    call_kwargs = mock_factory.call_args[1]
    assert search_web in call_kwargs["tools"]


@patch("agent.sub_agents.tester.create_sub_agent")
def test_create_tester(mock_factory):
    mock_factory.return_value = "tester_agent"
    result = create_tester("model", "key", "url")
    assert result == "tester_agent"
    mock_factory.assert_called_once_with(
        model="model", api_key="key", base_url="url",
        system_prompt=TESTER_PROMPT, tools=TOOLS,
    )


@patch("agent.sub_agents.spawner.create_sub_agent")
def test_create_spawned_agent(mock_factory):
    mock_factory.return_value = "spawned_agent"
    task = "Set up configuration files"
    expected_prompt = SPAWNER_PROMPT_TEMPLATE.format(task_description=task)
    result = create_spawned_agent("model", "key", "url", task)
    assert result == "spawned_agent"
    mock_factory.assert_called_once_with(
        model="model", api_key="key", base_url="url",
        system_prompt=expected_prompt, tools=TOOLS,
    )


@patch("agent.sub_agents.base.ChatNVIDIA")
def test_create_sub_agent_called_with_extra_body(mock_chat):
    mock_llm = MagicMock()
    mock_chat.return_value = mock_llm
    with patch("agent.sub_agents.base.THINKING", True):
        with patch("agent.sub_agents.base.create_agent") as mock_create:
            mock_create.return_value = "executor"
            create_sub_agent("m", "k", "u", "prompt", TOOLS)
            mock_chat.assert_called_once()
            kwargs = mock_chat.call_args[1]
            assert "extra_body" in kwargs
            assert "chat_template_kwargs" in kwargs["extra_body"]
