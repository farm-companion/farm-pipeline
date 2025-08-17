"""
Advanced farm shop crawling with Crawl4AI.
Uses LLM extraction to get structured farm shop data.
"""
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List

from crawl4ai import (
    AsyncWebCrawler, 
    BrowserConfig, 
    CrawlerRunConfig,
    LLMConfig,
    LLMExtractionStrategy
)

# Farm shop schema for LLM extraction
FARM_SHOP_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "The name of the farm shop"
        },
        "description": {
            "type": "string", 
            "description": "Brief description of the farm shop"
        },
        "address": {
            "type": "object",
            "properties": {
                "street": {"type": "string"},
                "city": {"type": "string"},
                "county": {"type": "string"},
                "postcode": {"type": "string"}
            }
        },
        "contact": {
            "type": "object",
            "properties": {
                "phone": {"type": "string"},
                "email": {"type": "string"},
                "website": {"type": "string"}
            }
        },
        "opening_hours": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "day": {"type": "string"},
                    "hours": {"type": "string"}
                }
            }
        },
        "products": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Types of products sold (e.g., vegetables, meat, dairy)"
        },
        "services": {
            "type": "array", 
            "items": {"type": "string"},
            "description": "Services offered (e.g., farm shop, cafe, pick-your-own)"
        },
        "organic": {
            "type": "boolean",
            "description": "Whether the farm is organic certified"
        }
    },
    "required": ["name"]
}

# Test URLs - replace with actual farm shop websites
TEST_URLS = [
    "https://www.tregonnafarm.co.uk/",
    "https://www.riverford.co.uk/", 
    "https://www.daylesford.com/",
    "https://www.abelandcole.co.uk/"
]

async def extract_farm_shop_data(url: str, name: str) -> Dict[str, Any]:
    """Extract structured farm shop data using LLM."""
    print(f"🌾 Extracting data from {name}...")
    
    # Browser configuration
    browser_config = BrowserConfig(
        headless=True,
        browser_type="chromium",
        viewport_width=1920,
        viewport_height=1080,
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    # LLM configuration (you can use any LLM provider)
    llm_config = LLMConfig(
        provider="openai",  # or "anthropic", "ollama", etc.
        model="gpt-4o-mini",  # or "claude-3-haiku", "llama3.1:8b", etc.
        api_key="your-api-key-here"  # Set your API key
    )
    
    # Extraction strategy
    extraction_strategy = LLMExtractionStrategy(
        llm_config=llm_config,
        schema=FARM_SHOP_SCHEMA,
        extraction_prompt="""
        Extract farm shop information from this webpage. Focus on:
        - Business name and description
        - Physical address and contact details
        - Opening hours if available
        - Types of products sold
        - Services offered (farm shop, cafe, etc.)
        - Whether they're organic certified
        
        Be accurate and only extract information that's clearly stated on the page.
        """
    )
    
    # Crawler configuration
    run_config = CrawlerRunConfig(
        wait_for_images=True,
        wait_for_js=True,
        screenshot=True,
        extract_links=True,
        extract_metadata=True,
        extraction_strategy=extraction_strategy
    )
    
    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(
                url=url,
                config=run_config
            )
            
            # Get extracted data
            extracted_data = result.extracted_content if result.extracted_content else {}
            
            # Combine with metadata
            data = {
                "name": name,
                "url": url,
                "title": result.metadata.get("title", ""),
                "description": result.metadata.get("description", ""),
                "markdown_length": len(result.markdown),
                "links_count": len(result.links) if result.links else 0,
                "screenshot": result.screenshot is not None,
                "extracted_data": extracted_data,
                "status": "success"
            }
            
            print(f"✅ {name}: Extracted {len(extracted_data)} fields")
            return data
            
    except Exception as e:
        print(f"❌ {name}: Error - {e}")
        return {
            "name": name,
            "url": url,
            "status": "error",
            "error": str(e)
        }

async def crawl_without_llm(url: str, name: str) -> Dict[str, Any]:
    """Fallback: Crawl without LLM extraction."""
    print(f"🌾 Crawling {name} (basic extraction)...")
    
    browser_config = BrowserConfig(
        headless=True,
        browser_type="chromium",
        viewport_width=1920,
        viewport_height=1080
    )
    
    run_config = CrawlerRunConfig(
        wait_for_images=True,
        wait_for_js=True,
        screenshot=True,
        extract_links=True,
        extract_metadata=True
    )
    
    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(
                url=url,
                config=run_config
            )
            
            # Basic data extraction from markdown
            markdown = result.markdown.lower()
            
            # Simple heuristics for data extraction
            data = {
                "name": name,
                "url": url,
                "title": result.metadata.get("title", ""),
                "description": result.metadata.get("description", ""),
                "markdown_length": len(result.markdown),
                "links_count": len(result.links) if result.links else 0,
                "screenshot": result.screenshot is not None,
                "extracted_data": {
                    "name": result.metadata.get("title", name),
                    "description": result.metadata.get("description", ""),
                    "has_organic": "organic" in markdown,
                    "has_cafe": "cafe" in markdown or "coffee" in markdown,
                    "has_shop": "shop" in markdown or "store" in markdown,
                    "has_farm": "farm" in markdown
                },
                "status": "success"
            }
            
            print(f"✅ {name}: Basic extraction complete")
            return data
            
    except Exception as e:
        print(f"❌ {name}: Error - {e}")
        return {
            "name": name,
            "url": url,
            "status": "error",
            "error": str(e)
        }

async def main():
    """Main function to crawl farm shops with structured extraction."""
    print("🚀 Starting advanced farm shop crawl...")
    print(f"📋 Testing {len(TEST_URLS)} farm shop websites")
    print("-" * 50)
    
    results = []
    
    # Try LLM extraction first, fallback to basic crawling
    for url in TEST_URLS:
        name = url.split("//")[1].split("/")[0].replace("www.", "")
        
        # Check if LLM API key is available
        try:
            # You can set this via environment variable
            import os
            if os.getenv("OPENAI_API_KEY"):
                result = await extract_farm_shop_data(url, name)
            else:
                print("⚠️  No LLM API key found, using basic extraction")
                result = await crawl_without_llm(url, name)
        except:
            result = await crawl_without_llm(url, name)
        
        results.append(result)
        await asyncio.sleep(2)  # Rate limiting
    
    # Save results
    output_file = Path("advanced_crawl_results.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("-" * 50)
    print(f"📊 Advanced Crawl Summary:")
    print(f"   Total tested: {len(results)}")
    print(f"   Successful: {len([r for r in results if r['status'] == 'success'])}")
    print(f"   Failed: {len([r for r in results if r['status'] == 'error'])}")
    print(f"   Results saved to: {output_file}")
    
    # Show extracted data sample
    successful = [r for r in results if r['status'] == 'success']
    if successful:
        print(f"\n📝 Extracted data sample from {successful[0]['name']}:")
        print("-" * 40)
        extracted = successful[0].get('extracted_data', {})
        for key, value in extracted.items():
            print(f"  {key}: {value}")

if __name__ == "__main__":
    asyncio.run(main())
