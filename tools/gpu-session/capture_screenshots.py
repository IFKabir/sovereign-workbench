#!/usr/bin/env python3
"""
Automated screenshot capture for SIH presentation.
Drives the Sovereign Workbench UI via Selenium, sends queries,
waits for responses, and captures full-page screenshots.
"""

import os
import sys
import time
import json
import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("screenshots")


def setup_driver(headless=True):
    """Set up Selenium WebDriver."""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--force-device-scale-factor=1")

    try:
        driver = webdriver.Chrome(options=options)
    except Exception:
        # Try with chromedriver path
        from shutil import which
        chromedriver = which("chromedriver")
        if chromedriver:
            service = Service(executable_path=chromedriver)
            driver = webdriver.Chrome(service=service, options=options)
        else:
            logger.error("Chrome/Chromedriver not found. Install with: sudo apt install chromium-browser chromium-chromedriver")
            sys.exit(1)

    return driver


def wait_for_response(driver, timeout=120):
    """Wait for the AI response to appear in the chat."""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    start = time.time()
    last_count = 0

    while time.time() - start < timeout:
        try:
            # Look for assistant message elements
            messages = driver.find_elements(By.CSS_SELECTOR, "[data-role='assistant'], .assistant-message, [class*='assistant']")
            if len(messages) > last_count:
                # Wait a bit more for the full response to render
                time.sleep(3)
                return True
            last_count = len(messages)
        except Exception:
            pass

        # Also check for loading indicators disappearing
        try:
            spinners = driver.find_elements(By.CSS_SELECTOR, "[class*='spin'], [class*='loading'], [class*='animate-pulse']")
            if not spinners and time.time() - start > 10:
                time.sleep(2)
                return True
        except Exception:
            pass

        time.sleep(2)

    return False


def send_chat_message(driver, message):
    """Type and send a message in the chat input."""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys

    # Find the chat input
    selectors = [
        "textarea",
        "input[type='text']",
        "[contenteditable='true']",
        "[placeholder*='message']",
        "[placeholder*='query']",
        "[placeholder*='ask']",
    ]

    input_el = None
    for sel in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, sel)
            for el in elements:
                if el.is_displayed() and el.is_enabled():
                    input_el = el
                    break
            if input_el:
                break
        except Exception:
            continue

    if not input_el:
        logger.error("Could not find chat input element")
        return False

    # Clear and type message
    input_el.clear()
    input_el.send_keys(message)
    time.sleep(0.5)

    # Try clicking send button first
    send_selectors = [
        "button[type='submit']",
        "button[aria-label*='send']",
        "button[aria-label*='Send']",
        "[class*='send']",
    ]

    for sel in send_selectors:
        try:
            btn = driver.find_element(By.CSS_SELECTOR, sel)
            if btn.is_displayed() and btn.is_enabled():
                btn.click()
                return True
        except Exception:
            continue

    # Fallback: press Enter
    input_el.send_keys(Keys.RETURN)
    return True


def capture_screenshot(driver, filepath, description=""):
    """Capture a full-page screenshot."""
    driver.save_screenshot(str(filepath))
    logger.info(f"  📸 Saved: {filepath.name} — {description}")


# ─── Demo Scenarios ─────────────────────────────────────────────────────────

DEMO_SCENARIOS = [
    # 1. Dashboard Overview
    {
        "id": "01_dashboard",
        "type": "page",
        "url": "/",
        "wait": 3,
        "description": "Operations Dashboard — System Status Overview",
    },

    # 2. General Industrial Q&A
    {
        "id": "02_general_qa",
        "type": "chat",
        "query": "Compare gate valves vs globe valves for crude oil service in a refinery. Which is more suitable for isolation duty and why?",
        "description": "General Q&A — Valve Comparison (Industrial Knowledge)",
    },

    # 3. OISD Standards RAG Query
    {
        "id": "03_oisd_standards",
        "type": "chat",
        "query": "What is the minimum safe separation distance between a fired heater and a floating roof storage tank as per OISD-118 Table 3?",
        "description": "RAG Standards Lookup — OISD-118 Separation Distances",
    },

    # 4. Numerical Calculation
    {
        "id": "04_numerical_calc",
        "type": "chat",
        "query": "Calculate the pressure drop across a 150m, 8-inch Schedule 40 carbon steel pipeline carrying crude oil at 80°C with a flow rate of 500 m³/hr using the Darcy-Weisbach equation. Show all steps.",
        "description": "Engineering Calculation — Darcy-Weisbach Pressure Drop",
    },

    # 5. P&ID Schematic Analysis (upload test image)
    {
        "id": "05_pid_analysis",
        "type": "schematic",
        "image": "apps/web/public/schematics/cdu_bypass_line.png",
        "description": "P&ID Schematic Analysis — CDU Bypass Line ISA-5.1 Detection",
    },

    # 6. Safety Procedure Query
    {
        "id": "06_safety_procedure",
        "type": "chat",
        "query": "What are the mandatory pre-commissioning checks required before starting a Hydrocracker unit as per OISD-105? List at least 5 critical steps with references.",
        "description": "Safety Procedure — OISD-105 Pre-Commissioning Checks",
    },

    # 7. Shift Handover Report Generation
    {
        "id": "07_shift_handover",
        "type": "chat",
        "query": "Draft a complete shift handover report for CDU-2 night shift. Include sections for equipment status, process parameters, near-misses, and pending work orders.",
        "description": "Document Generation — Shift Handover Report",
    },

    # 8. Safety Compliance Check
    {
        "id": "08_compliance_check",
        "type": "chat",
        "query": "In a CDU bypass line, what are the safety concerns if control valve CV-101 does not follow a Double Block and Bleed arrangement? Explain the isolation risks and OISD compliance requirements.",
        "description": "Safety Compliance — DBB Isolation Analysis",
    },

    # 9. PSV Sizing Calculation
    {
        "id": "09_psv_sizing",
        "type": "chat",
        "query": "Size a pressure safety valve (PSV) for a crude oil distillation column operating at 3.5 kg/cm²g with a relief capacity of 50,000 kg/hr of hydrocarbon vapor. Use API-520 methodology.",
        "description": "Engineering Calculation — API-520 PSV Sizing",
    },

    # 10. Audit Ledger Page
    {
        "id": "10_audit_ledger",
        "type": "page",
        "url": "/audit",
        "wait": 3,
        "description": "Audit Ledger — SHA-256 Tamper-Evident Blockchain",
    },

    # 11. P&ID Analysis with Second Schematic
    {
        "id": "11_pump_manifold",
        "type": "schematic",
        "image": "apps/web/public/schematics/pump_manifold_system.png",
        "description": "P&ID Schematic Analysis — Pump Manifold System",
    },

    # 12. Hindi/Bilingual Query
    {
        "id": "12_hindi_query",
        "type": "chat",
        "query": "CDU-2 में crude oil heater H-201 का maximum allowable tube metal temperature क्या है? और अगर temperature 370°C से ऊपर जाए तो क्या emergency procedure follow करना चाहिए?",
        "description": "Bilingual Query — Hindi/English Mixed (GIGW Compliance)",
    },
]


