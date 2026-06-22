from app.core.config import Settings


def test_mcp_settings_defaults() -> None:
    settings = Settings(_env_file=None, llm_api_key="llm-key", rerank_api_key="rerank-key")

    assert settings.mcp_server_name == "research-agent-tools"
    assert settings.mcp_server_version == "0.1.0"
    assert settings.mcp_external_servers == ""
    assert settings.parse_external_mcp_servers() == []


def test_parse_external_mcp_servers() -> None:
    settings = Settings(
        _env_file=None,
        llm_api_key="llm-key",
        rerank_api_key="rerank-key",
        mcp_external_servers=(
            "filesystem:npx -y @modelcontextprotocol/server-filesystem /tmp|"
            "demo:python -m scripts.run_mcp_server"
        ),
    )

    assert settings.parse_external_mcp_servers() == [
        {
            "name": "filesystem",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
        },
        {
            "name": "demo",
            "command": "python",
            "args": ["-m", "scripts.run_mcp_server"],
        },
    ]


def test_parse_external_mcp_servers_skips_malformed_entries() -> None:
    settings = Settings(
        _env_file=None,
        llm_api_key="llm-key",
        rerank_api_key="rerank-key",
        mcp_external_servers="missing_separator|empty_command:",
    )

    assert settings.parse_external_mcp_servers() == []


def test_parse_external_mcp_servers_preserves_windows_backslash_paths() -> None:
    settings = Settings(
        _env_file=None,
        llm_api_key="llm-key",
        rerank_api_key="rerank-key",
        mcp_external_servers=r"demo:C:\tools\node\npx.cmd -y server C:\tmp",
    )

    assert settings.parse_external_mcp_servers() == [
        {
            "name": "demo",
            "command": r"C:\tools\node\npx.cmd",
            "args": ["-y", "server", r"C:\tmp"],
        }
    ]


def test_parse_external_mcp_servers_preserves_quoted_windows_command() -> None:
    settings = Settings(
        _env_file=None,
        llm_api_key="llm-key",
        rerank_api_key="rerank-key",
        mcp_external_servers=r'demo:"C:\Program Files\nodejs\npx.cmd" -y server C:\tmp',
    )

    assert settings.parse_external_mcp_servers() == [
        {
            "name": "demo",
            "command": r"C:\Program Files\nodejs\npx.cmd",
            "args": ["-y", "server", r"C:\tmp"],
        }
    ]
