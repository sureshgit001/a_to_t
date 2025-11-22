# services/playwright_amazon_service.py
import logging
import re
import time
from typing import Optional, Dict, Any
from playwright.sync_api import sync_playwright, Playwright, Browser, BrowserContext, TimeoutError as PWTimeout
import atexit

# Configurable defaults (tune via environment/config.py if you want)
DEFAULT_WAIT = 8000  # ms
NAV_TIMEOUT = 15000  # ms

class BrowserManager:
    """
    Singleton manager that starts Playwright + one persistent Browser.
    Creates new BrowserContext per request for isolation.
    """
    _playwright: Optional[Playwright] = None
    _browser: Optional[Browser] = None
    _started = False

    @classmethod
    def start(cls, headless: bool = True, chromium_args: list = None):
        if cls._started:
            return
        chromium_args = chromium_args or [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-setuid-sandbox",
            "--disable-extensions",
            "--disable-gpu"
        ]
        logging.info("Starting Playwright browser (headless=%s)...", headless)
        cls._playwright = sync_playwright().start()
        cls._browser = cls._playwright.chromium.launch(headless=headless, args=chromium_args)
        cls._started = True
        # Ensure cleanup at process exit
        atexit.register(cls.stop)

    @classmethod
    def stop(cls):
        try:
            if cls._browser:
                logging.info("Closing Playwright browser...")
                cls._browser.close()
            if cls._playwright:
                cls._playwright.stop()
        except Exception as e:
            logging.warning("Error shutting down Playwright: %s", e)
        finally:
            cls._browser = None
            cls._playwright = None
            cls._started = False

    @classmethod
    def new_context(cls, *, user_agent: Optional[str] = None, locale: Optional[str] = "en-IN") -> BrowserContext:
        if not cls._started or not cls._browser:
            # default start with headless True
            cls.start(headless=True)
        context_args = {}
        if user_agent:
            context_args["user_agent"] = user_agent
        if locale:
            context_args["locale"] = locale
        # create an isolated context (like an incognito session)
        return cls._browser.new_context(**context_args)


# Helper: lightweight selectors + parsing utilities
def _text_or_none(locator) -> Optional[str]:
    try:
        txt = locator.text_content(timeout=2000)
        return txt.strip() if txt else None
    except Exception:
        return None


def expand_amazon_url(short_url: str) -> str:
    """
    Expand amzn.to or short links using a HEAD request fallback.
    Playwright is not required for expanding; use simple requests via browser navigation as last resort.
    We'll just try a quick navigator using browser to follow redirects for reliability.
    """
    try:
        # Use a temporary context to follow redirect faster (avoids external "requests" dependency)
        ctx = BrowserManager.new_context()
        page = ctx.new_page()
        page.goto(short_url, timeout=NAV_TIMEOUT)
        final = page.url
        try:
            page.close()
        except Exception:
            pass
        try:
            ctx.close()
        except Exception:
            pass
        return final
    except Exception as e:
        logging.warning("expand_amazon_url via Playwright failed: %s; returning original", e)
        return short_url


