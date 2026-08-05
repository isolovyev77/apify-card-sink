"""Deliver scraped product cards into a service the user connected over MCP.

Why this Actor exists. A scraper leaves its output in a dataset, but the person who ordered
the data wants a row in their own table. Between those two points there used to be a human:
export, check, upload. An MCP connector removes that step, and the user's credentials never
reach this Actor: the platform injects them on its side, and the Actor authenticates to the
proxy with its own run token.

The Actor deliberately does not know where it writes. It asks the connected service which
tools it exposes and picks one that can write. The same Actor then works against a Notion
workspace, a Supabase project or a Slack channel, depending on what the user connected.
"""
import asyncio
import os

from apify import Actor

# Tool names differ between services, and so do their separators: one exposes "create_page",
# another "notion-create-pages". Match on exact substrings rather than on the word "create":
# that also appears in create-attachment and create-file-upload, which are not where product
# cards belong.
WRITE_HINTS = ("create-pages", "create_pages", "create-page", "create_page",
               "insert", "add_row", "append", "execute_sql",
               "send_message", "post_message")


def pick_write_tool(tools):
    """Choose a tool that can write, out of whatever the service exposes.

    Returns (tool, reason_for_refusal). A refusal is described in words rather than by an
    empty result: the caller has to see what is wrong with their connection, otherwise the
    run just looks like the Actor did nothing.
    """
    if not tools:
        return None, "the connected service exposed no tools at all"
    names = {t.name: t for t in tools}
    for hint in WRITE_HINTS:
        for name, tool in names.items():
            if hint in name.lower():
                return tool, None
    return None, ("none of the tools this service exposes can write: "
                  + ", ".join(sorted(names))[:300])


def describe(tool):
    """Argument shape of a tool, in a form that survives a JSON dump.

    The SDK returns pydantic objects, and reading the attribute directly put a null in the
    dataset: the value existed but did not serialize. Without the shape there is no way to
    build a call, so this is the one thing a dry run has to get right.
    """
    for attr in ("model_dump", "dict"):
        fn = getattr(tool, attr, None)
        if callable(fn):
            try:
                return fn(mode="json") if attr == "model_dump" else fn()
            except TypeError:
                try:
                    return fn()
                except Exception:
                    pass
            except Exception:
                pass
    return {"name": getattr(tool, "name", None), "note": "shape unavailable"}


def rows_from(items, table):
    """Reduce cards to rows. We do not carry every field we scraped: the destination table
    has its own schema, and pushing our full field set into it hits unknown columns."""
    rows = []
    for it in items:
        if not isinstance(it, dict):
            continue
        rows.append({
            "platform": it.get("platform"),
            "title": it.get("title"),
            "url": it.get("url"),
            "price": it.get("price"),
            "spec_count": it.get("specCount"),
            "image_count": it.get("imageCount"),
            "scraped_at": it.get("scrapedAt"),
        })
    return {"table": table, "rows": rows}


async def main():
    async with Actor:
        inp = await Actor.get_input() or {}
        items = inp.get("items") or []
        connector_id = inp.get("outputConnector")
        table = (inp.get("targetTable") or "product_cards").strip()
        dry_run = bool(inp.get("dryRun"))

        # A refusal goes into the DATASET, not only into the log. The caller never sees the
        # log: the first run of this Actor exited on the connector check, wrote a warning to
        # the log and left an empty dataset, which from outside was indistinguishable from
        # "the Actor did nothing".
        async def refuse(status, detail):
            Actor.log.warning(detail)
            await Actor.push_data({"delivered": 0, "status": status, "detail": detail})

        if not items:
            return await refuse("no_input", "no input records: pass items")
        if not connector_id:
            return await refuse("no_connector", "no connector selected: nowhere to write")

        proxy_url = os.environ.get("APIFY_MCP_PROXY_URL")
        token = os.environ.get("APIFY_TOKEN")
        if not proxy_url or not token:
            # these variables do not exist on a local machine: connectors live on the platform
            return await refuse("no_proxy", "MCP connectors are only available in a platform run")

        payload = rows_from(items, table)
        Actor.log.info("rows prepared: %d, destination '%s'" % (len(payload["rows"]), table))

        import httpx
        from mcp import ClientSession
        from mcp.client.streamable_http import streamable_http_client

        async with httpx.AsyncClient(headers={"Authorization": "Bearer %s" % token},
                                     timeout=60) as http_client:
            # Client versions yield a different number of streams: the example in the Apify
            # docs unpacks three, the version installed here yields two. A fixed unpack
            # crashed the run with ValueError before the first request ever left the container.
            async with streamable_http_client("%s/%s" % (proxy_url, connector_id),
                                              http_client=http_client) as streams:
                read, write = streams[0], streams[1]
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = (await session.list_tools()).tools
                    Actor.log.info("service exposed %d tools (%s)"
                                   % (len(tools), ", ".join(t.name for t in tools[:8])))

                    tool, why = pick_write_tool(tools)
                    if tool is None:
                        Actor.log.warning(why)
                        await Actor.push_data({"delivered": 0, "status": "no_write_tool",
                                               "detail": why,
                                               "toolsAvailable": [t.name for t in tools]})
                        return

                    if dry_run:
                        Actor.log.info("dry run: would write through '%s'" % tool.name)
                        await Actor.push_data({"delivered": 0, "status": "dry_run",
                                               "tool": tool.name,
                                               "wouldWrite": len(payload["rows"]),
                                               "toolArguments": describe(tool),
                                               "toolsAvailable": [t.name for t in tools]})
                        return

                    try:
                        result = await session.call_tool(tool.name, arguments=payload)
                    except Exception as exc:
                        detail = "%s: %s" % (type(exc).__name__, str(exc)[:200])
                        Actor.log.warning("write through '%s' failed: %s" % (tool.name, detail))
                        await Actor.push_data({"delivered": 0, "status": "write_failed",
                                               "tool": tool.name, "detail": detail})
                        return

                    text = ""
                    for block in (getattr(result, "content", None) or []):
                        text += getattr(block, "text", "") or ""
                    Actor.log.info("written through '%s': %s" % (tool.name, text[:200]))
                    await Actor.push_data({"delivered": len(payload["rows"]),
                                           "status": "ok", "tool": tool.name,
                                           "response": text[:500]})


asyncio.run(main())
