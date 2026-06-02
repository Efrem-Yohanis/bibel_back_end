"""Simple render test script for admin login and admin endpoint checks."""

import argparse
import requests
import sys


def login(base_url: str, identifier: str, password: str, timeout: int = 15):
    url = f"{base_url.rstrip('/')}/api/auth/login"
    payload = {
        "username_or_email": identifier,
        "password": password,
    }
    response = requests.post(url, json=payload, timeout=timeout)
    print(f"LOGIN {url} -> {response.status_code}")
    print(response.text)
    if response.status_code != 200:
        response.raise_for_status()
    return response.json()["data"]["access_token"]


def call_admin(base_url: str, token: str, endpoint: str, timeout: int = 15):
    url = f"{base_url.rstrip('/')}/api/admin{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    response = requests.get(url, headers=headers, timeout=timeout)
    print(f"GET {url} -> {response.status_code}")
    print(response.text)
    return response


def main():
    parser = argparse.ArgumentParser(description="Render admin API smoke test")
    parser.add_argument("--base-url", default="https://bibel-quiz.onrender.com",
                        help="Render service base URL")
    parser.add_argument("--email", default="admin@example.com",
                        help="Admin login email")
    parser.add_argument("--username", default="admin",
                        help="Admin login username")
    parser.add_argument("--password", default="StrongPass123!",
                        help="Admin login password")
    parser.add_argument("--timeout", type=int, default=15,
                        help="HTTP request timeout in seconds")
    args = parser.parse_args()

    try:
        token = login(args.base_url, args.email, args.password, timeout=args.timeout)
    except Exception:
        print("EMAIL login failed, trying username login...")
        try:
            token = login(args.base_url, args.username, args.password, timeout=args.timeout)
        except Exception as exc:
            print(f"ERROR: failed to log in with username too: {exc}")
            return 1

    endpoints = [
        "/users",
        "/users/stats",
        "/books",
        "/languages",
    ]

    failed = False
    for endpoint in endpoints:
        try:
            response = call_admin(args.base_url, token, endpoint, timeout=args.timeout)
            if response.status_code != 200:
                failed = True
        except Exception as exc:
            print(f"ERROR: request failed for {endpoint}: {exc}")
            failed = True

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
