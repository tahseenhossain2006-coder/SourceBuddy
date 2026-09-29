import sys
from sourceai.extraction.scrapegraph import ScrapeGraphExtractor

def main():
    print("ScrapeGraphAI Verification")
    try:
        import scrapegraphai
        print(f"✅ ScrapeGraphAI installed: {scrapegraphai.__version__}")
    except ImportError:
        print("❌ ScrapeGraphAI not installed")
        sys.exit(1)

    extractor = ScrapeGraphExtractor()
    if not extractor.enabled:
        print("⚠️ ScrapeGraphAI disabled in configuration")

    # Try a minimal extraction on a known test page
    test_html = "<html><body><h1>Test Supplier</h1><p>MOQ: 100 pieces</p></body></html>"
    try:
        result = extractor.extract(test_html, "https://example.com")
        if result.get("company_name") or result.get("text"):
            print("✅ ScrapeGraphAI extraction test successful")
        else:
            print("❌ ScrapeGraphAI extraction returned empty")
    except Exception as e:
        print(f"❌ ScrapeGraphAI extraction failed: {e}")

if __name__ == "__main__":
    main()