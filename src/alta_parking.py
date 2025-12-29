"""
Alta Parking availability checker using Playwright to bypass Cloudflare.

Uses the HONK Mobile GraphQL API to check parking availability at Alta Ski Area.
Maintains a persistent browser instance for efficiency.
"""

import asyncio
from datetime import datetime
from playwright.async_api import async_playwright, Browser, BrowserContext, Playwright


ALTA_URL = "https://reserve.altaparking.com/select-parking"
GRAPHQL_URL = "https://platform.honkmobile.com/graphql"
HONK_GUID = "qc0kp53m7wnb2mb8ldl2fc"

# Global browser state
_playwright: Playwright | None = None
_browser: Browser | None = None
_lock = asyncio.Lock()
_request_count = 0
MAX_REQUESTS_BEFORE_RESTART = 100  # Restart browser periodically to prevent memory leaks

# Chromium args optimized for low memory usage in containers
BROWSER_ARGS = [
    '--disable-blink-features=AutomationControlled',
    '--disable-dev-shm-usage',      # Don't use /dev/shm (limited in containers)
    '--disable-gpu',                 # No GPU needed for headless
    '--no-sandbox',                  # Required for some container envs
    '--disable-extensions',
    '--disable-background-networking',
    '--disable-default-apps',
    '--disable-sync',
    '--disable-translate',
    # Note: --single-process removed - causes instability when closing contexts
]


async def _launch_browser() -> Browser:
    """Launch browser with memory-optimized settings."""
    return await _playwright.chromium.launch(headless=True, args=BROWSER_ARGS)


async def init_browser() -> None:
    """Initialize the persistent browser instance. Call on app startup."""
    global _playwright, _browser

    async with _lock:
        if _browser is not None:
            return  # Already initialized

        _playwright = await async_playwright().start()
        _browser = await _launch_browser()


async def close_browser() -> None:
    """Close the browser instance. Call on app shutdown."""
    global _playwright, _browser, _request_count

    async with _lock:
        if _browser:
            await _browser.close()
            _browser = None
        if _playwright:
            await _playwright.stop()
            _playwright = None
        _request_count = 0


async def _get_fresh_context() -> BrowserContext:
    """Get a fresh browser context, restarting browser if needed."""
    global _browser, _playwright, _request_count

    async with _lock:
        _request_count += 1

        # Restart browser periodically to prevent memory leaks
        if _request_count >= MAX_REQUESTS_BEFORE_RESTART and _browser:
            await _browser.close()
            _browser = await _launch_browser()
            _request_count = 0

        # Ensure browser is running (handle crashes)
        if _browser is None or not _browser.is_connected():
            if _playwright is None:
                _playwright = await async_playwright().start()
            _browser = await _launch_browser()

        # Create context inside lock to prevent race conditions
        context = await _browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/Denver'
        )
        return context


async def check_parking_availability(target_date: str) -> dict:
    """
    Check parking availability at Alta for a specific date.

    Args:
        target_date: Date string in YYYY-MM-DD format (e.g., "2025-01-15")

    Returns:
        dict with keys:
            - available: bool indicating if parking is available
            - date: the requested date
            - rates: list of available rates (if any)
            - calendar_status: status from availability calendar (if available)
            - error: error message (if any)
    """
    context = await _get_fresh_context()

    try:
        page = await context.new_page()

        # Remove webdriver detection
        await page.add_init_script('Object.defineProperty(navigator, "webdriver", {get: () => undefined})')

        # Variables to capture from initial page load
        cart_id = None
        availability_calendar = None

        async def capture_response(response):
            nonlocal cart_id, availability_calendar
            if 'graphql' in response.url:
                try:
                    body = await response.json()
                    data = body.get('data', {})
                    if 'createCart' in data and data['createCart'].get('cart'):
                        cart_id = data['createCart']['cart']['hashid']
                    if 'publicParkingAvailability' in data:
                        availability_calendar = data['publicParkingAvailability']
                except:
                    pass

        page.on('response', capture_response)

        # Navigate to Alta parking page
        await page.goto(ALTA_URL, wait_until='domcontentloaded')
        await page.wait_for_timeout(5000)

        if not cart_id:
            return {
                "available": False,
                "date": target_date,
                "rates": [],
                "calendar_status": None,
                "error": "Failed to create cart - page may not have loaded"
            }

        # Parse the target date and format for API
        dt = datetime.strptime(target_date, "%Y-%m-%d")
        start_time = dt.strftime("%Y-%m-%dT06:00:00-07:00")

        # Check calendar status for this date if available
        calendar_status = None
        if availability_calendar:
            date_key = dt.strftime("%Y-%m-%dT00:00:00-07:00")
            if date_key in availability_calendar:
                calendar_status = availability_calendar[date_key].get('status')

        # Change cart to target date and get rates
        rates_response = await page.evaluate('''
            async ([cartId, startTime, graphqlUrl, honkGuid]) => {
                // Change cart start time
                await fetch(`${graphqlUrl}?honkGUID=${honkGuid}`, {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({
                        operationName: "ChangeCartStartTime",
                        variables: {input: {id: cartId, startTime: startTime}},
                        query: "mutation ChangeCartStartTime($input: ChangeCartStartTimeInput!) { changeCartStartTime(input: $input) { cart { hashid startTime } errors } }"
                    })
                });

                // Get rates for the cart
                const ratesResp = await fetch(`${graphqlUrl}?honkGUID=${honkGuid}`, {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({
                        operationName: "GetRates",
                        variables: {cartId: cartId},
                        query: "query GetRates($cartId: ID!) { v2CartRates(cartId: $cartId) { hashid price description promoRate behaviourType freeFlag } }"
                    })
                });
                return await ratesResp.json();
            }
        ''', [cart_id, start_time, GRAPHQL_URL, HONK_GUID])

        rates = []
        if rates_response and 'data' in rates_response:
            rates = rates_response['data'].get('v2CartRates') or []

        return {
            "available": len(rates) > 0,
            "date": target_date,
            "rates": rates,
            "calendar_status": calendar_status,
            "error": None
        }

    except Exception as e:
        return {
            "available": False,
            "date": target_date,
            "rates": [],
            "calendar_status": None,
            "error": str(e)
        }
    finally:
        await context.close()
