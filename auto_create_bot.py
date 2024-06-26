import argparse
import json
import csv
import os
from telethon import TelegramClient, events
from telethon.tl.functions.photos import UploadProfilePhotoRequest
from telethon.tl.functions.bots import SetBotInfoRequest
import re
import string
import asyncio
import socks

api_id = 26120312
api_hash = "a122106d78462db8ab24b1028f3b64b0"

async def create_bot(client, bot):
    bot_token = None
    retry_time = None
    token_retrieved = asyncio.Event()

    def extract_retry_time(message):
        match = re.search(r"Please try again in (\d+) seconds", message)
        if match:
            return int(match.group(1))
        else:
            return None

    async def handler(event):
        nonlocal bot_token, token_retrieved, retry_time
        message = event.message.message

        if "Alright, a new bot. How are we going to call it? Please choose a name for your bot." in message:
            await asyncio.sleep(2)
            response_message = await client.send_message('BotFather', bot['name'])
        elif "Good. Now let's choose a username for your bot." in message:
            await asyncio.sleep(2)
            response_message = await client.send_message('BotFather', bot['username'])
        elif "Sorry, too many attempts." in message:
            retry_time = extract_retry_time(message)
            if retry_time:
                token_retrieved.set()
        elif "Done! Congratulations on your new bot." in message:
            try:
                # Find the line with the token
                lines = message.splitlines()
                for line in lines:
                    if line.startswith(
                            "Use this token to access the HTTP API:"):
                        bot_token = lines[lines.index(line) + 1].strip()
                        token_retrieved.set()  # Signal that bot_token has been retrieved
            except IndexError:
                print("Error: Failed to extract bot token from message:", message)
                token_retrieved.set()  # Signal that bot_token has been retrieved
        elif "Sorry, this username":
            print(f"Error: INVALID username {bot['username']}")
            bot_token = 'INVALID'
            token_retrieved.set()

    # Register the handler function for BotFather messages
    client.add_event_handler(
        handler, events.NewMessage(
            from_users='BotFather'))

    await client.send_message('BotFather', '/newbot')
    await token_retrieved.wait()

    # Must remove handler to avoid interaction chaos
    client.remove_event_handler(
        handler, events.NewMessage(
            from_users='BotFather'))

    return bot_token, retry_time

async def set_privacy(client, bot):
    set_done = asyncio.Event()
    async def handler(event):
        if "Choose a bot" in event.raw_text:
            await client.send_message('BotFather', '@'+bot['username'])
        elif "Current status is: ENABLED" in event.raw_text:
            await client.send_message('BotFather', 'Disable')
            print(f"Group privacy disabled for {bot['username']}")
            set_done.set()
        else:
            print(f"Group privacy already disabled {bot['username']}")
            set_done.set()

    # Register the handler function for BotFather messages
    client.add_event_handler(
        handler, events.NewMessage(
            from_users='BotFather'))

    await client.send_message('BotFather', '/setprivacy')
    await set_done.wait()

    # Must remove handler to avoid interaction chaos
    client.remove_event_handler(
        handler, events.NewMessage(
            from_users='BotFather'))

async def set_bot_profile(client, bot):
    avatar_dir = './photos'
    avatar_image = bot['photo']
    avatar_path = os.path.join(avatar_dir, avatar_image)

    try:
        photo = await client.upload_file(avatar_path, part_size_kb=512)
        await client(UploadProfilePhotoRequest(bot=bot['username'], file=photo))

        await client(SetBotInfoRequest(
            lang_code='en',
            bot=bot['username'],
            name=bot['name'],
            about=bot['about']
        ))
        print(f"Profile set for {bot['username']}")
    except Exception as e:
        print(f"Error set profile for {bot['username']}: {e}")

def write_bot_token(phone, bot_token):
    with open('output.csv', 'a') as file:
        file.write(f"Account: {phone} bot token: {bot_token}\n")


