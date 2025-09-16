import discord
from datetime import datetime
import os
from dotenv import load_dotenv

class MyClient(discord.Client):
    async def on_ready(self):
        print('✅ Logged on as {0}!'.format(self.user))

    async def on_message(self, message):
        log_channel = discord.utils.get(message.guild.text_channels, name='bot-log')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        guest_role = discord.utils.get(message.guild.roles, name='guest')


        if message.author == self.user:
            return
        
        # test active
        if message.content.startswith('>>test'):
            await message.channel.send('Hello `{0}`, `{1}` is active and ready to make your life easier!'.format(message.author, self.user))

            try:
                file_path = 'images/robojo.png'
                if os.path.exists(file_path):
                    await message.channel.send(file=discord.File(file_path))
            except Exception as e:
                await message.channel.send(f"⚠️ I can't seem to find a picture of myself to send")

            return

        # unarchive channel
        if message.content.startswith('>>unarchive'):
            try:
                await message.delete()
                await message.channel.edit(category=None, reason='unarchived by bot')
                await message.channel.edit(position=0)

                overwrite = message.channel.overwrites_for(message.guild.default_role)
                overwrite.view_channel = True
                overwrite.send_messages = True

                await message.channel.set_permissions(message.guild.default_role, overwrite=overwrite)

                await message.channel.send('```css\n[ ============ channel unarchived ============ ]```')

                log_message = f"```css\n[ Channel #{message.channel.name} was unarchived by {message.author} at {timestamp} ]\n```"
                await log_channel.send(log_message)
            except Exception as e:
                await message.channel.send('⚠️ Unexpected error occurred while unarchiving this channel')
            
            return

        # archive channel
        if message.content.startswith('>>archive'):
            try:
                await message.delete()
            except discord.Forbidden:
                await message.channel.send('⚠️ `{0}` needs permission to delete messages'.format(self.user))

            await message.channel.send('```css\n[ ========== This channel is now archived ========== ]```')

            archive_category = discord.utils.get(message.guild.categories, name='archive')
            if archive_category is None:
                await message.channel.send("⚠️ `{0}` could not find an `archive` category".format(self.user))
                return
            
            try:
                await message.channel.edit(category=archive_category, sync_permissions=True, reason='archived by a bot')
            except discord.Forbidden:
                await message.channel.send('⚠️ `{0}` needs permission to move channels'.format(self.user))

            return
        
        # delete channel
        if message.content.startswith('>>del'):
            channel_to_delete = message.channel
            try:
                await channel_to_delete.delete(reason='deleted by a bot')

                if log_channel:
                    log_message = f"```css\n[ Channel #{channel_to_delete.name} was deleted by {message.author} at {timestamp} ]\n```"
                    await log_channel.send(log_message)
            except discord.Forbidden:
                await message.channel.send('⚠️ `{0}` needs permission to delete channels'.format(self.user))

            return
                
        # purge messages/images/etc.
        if message.content.startswith('>>purge'):
            parts = message.content.split()

            if len(parts) < 2 or not parts[1].isdigit():
                await message.channel.send('⚠️ Proper usage: `>>purge <n>`')
                return
            
            n = int(parts[1])

            try:
                deleted = await message.channel.purge(limit=n+1)

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
                    
                    if n == 1:
                        header = f"[ {n} message was purged from #{message.channel.name} at {timestamp} ]"
                    else:
                        header = f"[ {n} messages were purged from #{message.channel.name} at {timestamp} ]"
                    log_message = "```css\n" + header + '``````' + '\n'.join(log_lines) + "\n```"

                    await log_channel.send(log_message)
            except discord.Forbidden:
                await message.channel.send('⚠️ `{0}` needs permission to purge messages'.format(self.user))
        
            return
        
        # view guestlist
        if message.content.startswith('>>guestlist'):
            guest_members = guest_role.members
            if not guest_members:
                await message.channel.send(f"No members currently have the `{guest_role}` role")
                return
            
            guest_lines = [f"- {member} ({member.id})" for member in guest_members]
            header = f"[ Guest List in {message.guild.name} at {timestamp} ]"
            guest_message = "```css\n" + header + "\n``````" + '\n'.join(guest_lines) + '\n```'

            await message.channel.send(guest_message)

            return
    
        # dub guest
        if message.content.startswith('>>guest'):
            parts = message.content.split(maxsplit=1)
            if len(parts) < 2:
                await message.channel.send('⚠️ Proper usage: `>>guest <@user>`')
                return
            
            if message.mentions:
                member = message.mentions[0]
            else:
                await message.channel.send('⚠️ Must mention a user')
                return
            
            try:
                await member.add_roles(guest_role, reason=f"Guest added by {message.author}")
                await message.channel.send(f'✅ `{guest_role}` was assigned to `{member}`')
                log_details = [
                    f"Time: {timestamp}",
                    f"Actor: {message.author} ({message.author.id})",
                    f"Target: {member} ({member.id})"
                ]
                log_message = '```css\n[ Guest Granted ]``````' + '\n'.join(log_details) + '\n```'
                await log_channel.send(log_message)
            except discord.Forbidden:
                await message.channel.send("⚠️ `{0}` needs permission to assign roles".format(self.user))

            return
        
        # remove guest
        if message.content.startswith('>>unguest'):
            parts = message.content.split(maxsplit=1)
            if len(parts) < 2:
                await message.channel.send('⚠️ Proper usage: `>>unguest <@user>`')
                return
            
            if message.mentions:
                member = message.mentions[0]
            else:
                await message.channel.send('⚠️ Must mention a user')
                return
            
            if guest_role not in member.roles:
                await message.channel.send(f"`{member}` does not have the `{guest_role}` role")
                return

            try:
                await member.remove_roles(guest_role, reason=f'Guest removed by {message.author}')
                await message.channel.send(f'✅ `{guest_role}` was removed from `{member}`')

                log_details = [
                    f"Time: {timestamp}",
                    f"Actor: {message.author} ({message.author.id})",
                    f"Target: {member} ({member.id})"
                ]
                log_message = '```css\n[ Guest Removed ]``````' + '\n'.join(log_details) + '\n```'
                await log_channel.send(log_message)
            except discord.Forbidden:
                await message.channel.send("⚠️ `{0}` needs permission to remove roles".format(self.user))

            return
        
        # kick guests
        if message.content.startswith('>>kickguests'):
            guests = list(guest_role.members)

            if not guests:
                await message.channel.send(f"No members currently have the `{guest_role}` role")
                return
            
            kicked = []
            failed = []

            for member in guests:
                if member == self.user or member == message.guild.owner:
                    continue
            
                try:
                    await member.kick(reason=f"Kicked by {message.author} via >>kickguests")
                    kicked.append(f"{member} ({member.id})")
                except discord.Forbidden:
                    failed.append(f"{member} ({member.id}) -- insufficient permissions")

            if kicked:
                n = len(kicked)
                if n == 1:
                    header = f"[ {n} guest was kicked at {timestamp} ]"
                else:
                    header = f"[ {len(kicked)} guest(s) were kicked at {timestamp} ]"
                log_message = '```css\n' + header + '\n``````' + '\n'.join(f"- {m}" for m in kicked) + '\n```'

                await message.channel.send(log_message)
            else:
                await message.channel.send(f"No members were kicked")

            log_lines = [
                f"Time: {timestamp}",
                f"Actor: {message.author} ({message.author.id})",
                f"Kicked: {len(kicked)}",
                f"Failed to kick: {len(failed)}"
            ]

            log_message = '```css\n' + '[ Guests Kicked ]' + '\n``````' + '\n'.join(log_lines) + '\n```'
            await log_channel.send(log_message)

            if kicked:
                kicked_message = '```css\n' + '[ ---- Kicked ---- ]' + '\n``````' + '\n'.join(f"- {m}" for m in kicked) + '\n```'
                await log_channel.send(kicked_message)
            if failed:
                failed_message = '```css\n' + '[ ---- Failed to Kick ---- ]' + '\n``````' + '\n'.join(f"- {m}" for m in failed) + '\n```'
                await log_channel.send(failed_message)
            
            return

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

client = MyClient(intents=intents)
load_dotenv()
client.run(os.getenv('DISCORD_TOKEN'))