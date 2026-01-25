"""
BeeGuardAI - Test Email Services
Tests report and alert email functionality.

Usage:
  python test_report.py          # Test both
  python test_report.py report   # Test report only
  python test_report.py alert    # Test alert only
"""

import requests
import sys

REPORT_URL = "http://localhost:8000/api/test/send-report"
ALERTS_URL = "http://localhost:8000/api/test/check-alerts"

def test_report():
    print("\n[REPORT] Sending test report...")
    try:
        response = requests.post(REPORT_URL, timeout=60)
        if response.status_code == 200:
            print("[OK] Report sent!")
            print(response.json())
        else:
            print(f"[FAIL] Status: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"[ERROR] {e}")

def test_alerts():
    print("\n[ALERT] Triggering alert check...")
    try:
        response = requests.post(ALERTS_URL, timeout=30)
        if response.status_code == 200:
            print("[OK] Alert check done!")
            print(response.json())
        else:
            print(f"[FAIL] Status: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"[ERROR] {e}")

def main():
    print("=" * 50)
    print("  BeeGuardAI - Test Email Services")
    print("=" * 50)

    if len(sys.argv) > 1:
        if sys.argv[1] == "report":
            test_report()
        elif sys.argv[1] == "alert":
            test_alerts()
        else:
            print("Usage: python test_report.py [report|alert]")
    else:
        # Test both
        test_alerts()
        test_report()

if __name__ == "__main__":
    main()
