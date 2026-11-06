import asyncio
import json
import os
import re

from telethon import TelegramClient
from telethon.errors import (
    ChannelPrivateError,
    FloodWaitError,
    InviteHashExpiredError,
    InviteHashInvalidError,
)

from telethon.tl.functions.messages import CheckChatInviteRequest


# ==========================================
# CONFIGURATION
# ==========================================

API_ID = 00000000  # Replace with your API ID
API_HASH = '000000000000'  # Replace with your API HASH

CHANNEL_LINK = 'https://t.me/+AbCdEfGhIjKl'

OUTPUT_JSON = 'posts.json'
DOWNLOAD_DIR = 'downloads'
SESSION_NAME = 'tg_session'

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# ==========================================
# HELPERS
# ==========================================

def extract_invite_hash(link: str):
    """Extract private channel invite hash."""

    if not link:
        return None

    match = re.search(
        r'(?:t\.me/\+|t\.me/joinchat/|tg://join\?invite=)([\w-]+)',
        link,
        flags=re.IGNORECASE,
    )

    return match.group(1) if match else None


def normalize_public_link(link: str) -> str:
    """Convert public Telegram link into username."""

    if not link:
        return link

    if re.match(
        r'^(?:https?://)?(?:www\.)?t\.me/',
        link,
        flags=re.IGNORECASE,
    ):
        match = re.search(
            r't\.me/(?:s/)?([^/?#]+)',
            link,
            flags=re.IGNORECASE,
        )

        if match:
            return match.group(1)

    return link.lstrip('@')


async def resolve_channel(client, link: str):
    """Resolve public or already joined private channel."""

    invite_hash = extract_invite_hash(link)

    if invite_hash:
        check = await client(CheckChatInviteRequest(invite_hash))

        chat = getattr(check, 'chat', None)

        if chat is not None:
            return await client.get_entity(chat)

        raise ValueError(
            "You are not a participant or channel entity is unavailable."
        )

    return await client.get_entity(normalize_public_link(link))


# ==========================================
# MEDIA DOWNLOAD
# ==========================================

async def download_message_media(client, message):

    media_path = None
    media_type = None
    media_error = None

    if not message.media:
        return media_path, media_type, media_error

    # Identify media type

    if message.photo:
        media_type = 'photo'

    elif message.video_note:
        # Ignore Telegram video circles
        return None, None, None

    elif message.voice:
        media_type = 'voice'

    elif message.video:
        media_type = 'video'

    else:
        # Ignore GIFs, documents, audio files, etc.
        return None, None, None

    file_path = os.path.join(
        DOWNLOAD_DIR,
        f"msg_{message.id}"
    )

    try:
        media_path = await client.download_media(
            message,
            file=file_path
        )

    except FloodWaitError as e:
        print(
            f"\n[Rate limit] Waiting {e.seconds} seconds "
            f"for message {message.id}..."
        )

        await asyncio.sleep(e.seconds + 1)

        try:
            media_path = await client.download_media(
                message,
                file=file_path
            )

        except Exception as retry_error:
            media_error = str(retry_error)

    except Exception as e:
        media_error = str(e)

    if media_error:
        print(
            f"\n[Warning] Failed to download "
            f"{media_type} for message {message.id}: {media_error}"
        )

    return media_path, media_type, media_error


# ==========================================
# MAIN
# ==========================================

async def main():

    print("Connecting to Telegram...")

    async with TelegramClient(
        SESSION_NAME,
        API_ID,
        API_HASH
    ) as client:

        print("Successfully authorized!")
        print("Resolving target channel...")

        try:

            channel = await resolve_channel(
                client,
                CHANNEL_LINK
            )

            print(
                f"Resolved channel: "
                f"{getattr(channel, 'title', CHANNEL_LINK)!r}"
            )

            print("Fetching posts...\n")

            messages_count = 0
            downloaded_count = 0
            failed_count = 0
            skipped_count = 0

            with open(
                OUTPUT_JSON,
                'w',
                encoding='utf-8'
            ) as f:

                async for message in client.iter_messages(
                    channel,
                    reverse=True
                ):

                    media_path, media_type, media_error = (
                        await download_message_media(
                            client,
                            message
                        )
                    )

                    if media_path:
                        downloaded_count += 1

                    if media_error:
                        failed_count += 1

                    if message.video_note:
                        skipped_count += 1

                    post_data = {
                        'id': message.id,
                        'date': (
                            message.date.isoformat()
                            if message.date else None
                        ),
                        'text': message.text or '',
                        'views': message.views or 0,
                        'forwards': message.forwards or 0,
                        'grouped_id': message.grouped_id,
                        'media_type': media_type,
                        'file_path': media_path,
                        'media_error': media_error,
                    }

                    f.write(
                        json.dumps(
                            post_data,
                            ensure_ascii=False
                        ) + '\n'
                    )

                    messages_count += 1

                    if messages_count % 100 == 0:
                        print(
                            f"Processed {messages_count} posts | "
                            f"Downloaded media: {downloaded_count} | "
                            f"Failed: {failed_count}"
                        )

            print("\n========== EXPORT COMPLETE ==========")

            print(f"Total posts: {messages_count}")
            print(f"Downloaded media: {downloaded_count}")
            print(f"Failed downloads: {failed_count}")
            print(f"Skipped video circles: {skipped_count}")

            print(f"\nJSON saved to: {OUTPUT_JSON}")

            print(
                f"Media saved to: "
                f"{os.path.abspath(DOWNLOAD_DIR)}/"
            )

        except InviteHashExpiredError:
            print("Error: Invite link has expired.")

        except InviteHashInvalidError:
            print("Error: Invalid invite link.")

        except ChannelPrivateError:
            print("Error: Channel is private or inaccessible.")

        except ValueError as e:
            print(f"Error: {e}")

        except Exception as e:
            print(f"Unexpected error: {e}")


# ==========================================
# ENTRY POINT
# ==========================================

if __name__ == '__main__':
    asyncio.run(main())
