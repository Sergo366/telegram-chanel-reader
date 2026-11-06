import asyncio
import os
import re

from telethon import TelegramClient
from telethon.errors import (
    ChannelPrivateError,
    InviteHashExpiredError,
    InviteHashInvalidError,
    UserAlreadyParticipantError,
)
from telethon.tl.functions.messages import (
    CheckChatInviteRequest,
    ImportChatInviteRequest,
)

# Insert your api_id and api_hash here.
# Note: API_ID must be an integer, and API_HASH must be a string
API_ID = 00000000  # REPLACE WITH YOUR API_ID
API_HASH = '000000000000'  # REPLACE WITH YOUR API_HASH

# Target channel. Can be one of:
#   - A public username:         '@channel_name'
#   - A public channel link:     'https://t.me/channel_name'
#   - A private invite link:     'https://t.me/+AbCdEfGhIjKl'
#   - A legacy invite link:      'https://t.me/joinchat/AbCdEfGhIjKl'
#   - A tg:// invite link:       'tg://join?invite=AbCdEfGhIjKl'
CHANNEL_LINK = 'https://t.me/+AbCdEfGhIjKl'  # REPLACE WITH TARGET CHANNEL

# Output file name for saving posts
OUTPUT_FILE = 'posts.txt'

# Session file name to save authorization, preventing code prompt on every run
SESSION_NAME = 'tg_session'


def extract_invite_hash(link: str):
    """Return the invite hash if `link` is a private invite link, else None."""
    if not link:
        return None
    match = re.search(
        r'(?:t\.me/\+|t\.me/joinchat/|tg://join\?invite=)([\w-]+)',
        link,
        flags=re.IGNORECASE,
    )
    return match.group(1) if match else None


def normalize_public_link(link: str) -> str:
    """Convert a public t.me link into a plain username for get_entity()."""
    if not link:
        return link
    if re.match(r'^(?:https?://)?(?:www\.)?t\.me/', link, flags=re.IGNORECASE):
        match = re.search(r't\.me/(?:s/)?([^/?#]+)', link, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return link


async def resolve_channel(client, link: str):
    """Resolve a channel/chat entity from a username, public link, or invite link."""
    invite_hash = extract_invite_hash(link)

    if invite_hash:
        # If we're already a member, grab the entity without side effects.
        try:
            check = await client(CheckChatInviteRequest(invite_hash))
            # ChatInviteAlready has .chat; ChatInvitePeek is a preview for non-members.
            chat = getattr(check, 'chat', None)
            if chat is not None:
                return chat
        except (InviteHashExpiredError, InviteHashInvalidError):
            # Let the join attempt below surface a clearer error.
            pass

        # Not a member yet (or we couldn't check) - join via invite.
        try:
            result = await client(ImportChatInviteRequest(invite_hash))
        except UserAlreadyParticipantError:
            # Race or stale session state: re-check to fetch the entity.
            check = await client(CheckChatInviteRequest(invite_hash))
            chat = getattr(check, 'chat', None)
            if chat is None:
                raise ValueError(
                    "Already a participant but could not resolve the chat entity."
                )
            return chat

        if not result.chats:
            raise ValueError("Invite import succeeded but returned no chats.")
        return result.chats[0]

    # Public username or public link.
    return await client.get_entity(normalize_public_link(link))


async def main():
    print("Connecting to Telegram...")
    # Create the client. On first run, it will ask for your phone number and Telegram code.
    async with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
        print("Successfully authorized! Resolving target channel...")

        try:
            channel = await resolve_channel(client, CHANNEL_LINK)
            print(f"Resolved channel: {getattr(channel, 'title', CHANNEL_LINK)!r}. Fetching posts...")

            messages_count = 0

            # Open file for writing. encoding='utf-8' is important for emojis and non-latin characters
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                # Iterate over all messages in the channel.
                # reverse=True means chronological order (oldest to newest)
                # Remove reverse=True to save from newest to oldest.
                async for message in client.iter_messages(channel, reverse=True):
                    # Check if the message has text content
                    if message.text:
                        f.write(message.text + '\n')
                        # Add a separator between posts for readability
                        f.write('\n' + '=' * 50 + '\n\n')
                        messages_count += 1

                        if messages_count % 100 == 0:
                            print(f"Downloaded {messages_count} posts...")

            print(f"Done! Successfully saved {messages_count} posts to {OUTPUT_FILE}.")

        except InviteHashExpiredError:
            print(f"Error: The invite link for {CHANNEL_LINK!r} has expired.")
        except InviteHashInvalidError:
            print(f"Error: The invite link for {CHANNEL_LINK!r} is invalid.")
        except UserAlreadyParticipantError:
            print(f"Error: Already a participant of {CHANNEL_LINK!r} but entity lookup failed.")
        except ChannelPrivateError:
            print(f"Error: Channel {CHANNEL_LINK!r} is private and cannot be accessed.")
        except ValueError as e:
            print(f"Error: Channel {CHANNEL_LINK!r} not found or inaccessible ({e}).")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


if __name__ == '__main__':
    asyncio.run(main())
