import discord
import os
import asyncio
import re
from datetime import datetime, timezone
from config import (
    ARCHIVE_CHANNEL_ID, CHANNELS_TO_SCAN,
    TARGET_EMOJI, MIN_REACTIONS, ARCHIVE_LOG_FILE
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

RIP_CHANNEL_ID = 1187566701290729626
INACTIVITY_MINUTES = 60
QUIET_START = 2
QUIET_END = 9
MIN_WORDS_PALU = 50

def load_archived_ids():
    raw = os.environ.get("ARCHIVED_IDS", "")
    if not raw:
        return set()
    return set(raw.split(","))

archived_ids = load_archived_ids()
last_message_time = None
rip_sent = False
handled_messages = set()

def build_archive_embed(message, reaction_count):
    embed = discord.Embed(
        description=message.content or "*[pas de texte]*",
        color=0xFFD700,
        timestamp=message.created_at
    )
    embed.set_author(
        name=message.author.display_name,
        icon_url=message.author.display_avatar.url
    )
    embed.add_field(
        name="Source",
        value=f"[Voir le message]({message.jump_url}) dans <#{message.channel.id}>",
        inline=False
    )
    embed.set_footer(text=f"{TARGET_EMOJI} {reaction_count} réactions")

    if message.attachments:
        for attachment in message.attachments:
            if attachment.content_type and attachment.content_type.startswith("image/"):
                embed.set_image(url=attachment.url)
                break

    return embed

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True
intents.guilds = True

client = discord.Client(intents=intents)

async def check_inactivity():
    global last_message_time, rip_sent
    await client.wait_until_ready()

    rip_channel = client.get_channel(RIP_CHANNEL_ID)

    try:
        async for msg in rip_channel.history(limit=1):
            last_message_time = msg.created_at
    except:
        last_message_time = datetime.now(timezone.utc)

    while not client.is_closed():
        await asyncio.sleep(60)

        now = datetime.now(timezone.utc)
        local_hour = (now.hour + 2) % 24

        if QUIET_START <= local_hour < QUIET_END:
            rip_sent = False
            continue

        if last_message_time is None:
            continue

        minutes_inactive = (now - last_message_time).total_seconds() / 60

        if minutes_inactive >= INACTIVITY_MINUTES and not rip_sent:
            try:
                guild = rip_channel.guild
                rip_emoji = discord.utils.get(guild.emojis, name="RIP")
                if rip_emoji:
                    await rip_channel.send(str(rip_emoji))
                else:
                    await rip_channel.send("RIP")
                rip_sent = True
                print(f"💀 RIP envoyé dans #{rip_channel.name}")
            except Exception as e:
                print(f"Erreur envoi RIP : {e}")
        elif minutes_inactive < INACTIVITY_MINUTES:
            rip_sent = False

@client.event
async def on_ready():
    print(f"✅ Connecté en tant que {client.user}")
    print(f"👀 En écoute des nouvelles réactions...")
    print(f"💀 Surveillance inactivité activée")
    client.loop.create_task(check_inactivity())

@client.event
async def on_message(message):
    global last_message_time, rip_sent

    if message.author.bot:
        return

    if message.channel.id == RIP_CHANNEL_ID:
        last_message_time = message.created_at
        rip_sent = False

        if message.id in handled_messages:
            return
        handled_messages.add(message.id)

        content = message.content
        content_lower = content.lower()

        # Fuck
        if re.search(r'\bfuck balu\b', content_lower):
            await message.channel.send("fuck balu")
            print(f"🤬 fuck balu envoyé pour {message.author.display_name}")

        # 50 mots → palu
        word_count = len(content.split())
        if word_count >= MIN_WORDS_PALU:
            guild = message.channel.guild
            check_emoji = discord.utils.get(guild.emojis, name="check")
            if check_emoji:
                await message.channel.send(f"palu {check_emoji}")
            else:
                await message.channel.send("palu ✅")
            print(f"📝 Palu envoyé pour {message.author.display_name} ({word_count} mots)")

@client.event
async def on_reaction_add(reaction, user):
    message = reaction.message

    if message.channel.id not in CHANNELS_TO_SCAN:
        return

    emoji = reaction.emoji
    if isinstance(emoji, str):
        if emoji != TARGET_EMOJI:
            return
    else:
        if emoji.name != TARGET_EMOJI:
            return

    msg_id = str(message.id)
    if msg_id in archived_ids:
        return

    count = reaction.count
    if count < MIN_REACTIONS:
        return

    archive_channel = client.get_channel(ARCHIVE_CHANNEL_ID)
    if not archive_channel:
        print("❌ Channel d'archive introuvable.")
        return

    embed = build_archive_embed(message, count)
    await archive_channel.send(embed=embed)
    archived_ids.add(msg_id)
    print(f"⭐ Archivé : message de {message.author.display_name} dans #{message.channel.name} ({count} réactions)")

client.run(BOT_TOKEN)
