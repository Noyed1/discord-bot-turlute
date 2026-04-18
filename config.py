import os
# ============================================================
#  CONFIGURATION — modifie uniquement ce fichier
# ============================================================

# Token de ton bot Discord (récupéré sur discord.com/developers)
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# ID du channel où les messages archivés seront postés
ARCHIVE_CHANNEL_ID = 1492126899143577651

# IDs des channels à scanner
CHANNELS_TO_SCAN = [1187566701290729626]

# Emoji spécifique à tracker (ex: "⭐", "🔥", ou un emoji custom "nom_emoji")
TARGET_EMOJI = "joie"

# Nombre minimum de cet emoji pour archiver le message
MIN_REACTIONS = 1

# Pour éviter les doublons : le bot garde en mémoire les messages déjà archivés
ARCHIVE_LOG_FILE = "archived_messages.txt"
