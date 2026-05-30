import os
import time
from typing import Optional

import certifi
import requests

BASE_URL = 'https://bibel-quiz.onrender.com'
VERIFY = certifi.where()
SESSION = requests.Session()
SESSION.verify = VERIFY
SESSION.trust_env = False


def send_request(method: str, url: str, **kwargs):
    kwargs.setdefault('verify', VERIFY)
    try:
        return SESSION.request(method, url, **kwargs)
    except requests.exceptions.SSLError as err:
        print('Warning: SSL verification failed. Retrying without certificate verification for debugging...')
        return SESSION.request(method, url, verify=False, **{k: v for k, v in kwargs.items() if k != 'verify'})


def register_user(username: str, password: str, email: Optional[str] = None):
    url = f"{BASE_URL}/api/auth/register"
    payload = {
        'username': username,
        'password': password,
        'confirm_password': password,
        'email': email
    }

    response = send_request('POST', url, json=payload)
    return response


def login_user(username_or_email: str, password: str):
    url = f"{BASE_URL}/api/auth/login"
    payload = {
        'username_or_email': username_or_email,
        'password': password
    }

    response = send_request('POST', url, json=payload)
    return response


def get_chapter_audio(book_name: str, chapter_number: int, token: str, language: str = 'en'):
    url = f"{BASE_URL}/api/bible/books/{book_name}/chapters/{chapter_number}"
    headers = {'Authorization': f'Bearer {token}'}
    params = {'language': language}
    response = send_request('GET', url, headers=headers, params=params)
    return response


def get_user_audio_progress(book_id: int, token: str):
    url = f"{BASE_URL}/api/bible/audio/books/{book_id}/progress"
    headers = {'Authorization': f'Bearer {token}'}
    response = send_request('GET', url, headers=headers)
    return response


def main():
    username = f"render_test_user_{int(time.time())}"
    password = 'TestPass123!'
    email = f"{username}@example.com"

    print('=== Register ===')
    reg_response = register_user(username, password, email)
    print(reg_response.status_code, reg_response.text)

    if reg_response.status_code == 400 and reg_response.json().get('errors'):
        print('Registration failed, attempting login with the same account...')
    elif reg_response.status_code not in (200, 201):
        raise SystemExit('Registration failed; aborting.')

    print('\n=== Login ===')
    login_response = login_user(username, password)
    print(login_response.status_code, login_response.text)
    login_response.raise_for_status()

    data = login_response.json().get('data', {})
    access_token = data.get('access_token')
    if not access_token:
        raise SystemExit('Login did not return access_token.')

    book_name = 'Genesis'
    chapter_number = 1

    print(f"\n=== Fetch chapter audio for {book_name} chapter {chapter_number} ===")
    chapter_response = get_chapter_audio(book_name, chapter_number, access_token)
    print(chapter_response.status_code, chapter_response.text)

    if chapter_response.ok:
        chapter_json = chapter_response.json()
        chapter_data = chapter_json.get('audio_url') or chapter_json.get('data', {}).get('audio_url')
        print('Audio URL:', chapter_data)
        if 'data' in chapter_json:
            print('Chapter response data:', chapter_json['data'])
    else:
        print('Failed to fetch chapter audio. Response body:')
        try:
            print(chapter_response.json())
        except ValueError:
            print(chapter_response.text)

    print('\n=== Fetch user audio progress (optional) ===')
    # Replace book_id with a real ID if available. The deployed API route is /api/bible/audio/books/{book_id}/progress
    try:
        progress_response = get_user_audio_progress(1, access_token)
        print(progress_response.status_code, progress_response.text)
    except requests.exceptions.SSLError as ssl_err:
        print('SSL error when calling progress endpoint:', ssl_err)
        print('If this persists, try running the script with the system CA bundle or use a local network without MITM proxies.')


if __name__ == '__main__':
    main()
