import asyncio
from pyrogram import Client
from anony import config, db

async def login():
    print("Pyrogram Session Login Utility")
    print("-" * 30)

    phone = input("Enter Phone Number (with country code): ")

    client = Client(
        name="AnonyLogin",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        in_memory=True
    )

    await client.connect()

    try:
        code = await client.send_code(phone)
        otp = input("Enter the OTP sent to your phone: ")

        try:
            await client.sign_in(phone, code.phone_code_hash, otp)
        except Exception as e:
            if "PASSWORD_HASH_INVALID" in str(e) or "two-step" in str(e).lower():
                password = input("Enter your Two-Step Verification password: ")
                await client.check_password(password)
            else:
                raise e

        session_string = await client.export_session_string()

        print("\nLogin Successful!")
        print(f"Session String: {session_string}")

        print("\nSaving to database...")
        await db.connect()

        choice = input("Save as assistant 1, 2, or 3? (default 1): ").strip()
        name_map = {"1": "one", "2": "two", "3": "three"}
        key = name_map.get(choice, "one")

        await db.set_session(key, session_string)
        print(f"Successfully saved as assistant '{key}' in SQLite database.")

        print("-" * 30)
        print("Tip: If you encounter 'Sign in to confirm you’re not a bot' on YouTube,")
        print("export your browser cookies as Netscape format, upload to batbin.me,")
        print("and add the raw URL to COOKIES_URL in your .env file.")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        await client.disconnect()
        await db.close()

if __name__ == "__main__":
    asyncio.run(login())
