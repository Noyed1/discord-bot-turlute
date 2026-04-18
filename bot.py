import discord
import asyncio
import os
from config import (
    BOT_TOKEN, ARCHIVE_CHANNEL_ID, CHANNELS_TO_SCAN,
    TARGET_EMOJI, MIN_REACTIONS, ARCHIVE_LOG_FILE
)

# ============================================================
#  Chargement des messages déjà archivés (anti-doublons)
# ============================================================
def load_archived_ids():
    if not os.path.exists(ARCHIVE_LOG_FILE):
        return set()
    with open(ARCHIVE_LOG_FILE, "r") as f:
        return set(line.strip() for line in f.readlines())

def save_archived_id(message_id):
    with open(ARCHIVE_LOG_FILE, "a") as f:
        f.write(f"{message_id}\n")

# ============================================================
#  Vérification des réactions
# ============================================================
def get_target_reaction_count(message):
    for reaction in message.reactions:
        emoji = reaction.emoji
        # Gère les emojis unicode (⭐) et les emojis custom Discord
        if isinstance(emoji, str):
            if emoji == TARGET_EMOJI:
                return reaction.count
        else:
            if emoji.name == TARGET_EMOJI:
                return reaction.count
    return 0

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

    # Si le message contient une image
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
    print(f"🔍 Début du scan...")

    archived_ids = load_archived_ids()
    archive_channel = client.get_channel(ARCHIVE_CHANNEL_ID)

    if not archive_channel:
        print("❌ Channel d'archive introuvable. Vérifie ARCHIVE_CHANNEL_ID dans config.py")
        await client.close()
        return

    total_archived = 0

    for channel_id in CHANNELS_TO_SCAN:
        channel = client.get_channel(channel_id)
        if not channel:
            print(f"⚠️  Channel {channel_id} introuvable, skipped.")
            continue

        print(f"📖 Scan de #{channel.name}...")
        count = 0

        scanned = 0
        async for message in channel.history(limit=None, oldest_first=True):
            scanned += 1
            if scanned % 100 == 0:
                print(f"   ... {scanned} messages scannés")
            msg_id = str(message.id)

            # Déjà archivé ?
            if msg_id in archived_ids:
                continue

            reaction_count = get_target_reaction_count(message)

            if reaction_count >= MIN_REACTIONS:
                embed = build_archive_embed(message, reaction_count)
                await archive_channel.send(embed=embed)
                save_archived_id(msg_id)
                archived_ids.add(msg_id)
                count += 1
                total_archived += 1
                await asyncio.sleep(1)  # évite le rate limit Discord

        print(f"   ✓ {count} messages archivés depuis #{channel.name}")

    print(f"\n🏁 Terminé ! {total_archived} messages archivés au total.")
    await client.close()

client.run(BOT_TOKEN)