def scrape_amazon_details(url: str, orgUrl: str) -> Dict[str, Any]:
    """
    Scrape Amazon product details using Playwright for dynamic content.
    Returns a dict with same keys as your previous scraper.
    """
    # Ensure browser started
    BrowserManager.start(headless=True)

    context = BrowserManager.new_context(user_agent=(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/127.0.0.1 Safari/537.36"
    ))
    page = context.new_page()
    page.set_default_navigation_timeout(NAV_TIMEOUT)
    page.set_default_timeout(DEFAULT_WAIT)

    try:
        logging.info("Playwright loading URL: %s", url)
        # Navigate and wait for key selectors that typically indicate product content
        page.goto(url, wait_until="domcontentloaded")

        # Wait for either product title or a common container (adjustable)
        try:
            page.wait_for_selector("#productTitle, #title, #dp", timeout=10000)
        except PWTimeout:
            logging.info("Primary selectors not found quickly; continuing anyway.")

        # Remove potential overlay/cookie banners that block content
        try:
            page.locator("button#sp-cc-accept, #sp-cc-accept, button[aria-label='Accept']").first.click(timeout=1500)
        except Exception:
            pass

        # Extract dynamically using robust locators
        def _get(selector_list):
            for sel in selector_list:
                try:
                    el = page.locator(sel).first
                    txt = el.text_content(timeout=1000)
                    if txt:
                        return txt.strip()
                except Exception:
                    continue
            return None

        def _get_attr(selector_list, attr):
            for sel in selector_list:
                try:
                    el = page.locator(sel).first
                    val = el.get_attribute(attr)
                    if val:
                        return val.strip()
                except Exception:
                    continue
            return None

        def _get_list(selector_list):
            out = []
            for sel in selector_list:
                try:
                    locs = page.locator(sel)
                    n = locs.count()
                    for i in range(n):
                        t = locs.nth(i).text_content()
                        if t:
                            out.append(t.strip())
                    if out:
                        return out
                except Exception:
                    continue
            return []

        title = _get(["#productTitle", "#title", "h1.a-size-large"]) or "Not Found"

        # Price may appear in multiple places
        price = _get([
            ".a-price .a-offscreen",
            "#priceblock_ourprice",
            "#priceblock_dealprice",
            "#tp_price_block_total_price_ww"
        ]) or "Not Found"

        deal_price = _get([
            "#priceblock_dealprice",
            ".a-price .a-offscreen"
        ]) or price

        discount = _get([
            ".savingsPercentage",
            "#regularprice_savings .a-size-medium.a-color-price",
            "#priceblock_savings .a-offscreen"
        ]) or "Not Found"

        rating = _get([
            "i.a-icon-star span.a-icon-alt",
            "#acrPopover",
            ".averageStarRating"
        ]) or "Not Found"

        review_count = _get([
            "#acrCustomerReviewText",
            "#acrCustomerReviewLink"
        ]) or "Not Found"

        image = _get_attr([
            "#landingImage",
            "#imgTagWrapperId img",
            ".imgTagWrapper img"
        ], "src") or _get_attr(["#imgTagWrapperId img"], "data-old-hires") or "Not Found"

        availability = _get([
            "#availability .a-declarative",
            "#availability span",
            "#availability_feature_div span"
        ]) or "Not Found"

        bullets = _get_list(["#feature-bullets ul li span", "#productDescription ul li", "#productDescription p"])
        description = " ".join(bullets) if bullets else _get(["#productDescription", "#feature-bullets"]) or "Not Found"

        asin = _get(["#ASIN", "input[name='ASIN']"]) or None
        if not asin:
            # try from URL
            m = re.search(r"/([A-Z0-9]{10})(?:[/?]|$)", url)
            if m:
                asin = m.group(1)
            else:
                asin = "Not Found"

        brand = _get(["#bylineInfo", "#brand", ".a-size-base.a-color-secondary"]) or "Not Found"

        category = _get_list(["#wayfinding-breadcrumbs_feature_div li a", "#wayfinding-breadcrumbs_container li a"]) or []

        # Best seller rank and dimensions often live in the details table; fetch whole table text and parse
        details_text = _get_list(["#productDetails_detailBullets_sections1 tr", "#productDetails_techSpec_section_1 tr", "#detailBullets_feature_div li"])
        details_blob = " | ".join(details_text) if details_text else ""

        # Extract weight/dimensions via regex on details_blob
        dims_match = re.search(r"((Dimensions|Product Dimensions)[^|\\n]*)", details_blob, re.IGNORECASE)
        dimensions = dims_match.group(1).strip() if dims_match else "Not Found"

        weight_match = re.search(r"(\\d+\\.?\\d*\\s?(kg|g|lbs|oz))", details_blob, re.IGNORECASE)
        weight = weight_match.group(1) if weight_match else "Not Found"

        # Best seller rank
        bsr_match = re.search(r"(#\\d+[\\d,]*)", details_blob)
        best_sellers_rank = bsr_match.group(1) if bsr_match else "Not Found"

        seller = _get(["#merchant-info", "#sellerProfileTriggerId"]) or "Not Found"
        warranty = _get(["#productWarranty_feature_div", "#warranty"]) or "Not Found"
        shipping = _get(["#ourprice_shippingmessage", "#deliveryMessageMirId"]) or "Not Found"

        # Build result - same keys as previous scraper
        result = {
            "url": url,
            "orgUrl": orgUrl,
            "title": title,
            "price": price,
            "deal_price": deal_price,
            "rating": rating,
            "discount": discount,
            "offer": _get(["#dealBadgePrimaryText"]) or "Not Found",
            "image": image,
            "description": description,
            "availability": availability,
            "prime_eligible": "Yes" if _get([".a-icon-prime", "#primeExclusiveBadge_feature_div"]) else "No",
            "review_count": review_count,
            "asin": asin,
            "brand": brand,
            "category": category,
            "bullet_points": bullets or [],
            "dimensions": dimensions,
            "weight": weight,
            "color": _get(["#variation_color_name .selection"]) or "Not Found",
            "size": _get(["#variation_size_name .selection"]) or "Not Found",
            "seller": seller,
            "shipping": shipping,
            "warranty": warranty,
            "reviews_link": _get_attr(["#reviews-medley-footer a", "#seeAllReviews"], "href") or "Not Found",
            "best_sellers_rank": best_sellers_rank,
            "manufacturer": _get(["#bylineInfo_feature_div", "#productDetails_techSpec_section_1"]) or "Not Found"
        }

        return result

    except Exception as exc:
        logging.exception("Playwright scraping error for url %s: %s", url, exc)
        return {"error": str(exc)}
    finally:
        try:
            page.close()
        except Exception:
            pass
        try:
            context.close()
        except Exception:
            pass

