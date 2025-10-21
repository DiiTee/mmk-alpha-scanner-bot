# MmkAlphaScanner — Quick Scan Bot (No-API Version)

import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# -----------------------
# Chain detection and normalization
# -----------------------
def normalize_chain(chain_input: str):
    """Normalize chain name from user input"""
    chain_lower = chain_input.lower().strip()
    if chain_lower in ["sol", "solana"]:
        return "SOL"
    elif chain_lower in ["bnb", "bsc", "binance"]:
        return "BNB"
    elif chain_lower in ["base"]:
        return "Base"
    return None

def detect_chain(ca: str):
    """Auto-detect chain from contract address format"""
    ca = ca.strip()
    
    # Solana: 32-44 chars, base58 encoded (no 0x prefix)
    if not ca.startswith("0x") and 32 <= len(ca) <= 44:
        # Check if it's valid base58-like (no 0, O, I, l in base58)
        if all(c in "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz" for c in ca):
            return "SOL"
    
    # EVM chains (BNB, Base, etc): 0x + 40 hex chars
    if ca.startswith("0x") and len(ca) == 42:
        # Default to BNB for now, user can specify if it's Base
        return "BNB"
    
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
    if len(context.args) == 0:
        await update.message.reply_text(
            "Usage:\n• /scan &lt;contract_address&gt;\n• /scan &lt;chain&gt; &lt;contract_address&gt;\n\nChains: SOL, BNB, Base",
            parse_mode="HTML"
        )
        return

    chat_id = update.message.chat_id
    full = toggle_show_full.get(chat_id, True)
    
    # Check if user specified chain explicitly
    if len(context.args) == 2:
        chain = normalize_chain(context.args[0])
        ca = context.args[1].strip()
        if not chain:
            await update.message.reply_text("❌ Invalid chain. Use: SOL, BNB, or Base")
            return
    elif len(context.args) == 1:
        ca = context.args[0].strip()
        chain = detect_chain(ca)
    else:
        await update.message.reply_text(
            "Usage:\n• /scan &lt;contract_address&gt;\n• /scan &lt;chain&gt; &lt;contract_address&gt;\n\nChains: SOL, BNB, Base",
            parse_mode="HTML"
        )
        return

    if chain == "Unknown":
        await update.message.reply_text("❌ Cannot detect chain. Please specify: /scan &lt;chain&gt; &lt;address&gt;", parse_mode="HTML")
        return

    links = generate_links(ca, chain, full)
    if not links:
        await update.message.reply_text("❌ Cannot generate links for this chain.")
        return

    reply_markup = InlineKeyboardMarkup(links)
    await update.message.reply_text(
        f"🔗 Links for contract: <code>{ca}</code>\nChain: <b>{chain}</b>",
        parse_mode="HTML",
        reply_markup=reply_markup,
    )

# -----------------------
# /scanmulti command
# -----------------------
async def scanmulti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage:\n• /scanmulti &lt;CA1&gt;,&lt;CA2&gt;,&lt;CA3&gt;\n• /scanmulti &lt;chain&gt; &lt;CA1&gt;,&lt;CA2&gt;,&lt;CA3&gt;\n\nChains: SOL, BNB, Base",
            parse_mode="HTML"
        )
        return

    chat_id = update.message.chat_id
    full = toggle_show_full.get(chat_id, True)
    
    # Check if first arg is a chain name
    chain_specified = None
    if len(context.args) >= 2:
        potential_chain = normalize_chain(context.args[0])
        if potential_chain:
            chain_specified = potential_chain
            contracts_str = " ".join(context.args[1:])
        else:
            contracts_str = " ".join(context.args)
    else:
        contracts_str = " ".join(context.args)
    
    contracts = contracts_str.replace(" ", "").split(",")
    
    for ca in contracts:
        ca = ca.strip()
        if not ca:
            continue
            
        if chain_specified:
            chain = chain_specified
        else:
            chain = detect_chain(ca)
        
        if chain == "Unknown":
            await update.message.reply_text(f"❌ Cannot detect chain for <code>{ca}</code>. Skipping.", parse_mode="HTML")
            continue
            
        links = generate_links(ca, chain, full)
        if not links:
            await update.message.reply_text(f"❌ Cannot generate links for <code>{ca}</code>. Skipping.", parse_mode="HTML")
            continue
            
        reply_markup = InlineKeyboardMarkup(links)
        await update.message.reply_text(
            f"🔗 Links for contract: <code>{ca}</code>\nChain: <b>{chain}</b>",
            parse_mode="HTML",
            reply_markup=reply_markup,
        )

# -----------------------
# /start and /help
# -----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """⚡ Welcome to <b>MmkAlphaScanner Quick Scan Bot</b>!

<b>Commands:</b>
🪙 /scan &lt;contract_address&gt;
   /scan &lt;chain&gt; &lt;contract_address&gt;
   Single token quick links

⚡ /scanmulti &lt;CA1&gt;,&lt;CA2&gt;,&lt;CA3&gt;
   /scanmulti &lt;chain&gt; &lt;CA1&gt;,&lt;CA2&gt;
   Bulk token links

🔁 /toggleshowfull
   Toggle compact/full link view

<b>Supported Chains:</b>
• SOL (Solana)
• BNB (Binance Smart Chain)
• Base

<b>Features:</b>
• Auto-detects chain from contract format
• Or specify chain explicitly for accuracy
• Opens scanners, block explorers, and swap pages
• Full mode shows all links; compact shows main explorer only"""
    await update.message.reply_text(text, parse_mode="HTML")

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
