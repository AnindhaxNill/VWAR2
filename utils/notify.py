# utils/notify.py
def notify(title, message, duration=10):
    try:
        from plyer import notification
        notification.notify(
            title=title,
            message=message,
            timeout=duration
        )
    except Exception as e:
        print(f"[ERROR] Notification failed: {e}")