async def list_my_bots(client):
    bots = []
    try:
        # Fetch the list of bots using BotFather's /mybots command
        await client.send_message('BotFather', '/mybots')
        response = await client.get_messages('BotFather', limit=1)

        if response and response[0].text.startswith(
                "Choose a bot from the list below:"):
            # Extract buttons from the reply markup
            reply_markup = response[0].reply_markup
            if reply_markup:
                for row in reply_markup.rows:
                    for button in row.buttons:
                        if button.text.startswith('@'):
                            bot_username = button.text.strip('@')
                            bots.append(bot_username)
                            print(f'Found bot: {bot_username}')

            print(f'Listed {len(bots)} bots')
        else:
            print('Failed to list bots: BotFather did not respond correctly')
    except Exception as e:
        print(f'Error listing bots: {e}')
    return bots


async def delete_bot(client, bot_username):
    try:
        # Send delete command to BotFather for the specific bot
        await client.send_message('BotFather', f'/deletebot')
        response = await client.get_messages('BotFather', limit=1)
        if response and f"Choose a bot to delete." in response[0].text:
            await client.send_message('BotFather', f'@{bot_username}')
            await client.send_message('BotFather', 'Yes, I am totally sure.')
            print(f'Bot {bot_username} successfully deleted')
        else:
            print(f'Error: Bot {bot_username} not found or cannot be deleted')
    except Exception as e:
        print(f'Error deleting bot {bot_username}: {e}')


async def delete_all_bots(client):
    bot_usernames = await list_my_bots(client)
    for bot_username in bot_usernames:
        await delete_bot(client, bot_username)


async def operate_bots_for_account(operation, interval, client, phone, bots):
    if operation == 'create':
        while bots:
            # Check if the number of existing bots is less than the maximum
            bot = bots[0]
            bot_token, retry_time = await create_bot(client, bot)
            if bot_token:
                if bot_token != 'INVALID':
                    print(f"---------created bot {bot} for account {phone}---------")
                    write_bot_token(phone, bot_token)  # Write Bot Token to file
                    await set_bot_profile(client, bot)  # Set bot profile
                    await set_privacy(client, bot)  # Set bot profile
                bots.remove(bot)
                if bots:
                    # for next create delay for some time
                    print(f"Waiting for {interval} seconds to create next bot for {phone}...")
                    await asyncio.sleep(interval)
                else:
                    print(f"Create bot done for {phone}")
            elif retry_time:
                if retry_time < 80000:
                    print(f"Waiting for {retry_time} seconds to retry create bot for {phone}...")
                    await asyncio.sleep(retry_time)  # delay based on response
                else:
                    print(f"Please retry tomorrow to create bot for {phone}...")
                    break

    elif operation == 'delete':
        await delete_all_bots(client)

    await client.disconnect()


async def create_clients(accounts, proxy):
    # create client has to in sequence as need verification interaction
    clients = {}
    for phone, _ in accounts.items():
        session_name = os.path.join('sessions', f"{phone}.session")
        client = TelegramClient(session_name, api_id, api_hash, proxy=proxy) if proxy else TelegramClient(session_name, api_id, api_hash)
        clients[phone] = client
        print(f"Verification for account {phone}......")
        await client.start(phone=phone)

    return clients

def parse_proxy(proxy_arg):
    if proxy_arg:
        parts = proxy_arg.split(':')
        if len(parts) != 2:
            raise ValueError("Proxy format is incorrect. Use ip:port")
        host = parts[0]
        port = int(parts[1])

        return (socks.HTTP, host, port)
    return None

async def main(operation, interval, proxy_arg):
    accounts = {}
    with open('input.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            phone = row['phone']
            bot = {
                'username': row['bot_username'],
                'name': row['bot_name'],
                'photo': row['bot_photo'],
                'about': row['bot_about']
            }

            # Check if the phone number is already a key in the dictionary
            if phone in accounts:
                accounts[phone].append(bot)
            else:
                accounts[phone] = [bot]

    proxy = parse_proxy(proxy_arg)

    clients = await create_clients(accounts, proxy)
    tasks = [
        operate_bots_for_account(
            operation,
            interval,
            client,
            phone,
            accounts[phone]) for phone,
        client in clients.items()]
    await asyncio.gather(*tasks)


# Run the main function
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create or delete Telegram bots')
    parser.add_argument('operation', choices=['create', 'delete'], help='Operation to perform: create or delete')
    parser.add_argument('--interval', type=int, default=5, help='Interval in seconds (default: 5)')
    parser.add_argument('--proxy', type=str, default=None, help='Proxy server in the format: host:port')
    args = parser.parse_args()
    
    asyncio.run(main(args.operation, args.interval, args.proxy))
