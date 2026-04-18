import discord
import os
from config import (
    ARCHIVE_CHANNEL_ID, CHANNELS_TO_SCAN,
    TARGET_EMOJI, MIN_REACTIONS, ARCHIVE_LOG_FILE
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

# ============================================================
#  Anti-doublons via variable d'environnement
# ============================================================
def load_archived_ids():
    raw = os.environ.get("ARCHIVED_IDS", "")
    if not raw:
        return set()
    return set(raw.split(","))

archived_ids = load_archived_ids()

# ============================================================
#  Formatage du message d'archive
# ============================================================
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

# ============================================================
#  Bot principal
# ============================================================
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ Connecté en tant que {client.user}")
    print(f"👀 En écoute des nouvelles réactions...")

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
