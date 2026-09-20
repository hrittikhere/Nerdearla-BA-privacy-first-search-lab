import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def test_real_mcp_handshake_tools_and_input_validation(tmp_path):
    async def run():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "privacy_lab.cli", "serve", "--transport", "stdio"],
            env={**os.environ, "LAB_INDEX_DIR": str(tmp_path), "LAB_BACKEND": "sqlite"},
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = (await session.list_tools()).tools
                assert len(tools) == 5
                assert all(t.annotations.readOnlyHint for t in tools)
                result = await session.call_tool("list_documents", {"limit": 1})
                assert not result.isError
                assert result.structuredContent["total"] == 0
                for name, args in [
                    ("search_documents", {"query": "test", "limit": 999}),
                    ("get_passage", {"chunk_id": "../../etc/passwd"}),
                    ("list_documents", {"min_principal_cents": -1}),
                ]:
                    assert (await session.call_tool(name, args)).isError

    asyncio.run(run())
