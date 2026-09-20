import argparse
import asyncio
import json
import sys
from pathlib import Path

from privacy_lab.config import Settings
from privacy_lab.documents import parse_pdf
from privacy_lab.service import SearchService


async def mcp_smoke(url: str):
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            expected = {
                "search_documents",
                "get_passage",
                "list_documents",
                "get_repayment_schedule",
                "corpus_status",
            }
            if {t.name for t in tools.tools} != expected:
                raise ValueError("Unexpected MCP tool surface")
            result = await session.call_tool("list_documents", {"limit": 1})
            if result.isError:
                raise ValueError("MCP list_documents failed")
            invalid = await session.call_tool("search_documents", {"query": "test", "limit": 500})
            if not invalid.isError:
                raise ValueError("MCP failed to reject an out-of-bounds request")
            return {"ok": True, "tools": sorted(expected), "catalog_result": result.model_dump()}


def main():
    parser = argparse.ArgumentParser(description="Inspectable local retrieval workshop")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect", "ingest", "verify-sources"):
        p = sub.add_parser(name)
        p.add_argument("source", type=Path, nargs="?", default=Path("data/source"))
    p = sub.add_parser("search")
    p.add_argument("query")
    p.add_argument("--document-id")
    p.add_argument("--limit", type=int, default=5)
    p = sub.add_parser("list")
    p.add_argument("--frequency", choices=["monthly", "quarterly"])
    p.add_argument("--min-principal-cents", type=int, default=0)
    p.add_argument("--category")
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--limit", type=int, default=20)
    p = sub.add_parser("passage")
    p.add_argument("chunk_id")
    p = sub.add_parser("schedule")
    p.add_argument("document_id")
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--limit", type=int, default=12)
    p = sub.add_parser("remove")
    p.add_argument("document_id")
    sub.add_parser("status")
    p = sub.add_parser("serve")
    p.add_argument("--transport", choices=["stdio", "streamable-http"], default="streamable-http")
    p = sub.add_parser("mcp-smoke")
    p.add_argument("--url", default="http://127.0.0.1:8765/mcp")
    args = parser.parse_args()
    try:
        if args.command == "inspect":
            paths = [args.source] if args.source.is_file() else sorted(args.source.rglob("*.pdf"))
            if not paths:
                raise ValueError("No PDFs found; import the corpus first")
            docs = [parse_pdf(p)[0] for p in paths]
            result = {
                "documents": len(docs),
                "pages": sum(d["pages"] for d in docs),
                "chunks": sum(d["chunks"] for d in docs),
                "repayment_rows": sum(len(d["schedule"]) for d in docs),
                "manifest": [{k: v for k, v in d.items() if k != "schedule"} for d in docs],
            }
        elif args.command == "serve":
            from privacy_lab.mcp_server import create_server

            create_server().run(transport=args.transport)
            return
        elif args.command == "mcp-smoke":
            result = asyncio.run(mcp_smoke(args.url))
        else:
            service = SearchService(Settings())
            if args.command == "ingest":
                paths = (
                    [args.source] if args.source.is_file() else sorted(args.source.rglob("*.pdf"))
                )
                result = service.ingest(paths)
            elif args.command == "search":
                result = service.search(args.query, args.limit, args.document_id)
            elif args.command == "list":
                result = service.catalog.list(
                    frequency=args.frequency,
                    min_principal_cents=args.min_principal_cents,
                    category=args.category,
                    offset=args.offset,
                    limit=args.limit,
                )
            elif args.command == "passage":
                result = service.passage(args.chunk_id)
            elif args.command == "schedule":
                result = service.schedule(args.document_id, args.offset, args.limit)
            elif args.command == "remove":
                service.remove(args.document_id)
                result = {"removed_from_index": args.document_id, "source_pdf_deleted": False}
            elif args.command == "verify-sources":
                result = service.verify_sources(args.source)
                if not result["ok"]:
                    print(json.dumps(result, indent=2))
                    sys.exit(1)
            else:
                result = service.catalog.stats()
        print(json.dumps(result, indent=2))
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
