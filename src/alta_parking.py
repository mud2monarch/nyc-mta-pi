"""
Alta Parking availability checker using Playwright to bypass Cloudflare.

Uses the HONK Mobile GraphQL API to check parking availability at Alta Ski Area.
"""

import json
from datetime import datetime
from playwright.async_api import async_playwright


ALTA_URL = "https://reserve.altaparking.com/select-parking"
GRAPHQL_URL = "https://platform.honkmobile.com/graphql"
HONK_GUID = "qc0kp53m7wnb2mb8ldl2fc"


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
    async with async_playwright() as p:
        # Launch browser with stealth settings to bypass Cloudflare
        browser = await p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/Denver'
        )

        page = await context.new_page()

        # Remove webdriver detection
        await page.add_init_script('Object.defineProperty(navigator, "webdriver", {get: () => undefined})')

        try:
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
            await browser.close()


async def get_availability_calendar() -> dict:
    """
    Get the full parking availability calendar from Alta.

    Returns:
        dict with date keys and availability status for each date
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/Denver'
        )

        page = await context.new_page()
        await page.add_init_script('Object.defineProperty(navigator, "webdriver", {get: () => undefined})')

        try:
            availability_calendar = None

            async def capture_response(response):
                nonlocal availability_calendar
                if 'graphql' in response.url:
                    try:
                        body = await response.json()
                        data = body.get('data', {})
                        if 'publicParkingAvailability' in data:
                            availability_calendar = data['publicParkingAvailability']
                    except:
                        pass

            page.on('response', capture_response)

            await page.goto(ALTA_URL, wait_until='domcontentloaded')
            await page.wait_for_timeout(5000)

            return {
                "calendar": availability_calendar,
                "error": None if availability_calendar else "Failed to load calendar"
            }

        except Exception as e:
            return {
                "calendar": None,
                "error": str(e)
            }
        finally:
            await browser.close()
