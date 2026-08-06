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

---

# По-русски

Актор отдаёт собранные карточки товаров прямо в сервис заказчика через
[MCP-коннектор Apify](https://docs.apify.com/platform/integrations/mcp-connectors): рабочее
пространство Notion, проект Supabase, канал в чате. Ключи заказчика в код актора не попадают:
площадка подставляет их на своей стороне, а актор ходит к прокси со своим токеном прогона.

Сопроводительный код к статье для блога Apify.

## Что делает

1. Принимает карточки значениями (`items`).
2. Подключается к выбранному коннектору по адресу `APIFY_MCP_PROXY_URL/<connectorId>`.
3. Спрашивает у сервиса список инструментов и выбирает тот, что умеет писать.
4. Пишет строки и сообщает результат в наборе данных, а не только в журнале.

## Вход

| Поле | Что означает |
|---|---|
| `items` | Карточки, переданные значениями. Прогон не может прочитать набор данных чужого прогона с обычными правами. |
| `outputConnector` | Идентификатор коннектора. В консоли рисуется выбором из списка. |
| `targetTable` | Имя таблицы, базы или канала. Сервисы, которым оно не нужно, его игнорируют. |
| `dryRun` | Подключиться, показать список инструментов сервиса и ничего не писать. Так стоит начинать при первом подключении коннектора. |

Начинайте с `dryRun: true`. Тогда в наборе данных окажутся `toolsAvailable` и схема аргументов
того инструмента, который был бы вызван. Это самый быстрый способ увидеть, что ваш сервис
вообще умеет.

## Грабли, на которых это собиралось

- `streamable_http_client` в разных версиях клиента протокола отдаёт разное число потоков.
  В примере из документации их три, в закреплённой здесь версии два. Брать по индексу,
  а не распаковывать жёстко.
- Имена инструментов у сервисов идут с разными разделителями: где-то `create_page`, где-то
  `notion-create-pages`. Совпадение по одному слову `create` заодно ловит `create-attachment`,
  куда карточкам не место.
- Универсального вызова записи не существует. Notion ждёт страницы с заголовком и телом
  в Markdown, база - строки, чат - канал и текст. Актор читает опубликованную схему
  инструмента и подстраивает вызов, а не гадает по названию.
- Шаблоны в `resourceType: "mcpConnector"` сверяются с настоящими именами инструментов.
  `create_*` никогда не совпадёт с `notion-create-pages`, и промах оставит заказчика перед
  пустым списком коннекторов.
- Любой отказ пишется в набор данных. Вызывающая сторона видит набор данных, а не журнал.

## Запуск на своей машине

Коннекторы живут только в прогоне на площадке: переменной `APIFY_MCP_PROXY_URL` на локальной
машине нет, и актор об этом честно сообщает, а не падает.

```bash
pip install -r requirements.txt
python -m src.main
```

## Лицензия

MIT

---

# По-русски

Актор отдаёт собранные карточки товаров прямо в сервис заказчика через
[MCP-коннектор Apify](https://docs.apify.com/platform/integrations/mcp-connectors): в рабочее
пространство Notion, в проект Supabase, в канал Slack. Ключи заказчика в код актора не
попадают: площадка подставляет их на своей стороне, а актор обращается к прокси со своим
токеном прогона.

Код написан к статье для программы авторов Apify.

## Что он делает

1. Принимает записи карточек значениями (`items`).
2. Подключается к выбранному коннектору по адресу `APIFY_MCP_PROXY_URL/<connectorId>`.
3. Спрашивает у сервиса список инструментов и выбирает тот, что умеет писать.
4. Пишет строки и сообщает результат в наборе данных, а не только в журнале.

## Вход

| Поле | Смысл |
|---|---|
| `items` | Записи карточек, передаются значениями. Актор с обычными правами не может читать набор данных чужого прогона. |
| `outputConnector` | Идентификатор коннектора. В консоли отрисовывается выбором из списка. |
| `targetTable` | Имя таблицы, базы или канала. Сервисы, которым это не нужно, поле игнорируют. |
| `dryRun` | Подключиться, показать инструменты сервиса, ничего не писать. Так стоит начинать при первом подключении коннектора. |

Начинайте с `dryRun: true`. В наборе данных тогда окажутся `toolsAvailable` и схема
аргументов того инструмента, который был бы вызван: быстрее всего понять, что именно
предлагает ваш сервис.

## Грабли, на которых это собиралось

- `streamable_http_client` в разных версиях клиента протокола отдаёт разное число потоков.
  В примере из документации их три, в закреплённой здесь версии два. Брать по индексу,
  а не распаковывать жёстко.
- Имена инструментов у сервисов идут с разными разделителями: где-то `create_page`, где-то
  `notion-create-pages`. Ловить по слову `create` нельзя: под него попадут
  `create-attachment` и `create-file-upload`, а карточкам там не место.
- Универсального вызова записи не существует. Notion ждёт страницы с заголовком и телом
  в Markdown, база - строки, чат - канал и текст. Актор читает опубликованную схему
  инструмента и подстраивает вызов, а не угадывает по названию.
- Каждый отказ пишется в набор данных. Вызывающая сторона видит набор данных, журнал - нет.
- Шаблоны в `resourceType: "mcpConnector"` сверяются с настоящими именами инструментов.
  `create_*` никогда не совпадёт с `notion-create-pages`, а промах шаблона оставляет
  заказчика перед пустым списком коннекторов.

## Запуск на своей машине

Коннекторы существуют только в прогоне на площадке: переменной `APIFY_MCP_PROXY_URL` на
локальной машине нет, и актор честно сообщает об этом вместо падения.

```bash
pip install -r requirements.txt
python -m src.main
```
