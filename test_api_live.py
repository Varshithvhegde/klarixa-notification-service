import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def test_user_preferences():
    print(f"--- Testing Step 2: User Preferences ---")
    user_id = "user_123"

    # 1. Set Preference (Opt-out of SMS)
    payload = {"channel": "sms", "is_opted_in": False}
    print(f"[*] Setting preference for {user_id}: {payload}")
    try:
        response = requests.post(f"{BASE_URL}/users/{user_id}/preferences", json=payload)
        response.raise_for_status()
        print(f"[+] Success! Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"[-] Failed to set preference: {e}")

    # 2. Set Preference (Opt-in to Email)
    payload2 = {"channel": "email", "is_opted_in": True}
    print(f"[*] Setting preference for {user_id}: {payload2}")
    try:
        response = requests.post(f"{BASE_URL}/users/{user_id}/preferences", json=payload2)
        response.raise_for_status()
        print(f"[+] Success! Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"[-] Failed to set preference: {e}")

    # 3. Get Preferences
    print(f"[*] Fetching preferences for {user_id}...")
    try:
        response = requests.get(f"{BASE_URL}/users/{user_id}/preferences")
        response.raise_for_status()
        print(f"[+] Success! Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"[-] Failed to fetch preferences: {e}")

def test_notifications():
    print(f"\n--- Testing Step 3: Notifications ---")
    user_id = "user_123"

    # 1. Send Notification
    payload = {
        "user_id": user_id,
        "channel": "email",
        "priority": "high",
        "message_body": "Hello {{name}}, your order has shipped!",
        "idempotency_key": f"key_{int(time.time())}"
    }
    print(f"[*] Dispatching Notification: {payload}")
    noti_id = None
    try:
        response = requests.post(f"{BASE_URL}/notifications/", json=payload)
        response.raise_for_status()
        data = response.json()
        noti_id = data["id"]
        print(f"[+] Success! Notification created with status: {data['status']}, ID: {noti_id}")
    except requests.exceptions.RequestException as e:
        print(f"[-] Failed to create notification: {e}")

    if noti_id:
        # 2. Get Notification Status by ID
        print(f"[*] Fetching status for Notification ID: {noti_id}")
        try:
            response = requests.get(f"{BASE_URL}/notifications/{noti_id}")
            response.raise_for_status()
            print(f"[+] Status: {response.json()['status']}")
        except requests.exceptions.RequestException as e:
            print(f"[-] Failed to fetch notification status: {e}")

    # 3. Get User Notification History
    print(f"[*] Fetching User Notification History for {user_id}")
    try:
        response = requests.get(f"{BASE_URL}/notifications/user/{user_id}")
        response.raise_for_status()
        print(f"[+] Found {len(response.json())} notifications in history.")
    except requests.exceptions.RequestException as e:
        print(f"[-] Failed to fetch history: {e}")

if __name__ == "__main__":
    print("Executing Live API Tests (Ensure server is running on port 8000)")
    try:
        req = requests.get(f"{BASE_URL}/ping")
        print(f"Server health: {req.json()}")
        test_user_preferences()
        test_notifications()
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Server is not running! Please run: uvicorn app.main:app --reload")

