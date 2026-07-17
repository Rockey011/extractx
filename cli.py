#!/usr/bin/env python3
"""
ExtractX CLI — AI-Powered Web Data Extractor
=============================================

Usage:
    extractx <url> [OPTIONS]
    
Examples:
    extractx https://example.com/products
    extractx https://news.ycombinator.com --extract "title,url,points"
    extractx https://amazon.com/dp/B0XXX --template ecommerce
    extractx https://twitter.com/user --template twitter -o profile.json
"""

import argparse
import os
import sys
import json
from pathlib import Path

from core.scraper import scrape
from core.extractor import extract_with_ai, extract_with_template
from core.exporters import export

# Built-in templates
BUILTIN_TEMPLATES = {
    "ecommerce": {
        "name": "E-Commerce Product",
        "description": "Extract product details from e-commerce pages",
        "fields": {
            "product_name": {"selector": "h1", "attr": "text"},
            "price": {"selector": "[data-price], .price, .product-price, [itemprop='price']", "attr": "text"},
            "description": {"selector": "[data-description], .description, .product-description, [itemprop='description']", "attr": "text"},
            "image": {"selector": "img[itemprop='image'], .product-image img", "attr": "src"},
            "rating": {"selector": "[itemprop='ratingValue'], .rating-value", "attr": "text"},
        }
    },
    "article": {
        "name": "Article / Blog Post",
        "description": "Extract article content and metadata",
        "fields": {
            "title": {"selector": "h1, .article-title, .post-title, [itemprop='headline']", "attr": "text"},
            "author": {"selector": "[itemprop='author'], .author, .byline", "attr": "text"},
            "date": {"selector": "[itemprop='datePublished'], .date, time", "attr": "datetime"},
            "content": {"selector": "article, .article-body, .post-content, [itemprop='articleBody']", "attr": "text"},
        }
    },
    "twitter": {
        "name": "Twitter/X Profile",
        "description": "Extract Twitter/X profile data",
        "fields": {
            "name": {"selector": "[data-testid='UserName'], .profile-name", "attr": "text"},
            "handle": {"selector": "[data-testid='UserScreenName'], .profile-handle", "attr": "text"},
            "bio": {"selector": "[data-testid='UserDescription'], .profile-bio", "attr": "text"},
            "followers": {"selector": "[data-testid='followers'], .followers-count", "attr": "text"},
            "following": {"selector": "[data-testid='following'], .following-count", "attr": "text"},
        }
    },
    "linkedin": {
        "name": "LinkedIn Profile",
        "description": "Extract LinkedIn profile information",
        "fields": {
            "name": {"selector": "h1, .top-card-layout__title, .profile-name", "attr": "text"},
            "headline": {"selector": ".top-card-layout__headline, .profile-headline", "attr": "text"},
            "location": {"selector": ".top-card-layout__first-subline, .profile-location", "attr": "text"},
            "about": {"selector": "#about ~ * p, .profile-about", "attr": "text"},
        }
    },
    "hackernews": {
        "name": "Hacker News",
        "description": "Extract items from Hacker News front page",
        "fields": {
            "title": {"selector": ".titleline > a", "attr": "text", "multiple": True},
            "url": {"selector": ".titleline > a", "attr": "href", "multiple": True},
        }
    },
    "reddit": {
        "name": "Reddit Posts",
        "description": "Extract posts from a subreddit",
        "fields": {
            "title": {"selector": "[data-testid='post-title'], h3", "attr": "text", "multiple": True},
            "score": {"selector": "[data-testid='post-score'], .score", "attr": "text", "multiple": True},
            "author": {"selector": "[data-testid='post-author'], .author", "attr": "text", "multiple": True},
        }
    },
}


