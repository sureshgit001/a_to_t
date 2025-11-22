import requests
from bs4 import BeautifulSoup
import logging
import re

# ---------------- Helper Functions ---------------- #
def safe_text(soup, selectors):
    """
    Try multiple selectors and return the first non-empty text.
    """
    if not isinstance(selectors, list):
        selectors = [selectors]
    for sel in selectors:
        el = soup.select_one(sel)
        if el and el.get_text(strip=True):
            return el.get_text(strip=True)
    return None

def safe_attr(soup, selectors, attr):
    """
    Try multiple selectors and return the first non-empty attribute.
    """
    if not isinstance(selectors, list):
        selectors = [selectors]
    for sel in selectors:
        el = soup.select_one(sel)
        if el and attr in el.attrs:
            return el[attr]
    return None

def safe_list(soup, selectors):
    """
    Return a list of text from multiple matching elements.
    """
    if not isinstance(selectors, list):
        selectors = [selectors]
    result = []
    for sel in selectors:
        els = soup.select(sel)
        for el in els:
            text = el.get_text(strip=True)
            if text:
                result.append(text)
    return result if result else None

# ---------------- Main Scraper ---------------- #
def expand_amazon_url(short_url: str) -> str:
    """
    Expand shortened Amazon URLs (amzn.to) to full URLs.
    """
    try:
        logging.info(f"Expanding shortened URL: {short_url}")
        response = requests.head(short_url, allow_redirects=True, timeout=10)
        return response.url
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error expanding URL: {e}")

def scrape_amazon_details(url: str, orgUrl: str) -> dict:
  
    """
    Scrape Amazon product page dynamically and return detailed info.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/127.0.0.0 Safari/537.36"
        )
    }

    try:
        logging.info(f"Fetching Amazon product page: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # ---------------- Selectors ---------------- #
        availability_sel = ["#availability span", "#availability_feature_div"]
        prime_sel = [".a-icon-prime", "#primeExclusiveBadge_feature_div"]
        review_count_sel = ["#acrCustomerReviewText"]
        asin_sel = ["#ASIN", "input[name='ASIN']"]
        brand_sel = ["#bylineInfo", ".brand"]
        category_sel = ["#wayfinding-breadcrumbs_feature_div li a"]
        bullet_points_sel = ["#feature-bullets ul li span"]
        dimensions_sel = ["#productDetails_techSpec_section_1 td.a-size-base", "#productDetails_detailBullets_sections1 td.a-size-base"]
        weight_sel = ["#productDetails_techSpec_section_1 td.a-size-base", "#productDetails_detailBullets_sections1 td.a-size-base"]
        color_sel = ["#variation_color_name .selection"]
        size_sel = ["#variation_size_name .selection"]
        seller_sel = ["#sellerProfileTriggerId", "#merchant-info"]
        shipping_sel = ["#ourprice_shippingmessage", "#fast-track-message"]
        warranty_sel = ["#warranty", "#productWarranty_feature_div"]
        reviews_link_sel = ["#reviews-medley-footer a", "#seeAllReviews"]
        best_sellers_rank_sel = ["#productDetails_detailBullets_sections1 li", "#SalesRank"]
        manufacturer_sel = ["#bylineInfo_feature_div", "#productDetails_detailBullets_sections1"]

        # ---------------- Extract Values ---------------- #
        bullets = safe_list(soup, bullet_points_sel)
        description = " ".join(bullets) if bullets else None

        # Parse dimensions & weight (simple fallback)
        dimensions_text = safe_text(soup, dimensions_sel) or ""
        weight_text = safe_text(soup, weight_sel) or ""
        weight_match = re.search(r"(\d+\.?\d*)\s?(kg|g|lbs|oz)", weight_text)
        weight = weight_match.group(0) if weight_match else None

        # Best seller rank (parse #1 in category)
        best_rank_text = safe_text(soup, best_sellers_rank_sel) or ""
        rank_match = re.search(r"#\d+", best_rank_text)
        best_sellers_rank = rank_match.group(0) if rank_match else None

        return {
            "url": url,
            "orgUrl": orgUrl,
            "title": safe_text(soup, "#productTitle") or "Not Found",
            "price": safe_text(soup, [".a-price .a-offscreen", "#priceblock_ourprice", "#priceblock_dealprice"]) or "Not Found",
            "deal_price": safe_text(soup, [".a-price .a-offscreen"]) or "Not Found",
            "rating": safe_text(soup, ["i.a-icon-star span.a-icon-alt"]) or "Not Found",
            "discount": safe_text(soup, [".savingsPercentage"]) or "Not Found",
            "offer": safe_text(soup, ["#dealBadgePrimaryText"]) or "Not Found",
            "image": safe_attr(soup, ["#landingImage", "#imgTagWrapperId img"], "src") or "Not Found",
            "description": description or "Not Found",
            "availability": safe_text(soup, availability_sel) or "Not Found",
            "prime_eligible": "Yes" if safe_text(soup, prime_sel) else "No",
            "review_count": safe_text(soup, review_count_sel) or "Not Found",
            "asin": safe_text(soup, asin_sel) or "Not Found",
            "brand": safe_text(soup, brand_sel) or "Not Found",
            "category": safe_list(soup, category_sel) or [],
            "bullet_points": bullets or [],
            "dimensions": dimensions_text or "Not Found",
            "weight": weight or "Not Found",
            "color": safe_text(soup, color_sel) or "Not Found",
            "size": safe_text(soup, size_sel) or "Not Found",
            "seller": safe_text(soup, seller_sel) or "Amazon",
            "shipping": safe_text(soup, shipping_sel) or "Not Found",
            "warranty": safe_text(soup, warranty_sel) or "Not Found",
            "reviews_link": safe_attr(soup, reviews_link_sel, "href") or "Not Found",
            "best_sellers_rank": best_sellers_rank or "Not Found",
            "manufacturer": safe_text(soup, manufacturer_sel) or "Not Found"
        }

    except requests.exceptions.RequestException as e:
        logging.error(f"Request error: {e}")
        return {"error": f"Request error: {e}"}
    except Exception as e:
        logging.exception("Scraping error")
        return {"error": str(e)}
