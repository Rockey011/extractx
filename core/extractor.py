"""
AI-powered data extraction engine.
Uses LLMs to intelligently extract structured data from raw text.
"""

import json
import os
from typing import Optional, Any

# Try to import OpenAI client
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


DEFAULT_EXTRACTION_PROMPT = """Extract the key data from this web page content.
Return a JSON object with clean, structured data. 

For e-commerce: extract product name, price, description, images, variants.
For articles: extract title, author, date, summary, key points.
For profiles: extract name, bio, links, stats.
For listings: extract an array of items with their properties.

Page Title: {title}
Page URL: {url}

Content:
{content}

Return ONLY valid JSON, no other text."""


def extract_with_ai(
    content: str,
    title: str = "",
    url: str = "",
    schema: Optional[dict] = None,
    instruction: str = "",
    model: str = "gpt-4o-mini",
    api_key: str = "",
    provider: str = "openai",
) -> dict:
    """
    Extract structured data from text using AI.
    
    Args:
        content: The text content to extract data from
        title: Page title for context
        url: Source URL for context
        schema: Optional JSON schema for structured output
        instruction: Custom extraction instruction (overrides default)
        model: AI model to use
        api_key: API key for the AI provider
        provider: 'openai' or 'anthropic'
    
    Returns:
        Dictionary with extracted data
    """
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY") or ""
    
    if not api_key:
        return {
            "error": "No AI API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable.",
            "hint": "You can still use template-based extraction without AI. See --template option."
        }
    
    prompt = instruction or DEFAULT_EXTRACTION_PROMPT.format(
        title=title or "Unknown",
        url=url or "Unknown",
        content=content[:8000]  # Truncate to fit context window
    )
    
    if schema:
        prompt += f"\n\nUse this JSON schema for the output:\n{json.dumps(schema, indent=2)}"
    
    try:
        if provider == "openai" and HAS_OPENAI:
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a precise data extraction AI. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            result_text = response.choices[0].message.content
            
        elif provider == "anthropic" and HAS_ANTHROPIC:
            client = Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model,
                max_tokens=4000,
                messages=[{
                    "role": "user",
                    "content": prompt + "\n\nReturn ONLY valid JSON, no other text."
                }],
                temperature=0.1,
            )
            result_text = response.content[0].text
            
        else:
            return {
                "error": f"Provider '{provider}' not available. Install openai or anthropic package.",
                "hint": "pip install openai anthropic"
            }
        
        # Parse JSON from response
        result_text = result_text.strip()
        # Handle markdown code blocks
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
            result_text = result_text.strip()
        
        return json.loads(result_text)
        
    except json.JSONDecodeError:
        return {"error": "AI returned invalid JSON", "raw_response": result_text[:500]}
    except Exception as e:
        return {"error": str(e)}


def extract_with_template(content: str, template: dict, 
                          title: str = "", url: str = "") -> dict:
    """
    Extract data using predefined CSS selectors and regex patterns.
    This is a fallback when AI is not available.
    
    Args:
        content: Raw HTML (not plain text — use scraper.html)
        template: Template definition with selectors
        title: Page title
        url: Source URL
    
    Returns:
        Extracted data as dictionary
    """
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(content, "html.parser")
    result = {"_meta": {"title": title, "url": url}}
    
    for field_name, config in template.get("fields", {}).items():
        selector = config.get("selector")
        attr = config.get("attr", "text")
        regex = config.get("regex")
        multiple = config.get("multiple", False)
        
        try:
            elements = soup.select(selector)
            
            if multiple:
                values = []
                for el in elements:
                    if attr == "text":
                        val = el.get_text(strip=True)
                    else:
                        val = el.get(attr, "")
                    if regex:
                        import re
                        match = re.search(regex, val)
                        val = match.group(1) if match else val
                    values.append(val)
                result[field_name] = values
            else:
                if elements:
                    el = elements[0]
                    if attr == "text":
                        val = el.get_text(strip=True)
                    else:
                        val = el.get(attr, "")
                    if regex:
                        import re
                        match = re.search(regex, val)
                        val = match.group(1) if match else val
                    result[field_name] = val
                else:
                    result[field_name] = None
        except Exception as e:
            result[field_name] = f"ERROR: {e}"
    
    return result
