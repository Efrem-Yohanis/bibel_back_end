import requests

url = "https://bibel-quiz.onrender.com/api/auth/register"
payload = {
    "username": "efrem_test_user_09",
    "email": "efremyohanis116@gmail.com",
    "password": "StrongPass123!",
    "confirm_password": "StrongPass123!"
}

response = requests.post(url, json=payload)
print("Status:", response.status_code)
print("Body:", response.text)



