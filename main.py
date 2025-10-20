# MmkAlphaScanner — Quick Scan Bot (No-API Version)

import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# -----------------------
# Chain detection
# -----------------------
def detect_chain(ca: str):
    if ca.startswith("0x"):
        return "BNB/Base"
    elif len(ca) == 44:
        return "SOL"
    else:
        return "Unknown"

# -----------------------
# Generate pre-filled token links
# -----------------------
def generate_links(ca: str, chain: str, full=True):
    links = []

    if chain == "SOL":
        if full:
            links.append([InlineKeyboardButton("SolSniffer", url=f"https://www.solsniffer.com/scanner/{ca}")])
            links.append([InlineKeyboardButton("SolScan", url=f"https://solscan.io/token/{ca}")])
            links.append([InlineKeyboardButton("RugCheck", url=f"https://rugcheck.xyz/tokens/{ca}")])
            links.append([InlineKeyboardButton("Tokensniffer", url=f"https://tokensniffer.com/token/solana/{ca}")])
            links.append([InlineKeyboardButton("Swap on Orca", url=f"https://www.orca.so/?tokenIn=So11111111111111111111111111111111111111112&tokenOut={ca}")])
        else:
            links.append([InlineKeyboardButton("SolScan", url=f"https://solscan.io/token/{ca}")])

    elif chain == "BNB":
        if full:
            links.append([InlineKeyboardButton("BscScan", url=f"https://bscscan.com/token/{ca}")])
            links.append([InlineKeyboardButton("Honeypot", url=f"https://honeypot.is/?address={ca}")])
            links.append([InlineKeyboardButton("Tokensniffer", url=f"https://tokensniffer.com/token/bsc/{ca}")])
            links.append([InlineKeyboardButton("PancakeSwap", url=f"https://pancakeswap.finance/swap?outputCurrency={ca}")])
        else:
            links.append([InlineKeyboardButton("BscScan", url=f"https://bscscan.com/token/{ca}")])

    elif chain == "Base":
        if full:
            links.append([InlineKeyboardButton("BaseScan", url=f"https://basescan.org/token/{ca}")])
            links.append([InlineKeyboardButton("Honeypot", url=f"https://honeypot.is/base?address={ca}")])
            links.append([InlineKeyboardButton("Tokensniffer", url=f"https://tokensniffer.com/token/base/{ca}")])
            links.append([InlineKeyboardButton("Aerodrome", url=f"https://aerodrome.finance/swap?outputCurrency={ca}")])
        else:
            links.append([InlineKeyboardButton("BaseScan", url=f"https://basescan.org/token/{ca}")])

    return links

# -----------------------
# Toggle full/compact links per chat
# -----------------------
toggle_show_full = {}  # chat_id -> True/False

async def toggleshowfull(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    toggle_show_full[chat_id] = not toggle_show_full.get(chat_id, True)
    status = "FULL" if toggle_show_full[chat_id] else "COMPACT"
    await update.message.reply_text(f"✅ Link view toggled to: {status}")

# -----------------------
# /scan command
# -----------------------
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /scan <contract_address>")
        return

    ca = context.args[0].strip()
    chain = detect_chain(ca)
    chat_id = update.message.chat_id
    full = toggle_show_full.get(chat_id, True)

    links = generate_links(ca, chain, full)
    if not links:
        await update.message.reply_text("❌ Unknown chain. Cannot generate links.")
        return

    reply_markup = InlineKeyboardMarkup(links)
    await update.message.reply_text(
        f"🔗 Links for contract: `{ca}`\nChain detected: *{chain}*\nTap a button to open the token page / scanner / swap.",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )

# -----------------------
# /scanmulti command
# -----------------------
async def scanmulti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /scanmulti <CA1>,<CA2>,<CA3>")
        return

    contracts = " ".join(context.args).replace(" ", "").split(",")
    chat_id = update.message.chat_id
    full = toggle_show_full.get(chat_id, True)

    for ca in contracts:
        chain = detect_chain(ca)
        links = generate_links(ca, chain, full)
        if not links:
            await update.message.reply_text(f"❌ Unknown chain for `{ca}`. Skipping.")
            continue
        reply_markup = InlineKeyboardMarkup(links)
        await update.message.reply_text(
            f"🔗 Links for contract: `{ca}`\nChain detected: *{chain}*",
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )

# -----------------------
# /start and /help
# -----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
⚡ Welcome to **MmkAlphaScanner Quick Scan Bot**!

Commands:
🪙 /scan <contract_address> — Single token quick links
⚡ /scanmulti <CA1>,<CA2> — Bulk token links
🔁 /toggleshowfull — Toggle compact/full link view

Features:
- Solana + BNB + Base support
- Opens scanners, block explorers, and swap pages
- Full mode shows all links; compact mode shows main explorer only
"""
    await update.message.reply_text(text, parse_mode="Markdown")

# -----------------------
# Telegram app setup
# -----------------------
app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", start))
app.add_handler(CommandHandler("scan", scan))
app.add_handler(CommandHandler("scanmulti", scanmulti))
app.add_handler(CommandHandler("toggleshowfull", toggleshowfull))

if __name__ == "__main__":
    print("🚀 MmkAlphaScanner Quick Scan Bot is running...")
    app.run_polling()
