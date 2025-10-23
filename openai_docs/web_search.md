Web search
==========

Allow models to search the web for the latest information before generating a response.

Using the [Chat Completions API](/docs/api-reference/chat), you can directly access the fine-tuned models and tool used by [Search in ChatGPT](https://openai.com/index/introducing-chatgpt-search/).

When using Chat Completions, the model always retrieves information from the web before responding to your query. To use `web_search_preview` as a tool that models like `gpt-4o` and `gpt-4o-mini` invoke only when necessary, switch to using the [Responses API](/docs/guides/tools-web-search?api-mode=responses).

Currently, you need to use one of these models to use web search in Chat Completions:

*   `gpt-5-search-api`
*   `gpt-4o-search-preview`
*   `gpt-4o-mini-search-preview`

Web search parameter example

```javascript
import OpenAI from "openai";
const client = new OpenAI();

const completion = await client.chat.completions.create({
    model: "gpt-4o-search-preview",
    web_search_options: {},
    messages: [{
        "role": "user",
        "content": "What was a positive news story from today?"
    }],
});

console.log(completion.choices[0].message.content);
```

```python
from openai import OpenAI
client = OpenAI()

completion = client.chat.completions.create(
    model="gpt-4o-search-preview",
    web_search_options={},
    messages=[
        {
            "role": "user",
            "content": "What was a positive news story from today?",
        }
    ],
)

print(completion.choices[0].message.content)
```

```bash
curl -X POST "https://api.openai.com/v1/chat/completions" \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -H "Content-type: application/json" \
    -d '{
        "model": "gpt-4o-search-preview",
        "web_search_options": {},
        "messages": [{
            "role": "user",
            "content": "What was a positive news story from today?"
        }]
    }'
```

Output and citations
--------------------

The API response item in the `choices` array will include:

*   `message.content` with the text result from the model, inclusive of any inline citations
*   `annotations` with a list of cited URLs

By default, the model's response will include inline citations for URLs found in the web search results. In addition to this, the `url_citation` annotation object will contain the URL and title of the cited source, as well as the start and end index characters in the model's response where those sources were used.

When displaying web results or information contained in web results to end users, inline citations must be made clearly visible and clickable in your user interface.

```json
[
    {
        "index": 0,
        "message": {
            "role": "assistant",
            "content": "the model response is here...",
            "refusal": null,
            "annotations": [
                {
                    "type": "url_citation",
                    "url_citation": {
                        "end_index": 985,
                        "start_index": 764,
                        "title": "Page title...",
                        "url": "https://..."
                    }
                }
            ]
        },
        "finish_reason": "stop"
    }
]
```

Domain filtering
----------------

Domain filtering in web search lets you limit results to a specific set of domains. With the `filters` parameter you can set an allow-list of up to 20 URLs. When formatting URLs, omit the HTTP or HTTPS prefix. For example, use [`openai.com`](http://openai.com) instead of [`https://openai.com/`](https://openai.com/). This approach also includes subdomains in the search. Note that domain filtering is only available in the Responses API with the `web_search` tool.

User location
-------------

To refine search results based on geography, you can specify an approximate user location using country, city, region, and/or timezone.

*   The `city` and `region` fields are free text strings, like `Minneapolis` and `Minnesota` respectively.
*   The `country` field is a two-letter [ISO country code](https://en.wikipedia.org/wiki/ISO_3166-1), like `US`.
*   The `timezone` field is an [IANA timezone](https://timeapi.io/documentation/iana-timezones) like `America/Chicago`.

Note that user location is not supported for deep research models using web search.

Customizing user location

```python
from openai import OpenAI
client = OpenAI()

completion = client.chat.completions.create(
    model="gpt-4o-search-preview",
    web_search_options={
        "user_location": {
            "type": "approximate",
            "approximate": {
                "country": "GB",
                "city": "London",
                "region": "London",
            }
        },
    },
    messages=[{
        "role": "user",
        "content": "What are the best restaurants near me?",
    }],
)

print(completion.choices[0].message.content)
```

```javascript
import OpenAI from "openai";
const client = new OpenAI();

const completion = await client.chat.completions.create({
    model: "gpt-4o-search-preview",
    web_search_options: {
        user_location: {
            type: "approximate",
            approximate: {
                country: "GB",
                city: "London",
                region: "London",
            },
        },
    },
    messages: [{
        "role": "user",
        "content": "What are the best restaurants near me?",
    }],
});
console.log(completion.choices[0].message.content);
```

```bash
curl -X POST "https://api.openai.com/v1/chat/completions" \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -H "Content-type: application/json" \
    -d '{
        "model": "gpt-4o-search-preview",
        "web_search_options": {
            "user_location": {
                "type": "approximate",
                "approximate": {
                    "country": "GB",
                    "city": "London",
                    "region": "London"
                }
            }
        },
        "messages": [{
            "role": "user",
            "content": "What are the best restaurants near me?"
        }]
    }'
```

API compatibility
-----------------

Web search is available in the Responses API as the generally available version of the tool, `web_search`, as well as the earlier tool version, `web_search_preview`. To use web search in the Chat Completions API, use the specialized web search models `gpt-5-search-api`, `gpt-4o-search-preview` and `gpt-4o-mini-search-preview`.

Limitations
-----------

*   Web search is currently not supported in [`gpt-5`](/docs/models/gpt-5) with `minimal` reasoning, and [`gpt-4.1-nano`](/docs/models/gpt-4.1-nano).
*   When used as a tool in the [Responses API](/docs/api-reference/responses), web search has the same tiered rate limits as the models above.
*   Web search is limited to a context window size of 128000 (even with [`gpt-4.1`](/docs/models/gpt-4.1) and [`gpt-4.1-mini`](/docs/models/gpt-4.1-mini) models).

Usage notes
-----------

||
|ResponsesChat CompletionsAssistants|Same as tiered rate limits for underlying model used with the tool.|PricingZDR and data residency|