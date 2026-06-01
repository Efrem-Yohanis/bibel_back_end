import os
import sys
import django
import requests

sys.path.append(r'c:\Users\efrem\bibel_back_end')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bibel_project.settings')
django.setup()

base_url = 'http://127.0.0.1:8000'
print('base_url', base_url)
try:
    r = requests.post(
        f'{base_url}/api/auth/login',
        json={'username_or_email': 'admin', 'password': 'Admin123!'}
    )
    print('login_status', r.status_code)
    print('login_body', r.text)
    if r.status_code == 200:
        token = r.json()['data']['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        for endpoint in ['/api/admin/users/stats', '/api/admin/languages', '/api/admin/books', '/api/admin/import/bible']:
            rr = requests.get(f'{base_url}{endpoint}', headers=headers)
            print(endpoint, rr.status_code, rr.text[:400])
except Exception as e:
    print('exception', e)
