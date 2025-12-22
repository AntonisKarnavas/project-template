import sys
import os

# Add the project root to the python path so imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security.auth import create_access_token
from datetime import timedelta


def main():
    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        username = "test_user"

    # Create a token valid for 24 hours for testing
    access_token = create_access_token(
        data={"sub": username}, expires_delta=timedelta(hours=24)
    )

    print(f"\n--- Generated Token for '{username}' ---")
    print(f"Algorithm: HS256")
    print(f"Expires: 24 hours")
    print("-" * 40)
    print(access_token)
    print("-" * 40)
    print(f"Usage: Authorization: Bearer {access_token}")


if __name__ == "__main__":
    main()