def load_custom_template(path: str) -> dict:
    """Load a custom YAML/JSON template file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Template file not found: {path}")
    
    content = path.read_text()
    
    if path.suffix in (".yaml", ".yml"):
        try:
            import yaml
            return yaml.safe_load(content)
        except ImportError:
            print("⚠️  PyYAML not installed. Install with: pip install pyyaml")
            sys.exit(1)
    elif path.suffix == ".json":
        return json.loads(content)
    else:
        raise ValueError(f"Unsupported template format: {path.suffix}. Use .yaml, .yml, or .json")


def main():
    parser = argparse.ArgumentParser(
        description="ExtractX — AI-Powered Web Data Extractor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  extractx https://news.ycombinator.com
  extractx https://amazon.com/dp/B0XXX --template ecommerce
  extractx https://example.com --extract "title, author, date" --ai
  extractx https://twitter.com/elonmusk --template twitter -o profile.json
  extractx https://news.ycombinator.com -f csv -o hn.csv

Built-in templates: """ + ", ".join(BUILTIN_TEMPLATES.keys()),
    )
    
    parser.add_argument("url", help="URL to extract data from")
    parser.add_argument("-t", "--template", choices=list(BUILTIN_TEMPLATES.keys()),
                        help="Built-in extraction template")
    parser.add_argument("--template-file", help="Path to custom YAML/JSON template")
    parser.add_argument("-e", "--extract", help='Fields to extract (comma-separated, e.g. "title,price")')
    parser.add_argument("--ai", action="store_true", help="Use AI-powered extraction")
    parser.add_argument("--ai-model", default="gpt-4o-mini", help="AI model (default: gpt-4o-mini)")
    parser.add_argument("--ai-provider", default="openai", choices=["openai", "anthropic"],
                        help="AI provider (default: openai)")
    parser.add_argument("--ai-key", default="", help="API key (or set OPENAI_API_KEY env)")
    parser.add_argument("-f", "--format", default="json", choices=["json", "csv", "md"],
                        help="Output format (default: json)")
    parser.add_argument("-o", "--output", help="Save output to file")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds")
    parser.add_argument("--ua", "--user-agent", help="Custom User-Agent header")
    parser.add_argument("--proxy", help="Proxy URL (e.g., http://proxy:8080)")
    parser.add_argument("--list-templates", action="store_true", help="List all built-in templates")
    parser.add_argument("--version", action="version", version="ExtractX v0.1.0")
    
    args = parser.parse_args()
    
    # List templates
    if args.list_templates:
        print("\n📋 Built-in Extraction Templates\n")
        for name, tmpl in BUILTIN_TEMPLATES.items():
            print(f"  {name:15s} — {tmpl['description']}")
            fields = tmpl.get("fields", {})
            print(f"  {'':15s}   Fields: {', '.join(list(fields.keys())[:6])}")
        print(f"\n  Use: extractx <url> --template <name>")
        return
    
    # Step 1: Scrape the URL
    print(f"🔍 Scraping {args.url}...", file=sys.stderr)
    result = scrape(args.url, timeout=args.timeout, user_agent=args.ua, proxy=args.proxy)
    
    if not result.success:
        print(f"❌ Failed to scrape: {result.error}", file=sys.stderr)
        sys.exit(1)
    
    print(f"✅ Got {len(result.text)} chars from {result.title or result.url}", file=sys.stderr)
    
    # Step 2: Extract data
    data = None
    
    if args.ai:
        print(f"🤖 Using AI ({args.ai_provider}/{args.ai_model})...", file=sys.stderr)
        instruction = ""
        if args.extract:
            instruction = f"Extract ONLY these fields from the content: {args.extract}. Return as JSON."
        
        data = extract_with_ai(
            content=result.text,
            title=result.title,
            url=result.url,
            instruction=instruction,
            model=args.ai_model,
            provider=args.ai_provider,
            api_key=args.ai_key,
        )
    
    elif args.template:
        print(f"📐 Using template: {args.template}", file=sys.stderr)
        template = BUILTIN_TEMPLATES[args.template]
        data = extract_with_template(result.html, template, result.title, result.url)
    
    elif args.template_file:
        print(f"📐 Using custom template: {args.template_file}", file=sys.stderr)
        template = load_custom_template(args.template_file)
        data = extract_with_template(result.html, template, result.title, result.url)
    
    elif args.extract:
        print(f"🤖 AI extracting: {args.extract}", file=sys.stderr)
        instruction = f"Extract ONLY these fields from the content: {args.extract}. Return as JSON."
        data = extract_with_ai(
            content=result.text,
            title=result.title,
            url=result.url,
            instruction=instruction,
            model=args.ai_model,
            provider=args.ai_provider,
            api_key=args.ai_key,
        )
    
    else:
        # Default: intelligent extraction (try AI first, fallback to metadata)
        print("🤖 Using AI auto-extraction...", file=sys.stderr)
        data = extract_with_ai(
            content=result.text,
            title=result.title,
            url=result.url,
            model=args.ai_model,
            provider=args.ai_provider,
            api_key=args.ai_key,
        )
        
        if "error" in data:
            # Fallback: return metadata
            print("⚠️  AI not available, returning page metadata", file=sys.stderr)
            data = {
                "title": result.title,
                "url": result.url,
                "text_length": len(result.text),
                "meta": result.metadata.get("meta", {}),
            }
    
    # Step 3: Export
    output = export(data, format=args.format, output=args.output)
    print(output)


if __name__ == "__main__":
    main()
