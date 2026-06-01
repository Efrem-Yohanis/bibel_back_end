import requests

url = "https://bibel-quiz.onrender.com/api/auth/register"
payload = {
    "username": "efrem_test_user_003",
    "email": "icraft.efrem1@gmail.com",
    "password": "StrongPass123!",
    "confirm_password": "StrongPass123!"
}

response = requests.post(url, json=payload)
print("Status:", response.status_code)
print("Body:", response.text)



EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com