# card-sink

An Apify Actor that delivers scraped product cards into a service you connected over
[MCP connectors](https://docs.apify.com/platform/integrations/mcp-connectors): a Notion
workspace, a Supabase project, a Slack channel. Your credentials never reach the Actor code.
The platform injects them server-side, and the Actor authenticates to the MCP proxy with its
own run token.

Companion code for an article in the Apify writing program.

## What it does

1. Takes product card records by value (`items`).
2. Connects to the connector you selected through `APIFY_MCP_PROXY_URL/<connectorId>`.
3. Asks the service which tools it exposes, picks one that can write.
4. Writes the rows, and reports what happened in the dataset, not only in the log.

## Input

| Field | Meaning |
|---|---|
| `items` | Card records, passed by value. A run cannot read another run's dataset with standard permissions. |
| `outputConnector` | Connector ID. Rendered as a picker in Apify Console. |
| `targetTable` | Table, database or channel name. Ignored by services that do not need it. |
| `dryRun` | Connect, list the tools the service exposes, write nothing. Use it the first time you attach a connector. |

Start with `dryRun: true`. The dataset then contains `toolsAvailable` and the argument schema
of the tool that would be used, which is the fastest way to see what your service actually
offers.

## Confirmed run

One card in, one Notion page out, through a connector authorized on the Apify side:

```json
{
  "delivered": 1,
  "status": "ok",
  "tool": "notion-create-pages",
  "argumentShape": "notion-style pages"
}
```

## Notes from building it

- `streamable_http_client` yields a different number of streams across MCP SDK versions. The
  documentation example unpacks three; the version pinned here yields two. Index the result
  instead of unpacking a fixed shape.
- Tool names carry different separators per service: `create_page` in one, `notion-create-pages`
  in another. Matching on the bare word `create` also catches `create-attachment`, which is not
  where cards belong.
- Every refusal is written to the dataset. The caller sees the dataset, never the log.
- There is no universal write call. Notion wants pages with a title property and a Markdown
  body, a database wants rows, a chat wants a channel and text. The Actor reads the argument
  schema the service published and shapes the call to match, rather than guessing from the
  tool name.
- `resourceType: "mcpConnector"` patterns are matched against real tool names. `create_*`
  never matches `notion-create-pages`, and a pattern that misses leaves the user with an
  empty connector picker.

## Running it locally

MCP connectors exist only in a platform run: `APIFY_MCP_PROXY_URL` is not set on a local
machine, and the Actor reports that instead of failing.

```bash
pip install -r requirements.txt
python -m src.main
```

## License

MIT
