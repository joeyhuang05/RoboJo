import discord
from datetime import datetime
import os
from dotenv import load_dotenv

class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    async def on_message(self, message):
        if message.author == self.user:
            return
        
        # test active
        if message.content.startswith('>>test'):
            await message.channel.send('`{0}` is active and ready to make your life easier!'.format(self.user))

        # archive channel
        if message.content.startswith('>>archive'):
            try:
                await message.delete()
            except discord.Forbidden:
                await message.channel.send('⚠️ `{0}` needs permission to delete messages'.format(self.user))

            await message.channel.send('```============= This channel is now archived =============```')

            archive_category = discord.utils.get(message.guild.categories, name='archive')
            if archive_category is None:
                await message.channel.send("⚠️ `{0}` could not find an `archive` category".format(self.user))
                return
            
            try:
                await message.channel.edit(category=archive_category, sync_permissions=True, reason='archived by a bot')
            except discord.Forbidden:
                await message.channel.send('⚠️ `{0}` needs permission to move channels'.format(self.user))
        
        # delete channel
        if message.content.startswith('>>del'):
            try:
                await message.channel.delete(reason='deleted by a bot')
            except discord.Forbidden:
                await message.channel.send('⚠️ `{0}` needs permission to delete channels'.format(self.user))
                
        # purge messages/images/etc.
        if message.content.startswith('>>purge'):
            parts = message.content.split()

            if len(parts) < 2 or not parts[1].isdigit():
                await message.channel.send('⚠️ Proper usage: `>>purge {number}`')
                return
            
            n = int(parts[1])

            try:
                deleted = await message.channel.purge(limit=n+1)

                log_channel = discord.utils.get(message.guild.text_channels, name='bot-log')
                if log_channel:
                    log_lines = []
                    for msg in reversed(deleted[1:]):
                        if msg.content:
                            log_lines.append(f"{msg.author}: {msg.content}")

                        for attachment in msg.attachments:
                            content_type = attachment.content_type or ''
                            
                            if content_type.startswith('image/') or content_type.startswith('video/'):
                                log_lines.append(f"{msg.author}: [image / video]")
                            else:
                                filename = attachment.filename.lower()

                                if any(filename.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv']):
                                    log_lines.append(f"{msg.author}: [image / video]")
                    
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    header = f"=== {len(deleted)-1} messages were deleted at {timestamp} ==="
                    log_message = "```\n" + header + '\n' + '\n'.join(log_lines) + "\n```"

                    await log_channel.send(log_message)
            except discord.Forbidden:
                await message.channel.send('⚠️ `{0}` needs permission to purge messages'.format(self.user))


intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

client = MyClient(intents=intents)
load_dotenv()
client.run(os.getenv('DISCORD_TOKEN'))