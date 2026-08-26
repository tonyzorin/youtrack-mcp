"""Unit tests for main.py transport helpers (Compose vs docker -i)."""

import stat
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import main as mcp_main


class TestStdinDetection:
    @pytest.mark.unit
    def test_fifo_is_mcp_client(self):
        fake_stat = SimpleNamespace(st_mode=stat.S_IFIFO)
        with patch.object(mcp_main.os, "fstat", return_value=fake_stat), patch.object(
            mcp_main.sys.stdin, "fileno", return_value=0
        ):
            assert mcp_main._stdin_is_mcp_client() is True
            assert mcp_main._should_fallback_to_http() is False

    @pytest.mark.unit
    def test_tty_stays_stdio(self):
        fake_stat = SimpleNamespace(st_mode=stat.S_IFCHR)
        with patch.object(mcp_main.os, "fstat", return_value=fake_stat), patch.object(
            mcp_main.sys.stdin, "fileno", return_value=0
        ), patch.object(mcp_main.sys.stdin, "isatty", return_value=True):
            assert mcp_main._stdin_is_mcp_client() is False
            assert mcp_main._should_fallback_to_http() is False

    @pytest.mark.unit
    def test_detached_stdin_falls_back(self):
        # /dev/null in docker compose: not a fifo, not a tty
        fake_stat = SimpleNamespace(st_mode=stat.S_IFCHR)
        with patch.object(mcp_main.os, "fstat", return_value=fake_stat), patch.object(
            mcp_main.sys.stdin, "fileno", return_value=0
        ), patch.object(mcp_main.sys.stdin, "isatty", return_value=False):
            assert mcp_main._should_fallback_to_http() is True

    @pytest.mark.unit
    def test_normalize_http_alias(self):
        assert mcp_main._normalize_transport("http") == "streamable-http"
        assert mcp_main._normalize_transport("stdio") == "stdio"


class TestRunKwargs:
    """MCP SDK v2: host/port go to run() for HTTP transports only."""

    @pytest.mark.unit
    def test_create_server_omits_host_port(self):
        with patch.object(mcp_main, "load_all_tools", return_value={}), patch.object(
            mcp_main, "MCPServer"
        ) as mock_cls:
            mcp_main.create_server()
            kwargs = mock_cls.call_args.kwargs
            assert "host" not in kwargs
            assert "port" not in kwargs
            assert kwargs.get("version") == mcp_main.APP_VERSION

    @pytest.mark.unit
    def test_streamable_http_passes_host_port(self):
        fake_mcp = MagicMock()
        with patch.object(mcp_main, "create_server", return_value=fake_mcp), patch.object(
            mcp_main.sys,
            "argv",
            ["main.py", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "9000"],
        ):
            mcp_main.main()
        fake_mcp.run.assert_called_once_with(
            transport="streamable-http", host="0.0.0.0", port=9000
        )

    @pytest.mark.unit
    def test_sse_passes_host_port(self):
        fake_mcp = MagicMock()
        with patch.object(mcp_main, "create_server", return_value=fake_mcp), patch.object(
            mcp_main.sys,
            "argv",
            ["main.py", "--transport", "sse", "--host", "127.0.0.1", "--port", "8080"],
        ):
            mcp_main.main()
        fake_mcp.run.assert_called_once_with(
            transport="sse", host="127.0.0.1", port=8080
        )

    @pytest.mark.unit
    def test_stdio_does_not_pass_host_port(self):
        fake_mcp = MagicMock()
        with patch.object(mcp_main, "create_server", return_value=fake_mcp), patch.object(
            mcp_main.sys, "argv", ["main.py", "--transport", "stdio"]
        ):
            mcp_main.main()
        fake_mcp.run.assert_called_once_with(transport="stdio")

    @pytest.mark.unit
    def test_http_alias_passes_host_port(self):
        fake_mcp = MagicMock()
        with patch.object(mcp_main, "create_server", return_value=fake_mcp), patch.object(
            mcp_main.sys,
            "argv",
            ["main.py", "--transport", "http", "--host", "0.0.0.0", "--port", "8000"],
        ):
            mcp_main.main()
        fake_mcp.run.assert_called_once_with(
            transport="streamable-http", host="0.0.0.0", port=8000
        )