def run_demos(driver, base_url, api_url, output_dir, project_root):
    """Run all demo scenarios and capture screenshots."""
    from selenium.webdriver.common.by import By

    output_dir = Path(output_dir)

    for scenario in DEMO_SCENARIOS:
        logger.info(f"\n{'─' * 60}")
        logger.info(f"  Demo: {scenario['description']}")
        logger.info(f"{'─' * 60}")

        try:
            if scenario["type"] == "page":
                # Simple page screenshot
                driver.get(f"{base_url}{scenario['url']}")
                time.sleep(scenario.get("wait", 3))
                capture_screenshot(driver, output_dir / f"{scenario['id']}.png", scenario["description"])

            elif scenario["type"] == "chat":
                # Navigate to chat page
                driver.get(f"{base_url}/chat")
                time.sleep(3)

                # Send the query
                if send_chat_message(driver, scenario["query"]):
                    logger.info(f"  Sent query, waiting for response...")
                    wait_for_response(driver, timeout=120)
                    time.sleep(2)

                    # Scroll to bottom to show full response
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)

                    capture_screenshot(driver, output_dir / f"{scenario['id']}.png", scenario["description"])
                else:
                    logger.warning(f"  Could not send message for {scenario['id']}")

            elif scenario["type"] == "schematic":
                # Navigate to chat page with schematic mode
                driver.get(f"{base_url}/chat?mode=schematic")
                time.sleep(3)

                # Upload image via file input
                image_path = str(Path(project_root) / scenario["image"])
                if os.path.exists(image_path):
                    try:
                        file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
                        file_input.send_keys(image_path)
                        time.sleep(3)

                        # Click analyze button
                        analyze_btns = driver.find_elements(By.XPATH, "//*[contains(text(), 'ANALYZE')]")
                        for btn in analyze_btns:
                            if btn.is_displayed():
                                btn.click()
                                break

                        # Wait for YOLO analysis
                        time.sleep(15)

                        capture_screenshot(driver, output_dir / f"{scenario['id']}.png", scenario["description"])
                    except Exception as e:
                        logger.warning(f"  Schematic upload failed: {e}")
                        capture_screenshot(driver, output_dir / f"{scenario['id']}_fallback.png", scenario["description"])
                else:
                    logger.warning(f"  Image not found: {image_path}")

        except Exception as e:
            logger.error(f"  Error in {scenario['id']}: {e}")
            try:
                capture_screenshot(driver, output_dir / f"{scenario['id']}_error.png", f"ERROR: {e}")
            except Exception:
                pass

    # Save scenario metadata
    metadata = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "scenarios": DEMO_SCENARIOS,
        "total_screenshots": len(list(output_dir.glob("*.png"))),
    }
    with open(output_dir / "screenshots_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Capture presentation screenshots")
    parser.add_argument("--output-dir", default="presentation-screenshots")
    parser.add_argument("--base-url", default="http://localhost:3000")
    parser.add_argument("--api-url", default="http://localhost:8080")
    parser.add_argument("--no-headless", action="store_true", help="Show browser window")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[2]
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Setting up Chrome WebDriver...")
    driver = setup_driver(headless=not args.no_headless)

    try:
        run_demos(driver, args.base_url, args.api_url, output_dir, project_root)
    finally:
        driver.quit()

    screenshots = list(output_dir.glob("*.png"))
    logger.info(f"\n✅ Captured {len(screenshots)} screenshots to {output_dir}")
    for s in sorted(screenshots):
        logger.info(f"  📸 {s.name}")


if __name__ == "__main__":
    main()
