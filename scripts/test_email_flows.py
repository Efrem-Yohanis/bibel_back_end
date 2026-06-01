import argparse
import requests
import sys


def send_forgot_password(base_url: str, email: str) -> None:
    url = f"{base_url.rstrip('/')}/forgot-password"
    payload = {"email": email}
    print(f"POST {url}\nPayload: {payload}\n")
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(response.text)


def verify_email(base_url: str, token: str) -> None:
    url = f"{base_url.rstrip('/')}/verify-email"
    payload = {"token": token}
    print(f"POST {url}\nPayload: {payload}\n")
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(response.text)


def resend_verification(base_url: str, email: str) -> None:
    url = f"{base_url.rstrip('/')}/send-verification-code"
    payload = {"email": email}
    print(f"POST {url}\nPayload: {payload}\n")
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(response.text)


def main() -> int:
    parser = argparse.ArgumentParser(description="Test Bible Quiz auth email flows")
    parser.add_argument("--base-url", default="https://bibel-quiz.onrender.com/api/auth",
                        help="Base auth API URL")
    parser.add_argument("--email", help="User email for forgot password / resend verification")
    parser.add_argument("--token", help="Email verification token")
    parser.add_argument("--forgot-password", action="store_true",
                        help="Send forgot password request")
    parser.add_argument("--verify-email", action="store_true",
                        help="Send email verification request")
    parser.add_argument("--resend-verification", action="store_true",
                        help="Resend verification email")

    args = parser.parse_args()

    if not (args.forgot_password or args.verify_email or args.resend_verification):
        parser.print_help()
        return 1

    if args.forgot_password or args.resend_verification:
        if not args.email:
            print("Error: --email is required for forgot-password or resend-verification")
            return 1

    if args.verify_email and not args.token:
        print("Error: --token is required for verify-email")
        return 1

    if args.forgot_password:
        send_forgot_password(args.base_url, args.email)

    if args.resend_verification:
        resend_verification(args.base_url, args.email)

    if args.verify_email:
        verify_email(args.base_url, args.token)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
