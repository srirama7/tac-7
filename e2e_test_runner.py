#!/usr/bin/env python3
"""
E2E Test Runner for Synthetic Data Generation
"""
import asyncio
import json
import sys
import os
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Configuration
# Get the script's directory and navigate to project root
SCRIPT_DIR = Path(__file__).parent.absolute()
BASE_PATH = SCRIPT_DIR
ADW_ID = "644bd93f"
AGENT_NAME = "test_e2e"
TEST_NAME = "synthetic_data_generation"
APP_URL = "http://localhost:5173"
SCREENSHOT_DIR = BASE_PATH / "agents" / ADW_ID / AGENT_NAME / "img" / TEST_NAME
TEST_CSV = BASE_PATH / "test_users.csv"

# Ensure screenshot directory exists
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

async def run_test():
    """Execute the E2E test for synthetic data generation"""
    screenshots = []
    errors = []

    async with async_playwright() as p:
        # Launch browser in headed mode
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        try:
            # Step 1-2: Navigate and take initial screenshot
            print("Step 1-2: Navigating to application...")
            await page.goto(APP_URL, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)

            screenshot_path = str(SCREENSHOT_DIR / "01_initial_state.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            screenshots.append(screenshot_path)
            print(f"[OK] Screenshot saved: {screenshot_path}")

            # Step 3: Verify page title
            print("Step 3: Verifying page title...")
            title = await page.title()
            if "Natural Language SQL Interface" not in title:
                errors.append(f"(Step 3 FAIL) Page title incorrect. Expected 'Natural Language SQL Interface', got '{title}'")
                raise Exception(errors[-1])
            print("[OK] Page title verified")

            # Step 4: Verify core UI elements
            print("Step 4: Verifying core UI elements...")
            query_input = await page.query_selector("#query-input")
            if not query_input:
                errors.append("(Step 4 FAIL) Query input textbox not found")
                raise Exception(errors[-1])

            query_button = await page.query_selector("#query-button")
            if not query_button:
                errors.append("(Step 4 FAIL) Query button not found")
                raise Exception(errors[-1])

            upload_button = await page.query_selector("#upload-data-button")
            if not upload_button:
                errors.append("(Step 4 FAIL) Upload Data button not found")
                raise Exception(errors[-1])

            tables_section = await page.query_selector("#tables-section")
            if not tables_section:
                errors.append("(Step 4 FAIL) Available Tables section not found")
                raise Exception(errors[-1])

            print("[OK] All core UI elements present")

            # Step 5: Upload test CSV file
            print("Step 5: Uploading test CSV file...")
            await upload_button.click()
            await page.wait_for_timeout(1000)

            # File input is hidden, so we select it directly by ID
            file_input = await page.query_selector("#file-input")
            if not file_input:
                errors.append("(Step 5 FAIL) File input not found")
                raise Exception(errors[-1])

            await file_input.set_input_files(str(TEST_CSV))
            await page.wait_for_timeout(3000)

            print("[OK] File uploaded")

            # Step 6: Verify table appears in Available Tables
            print("Step 6: Verifying table appears...")
            table_item = await page.wait_for_selector(".table-item", timeout=10000)
            if not table_item:
                errors.append("(Step 6 FAIL) Table item not found after upload")
                raise Exception(errors[-1])
            print("[OK] Table appears in Available Tables")

            # Step 7: Verify initial row count
            print("Step 7: Verifying initial row count...")
            row_count_elem = await page.query_selector(".table-item .row-count")
            if not row_count_elem:
                errors.append("(Step 7 FAIL) Row count element not found")
                raise Exception(errors[-1])

            initial_row_count_text = await row_count_elem.inner_text()
            initial_row_count = int(initial_row_count_text.split()[0])
            print(f"[OK] Initial row count: {initial_row_count}")

            # Step 8-9: Verify Generate Data button
            print("Step 8-9: Verifying Generate Data button...")
            generate_button = await page.wait_for_selector("button:has-text('Generate')", timeout=5000)
            if not generate_button:
                errors.append("(Step 8 FAIL) Generate Data button not found")
                raise Exception(errors[-1])

            # Check button text and icon
            button_text = await generate_button.inner_text()
            if "Generate" not in button_text:
                errors.append(f"(Step 9 FAIL) Generate button text incorrect: '{button_text}'")
                raise Exception(errors[-1])

            print("[OK] Generate Data button verified")

            # Step 10: Screenshot with Generate Data button
            screenshot_path = str(SCREENSHOT_DIR / "02_generate_button_visible.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            screenshots.append(screenshot_path)
            print(f"[OK] Screenshot saved: {screenshot_path}")

            # Step 11: Click Generate Data button
            print("Step 11: Clicking Generate Data button...")
            await generate_button.click()
            await page.wait_for_timeout(1000)

            # Step 12-13: Verify button state during generation
            print("Step 12-13: Verifying button state during generation...")
            is_disabled = await generate_button.is_disabled()
            if not is_disabled:
                errors.append("(Step 12 FAIL) Generate button not disabled during generation")
                raise Exception(errors[-1])

            button_text = await generate_button.inner_text()
            if "Generating" not in button_text:
                errors.append(f"(Step 13 FAIL) Button text during generation incorrect: '{button_text}'")
                raise Exception(errors[-1])

            print("[OK] Button disabled with 'Generating...' text")

            # Step 15: Wait for generation to complete (up to 30 seconds)
            print("Step 15: Waiting for generation to complete (up to 30 seconds)...")
            try:
                # Wait for button to be re-enabled
                await page.wait_for_function(
                    "() => !document.querySelector('button:has-text(\\'Generate\\')').disabled",
                    timeout=30000
                )
                print("[OK] Generation completed")
            except PlaywrightTimeoutError:
                errors.append("(Step 15 FAIL) Generation timed out after 30 seconds")
                raise Exception(errors[-1])

            # Step 16-17: Verify success notification
            print("Step 16-17: Verifying success notification...")
            await page.wait_for_timeout(1000)

            # Look for notification/toast message
            notification = await page.query_selector(".notification, .toast, .success-message")
            if notification:
                notification_text = await notification.inner_text()
                if "10 rows" in notification_text.lower() or "added" in notification_text.lower():
                    print(f"[OK] Success notification: {notification_text}")
                else:
                    print(f"[WARN] Notification found but message unclear: {notification_text}")
            else:
                print("[WARN] No notification element found (may have disappeared)")

            # Step 18: Verify row count increased by 10
            print("Step 18: Verifying row count increased...")
            await page.wait_for_timeout(2000)
            row_count_elem = await page.query_selector(".table-item .row-count")
            new_row_count_text = await row_count_elem.inner_text()
            new_row_count = int(new_row_count_text.split()[0])

            expected_count = initial_row_count + 10
            if new_row_count != expected_count:
                errors.append(f"(Step 18 FAIL) Row count incorrect. Expected {expected_count}, got {new_row_count}")
                raise Exception(errors[-1])

            print(f"[OK] Row count increased from {initial_row_count} to {new_row_count}")

            # Step 19: Verify button re-enabled
            print("Step 19: Verifying button re-enabled...")
            generate_button = await page.query_selector("button:has-text('Generate')")
            is_disabled = await generate_button.is_disabled()
            if is_disabled:
                errors.append("(Step 19 FAIL) Generate button still disabled after completion")
                raise Exception(errors[-1])
            print("[OK] Generate button re-enabled")

            # Step 20: Screenshot of success state
            screenshot_path = str(SCREENSHOT_DIR / "03_success_notification.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            screenshots.append(screenshot_path)
            print(f"[OK] Screenshot saved: {screenshot_path}")

            # Step 21-22: Query to view generated data
            print("Step 21-22: Querying generated data...")
            await query_input.fill("SELECT * FROM test_users ORDER BY rowid DESC LIMIT 10")
            await query_button.click()
            await page.wait_for_timeout(3000)

            # Step 23-25: Verify generated data
            print("Step 23-25: Verifying generated data...")
            results_table = await page.wait_for_selector("#results-table", timeout=10000)
            if not results_table:
                errors.append("(Step 23 FAIL) Query results table not found")
                raise Exception(errors[-1])

            # Check number of rows in results
            result_rows = await page.query_selector_all("#results-table tbody tr")
            if len(result_rows) < 10:
                errors.append(f"(Step 23 FAIL) Expected at least 10 rows in results, got {len(result_rows)}")
                raise Exception(errors[-1])

            print(f"[OK] Query returned {len(result_rows)} rows")

            # Verify column structure
            headers = await page.query_selector_all("#results-table thead th")
            column_names = [await h.inner_text() for h in headers]
            expected_columns = ["id", "name", "email", "age", "city"]

            if not all(col in column_names for col in expected_columns):
                errors.append(f"(Step 24 FAIL) Column structure mismatch. Expected {expected_columns}, got {column_names}")
                raise Exception(errors[-1])

            print(f"[OK] Column structure correct: {column_names}")

            # Step 26: Screenshot of generated data
            screenshot_path = str(SCREENSHOT_DIR / "04_generated_data_results.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            screenshots.append(screenshot_path)
            print(f"[OK] Screenshot saved: {screenshot_path}")

            # Step 30: Final screenshot
            screenshot_path = str(SCREENSHOT_DIR / "05_final_state.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            screenshots.append(screenshot_path)
            print(f"[OK] Screenshot saved: {screenshot_path}")

            print("\n[OK] All test steps completed successfully!")

        except Exception as e:
            print(f"\n[FAIL] Test failed: {str(e)}")
            # Capture error screenshot
            error_screenshot = str(SCREENSHOT_DIR / "error_state.png")
            await page.screenshot(path=error_screenshot, full_page=True)
            screenshots.append(error_screenshot)

            if not errors:
                errors.append(str(e))

        finally:
            await browser.close()

    # Generate report
    report = {
        "test_name": "Synthetic Data Generation",
        "status": "passed" if not errors else "failed",
        "screenshots": screenshots,
        "error": errors[0] if errors else None
    }

    return report

if __name__ == "__main__":
    try:
        report = asyncio.run(run_test())
        print("\n" + "="*80)
        print("TEST REPORT")
        print("="*80)
        print(json.dumps(report, indent=2))

        # Exit with appropriate code
        sys.exit(0 if report["status"] == "passed" else 1)

    except Exception as e:
        print(f"Fatal error: {e}")
        error_report = {
            "test_name": "Synthetic Data Generation",
            "status": "failed",
            "screenshots": [],
            "error": str(e)
        }
        print(json.dumps(error_report, indent=2))
        sys.exit(1)
