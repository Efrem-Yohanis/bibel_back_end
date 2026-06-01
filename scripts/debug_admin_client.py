import os
import sys
import django
from django.test import Client

sys.path.append(r'c:\Users\efrem\bibel_back_end')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bibel_project.settings')
django.setup()

client = Client(HTTP_HOST='127.0.0.1')

login_resp = client.post('/api/auth/login/', {'username_or_email': 'admin', 'password': 'Admin123!'}, content_type='application/json')
print('login status', login_resp.status_code)
print(login_resp.content.decode())

if login_resp.status_code == 200:
    data = login_resp.json()['data']
    token = data['access_token']
    headers = {'HTTP_AUTHORIZATION': f'Bearer {token}'}
    for endpoint in ['/api/admin/users/stats', '/api/admin/languages', '/api/admin/books', '/api/admin/import/bible']:
        resp = client.get(endpoint, **headers)
        print(endpoint, resp.status_code, resp.content.decode()[:400])
