# ExtractX — AI Web Data Extractor

Extract structured data from any website using AI. Point it at a URL and get clean JSON, CSV, or Markdown.

## Quick start

```bash
pip install extractx

# Simple: auto-extract with AI
extractx https://news.ycombinator.com --ai > hn.json

# With templates (no AI needed)
extractx https://twitter.com/elonmusk --template twitter -o profile.csv -f csv

# Amazon products
extractx https://amazon.com/dp/B0XXX --template ecommerce -f json
```

Set `OPENAI_API_KEY` env var for AI-powered extraction.

## Features

- **AI extraction** — understands page content and extracts structured data
- **6 built-in templates** — ecommerce, article, twitter, linkedin, hackernews, reddit
- **Multi-format export** — JSON, CSV, Markdown table
- **Custom templates** — define your own YAML selectors
- **JavaScript support** — coming soon (Playwright integration)

## Install

```bash
pip install extractx
# or from source:
git clone https://github.com/Rockey011/extractx
cd extractx && pip install -e .
```

## Usage

```bash
# List available templates
extractx --list-templates

# Use a template
extractx <url> --template <name> [-f json|csv|md] [-o output.ext]

# AI-powered extraction
extractx <url> --ai [--ai-model gpt-4o-mini] [--extract "field1,field2"]

# Custom template
extractx <url> --template-file my_template.yaml
```

## Templates

| Template | Source | Fields |
|----------|--------|--------|
| `ecommerce` | Amazon, Shopify | product_name, price, description, image, rating |
| `article` | Blogs, news | title, author, date, content |
| `twitter` | X/Twitter | name, handle, bio, followers, following |
| `linkedin` | LinkedIn | name, headline, location, about |
| `hackernews` | HN | title, url (30 latest) |
| `reddit` | Reddit | title, score, author |

## License

MIT — [Rockey011](https://github.com/Rockey011)
