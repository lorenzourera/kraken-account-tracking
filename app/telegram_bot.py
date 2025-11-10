# import logging
# from telegram import Update
# from telegram.ext import Application, CommandHandler, ContextTypes
# from database import Database
# from config import DATABASE_URL, TELEGRAM_BOT_TOKEN, ALLOWED_USER_IDS
# from decimal import Decimal
# from telegram import Bot
# import csv
# import io
# from datetime import datetime

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s %(levelname)s %(message)s",
#     handlers=[logging.StreamHandler()],
# )
# logging.getLogger("httpx").setLevel(logging.WARNING)
# logging.getLogger("httpcore").setLevel(logging.WARNING)
# logging.getLogger("telegram").setLevel(logging.WARNING)
# logger = logging.getLogger(__name__)

# db = Database(DATABASE_URL)


# def is_authorized(user_id: int) -> bool:
#     if not ALLOWED_USER_IDS:
#         return False
#     return str(user_id) in [uid.strip() for uid in ALLOWED_USER_IDS.split(",") if uid.strip()]


# async def notify_owner(text: str):
#     try:
#         bot = Bot(token=TELEGRAM_BOT_TOKEN)
#         owner_id = ALLOWED_USER_IDS.split(",")[0].strip()
#         await bot.send_message(chat_id=owner_id, text=f"DEBUG: {text}")
#     except:
#         pass


# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     user = update.effective_user
#     if not is_authorized(user.id):
#         await update.message.reply_text("Access denied.")
#         return
#     await update.message.reply_text(
#         "ZO KRAKEN TRACKING ACTIVE\n\n"
#         "/pull → fetch balance & trades\n"
#         "/balance → latest balance\n"
#         "/returns → recent returns\n"
#         "/trades → recent trades\n"
#         "/export [limit] → export balance snapshots\n"
#         "/export_returns [limit] → export returns\n"
#         "/export_trades [limit] → export all trades as CSV"
#     )
#     await notify_owner(f"@{user.username or user.id} started bot")


# async def pull(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if not is_authorized(update.effective_user.id):
#         return
#     await update.message.reply_text("<i>Pulling fresh data...</i>", parse_mode="HTML")
#     try:
#         from main import run_daily_snapshot
#         run_daily_snapshot()
#         await update.message.reply_text("Fresh data pulled! Use /balance or /trades")
#     except Exception as e:
#         await update.message.reply_text(f"Pull failed: {e}")


# async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if not is_authorized(update.effective_user.id):
#         return

#     bal = db.get_latest_balance("kraken")
#     if not bal:
#         await update.message.reply_text("No data — run /pull first")
#         return

#     import json
#     balances_raw = bal["balances"]
#     if isinstance(balances_raw, str):
#         try:
#             balances_dict = json.loads(balances_raw)
#         except:
#             await update.message.reply_text("Corrupted balance data")
#             return
#     else:
#         balances_dict = balances_raw

#     asset_values = {}
#     for asset, data in balances_dict.items():
#         try:
#             usd_val = float(data.get("usd_value", 0))
#             if usd_val > 0.01:
#                 asset_values[asset] = usd_val
#         except:
#             continue

#     total = float(bal["total_balance_usd"])
#     text = f"<b>LATEST KRAKEN BALANCE</b>\n"
#     text += f"<pre>Account: {bal['account_id']}</pre>\n"
#     text += f"<pre>Date:    {bal['snapshot_date']}</pre>\n"
#     text += f"<b>TOTAL: ${total:,.2f}</b>\n\n"
#     text += "<b>Top Assets:</b>\n<code>\n"

#     for asset, usd_val in sorted(asset_values.items(), key=lambda x: x[1], reverse=True)[:20]:
#         amt = balances_dict[asset].get("amount", "0")
#         try:
#             amt_float = float(amt)
#             text += f"{asset:<8} {amt_float:>15,.8f}  (${usd_val:,.2f})\n"
#         except:
#             text += f"{asset:<8} {amt:>15}  (${usd_val:,.2f})\n"
#     text += "</code>"

#     await update.message.reply_text(text, parse_mode="HTML")


# async def trades(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if not is_authorized(update.effective_user.id):
#         return

#     limit = 20
#     if context.args:
#         try:
#             limit = int(context.args[0])
#             if limit < 1: limit = 20
#         except:
#             pass

#     rows = db.get_all_trades(limit=limit) if hasattr(db, 'get_all_trades') else []
#     if not rows:
#         await update.message.reply_text("No trades found. Run /pull first.")
#         return

#     text = f"<b>RECENT TRADES</b> (last {len(rows)})\n<code>\n"
#     text += f"{'Date':<12} {'Symbol':<12} {'Side':<6} {'Amt':>12} {'Price':>10} {'Cost':>10}\n"
#     text += "—" * 60 + "\n"

#     for t in rows:
#         ts = t['trade_timestamp']
#         if isinstance(ts, datetime):
#             date_str = ts.strftime("%m-%d %H:%M")
#         else:
#             date_str = str(ts)[:16].replace("T", " ")

#         symbol = t['symbol'].replace("/", "")[:10]
#         side = "BUY" if t['side'] == 'buy' else "SELL"
#         side_icon = "BUY" if side == "BUY" else "SELL"
#         amt = float(t['amount'])
#         price = float(t['price'])
#         cost = float(t['cost'])

#         text += f"{date_str:<12} {symbol:<12} {side_icon:<6} {amt:>12,.4f} ${price:>9,.2f} ${cost:>9,.0f}\n"

#     text += "</code>"
#     await update.message.reply_text(text, parse_mode="HTML")


# async def export(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if not is_authorized(update.effective_user.id):
#         return

#     preview_limit = 10
#     if context.args:
#         try:
#             preview_limit = int(context.args[0])
#             if preview_limit < 1: preview_limit = 10
#         except:
#             pass

#     await update.message.reply_text(f"<i>Exporting balance snapshots...</i>", parse_mode="HTML")

#     snapshots = db.get_all_balances(exchange="kraken", limit=1000)
#     if not snapshots:
#         await update.message.reply_text("No balance data.")
#         return

#     preview_text = f"<b>BALANCE EXPORT</b> — {len(snapshots)} rows\n<code>"
#     preview_text += f"{'Date':<20} {'Total USD':>15}\n" + "—"*37 + "\n"
#     for s in snapshots[:preview_limit]:
#         ts = s['timestamp'].strftime("%Y-%m-%d %H:%M") if isinstance(s['timestamp'], datetime) else str(s['timestamp'])[:16]
#         total = float(s['total_balance_usd'])
#         preview_text += f"{ts:<20} ${total:>14,.2f}\n"
#     preview_text += "</code>"
#     await update.message.reply_text(preview_text, parse_mode="HTML")

#     buffer = io.StringIO()
#     writer = csv.writer(buffer)
#     writer.writerow(["timestamp", "total_balance_usd"])
#     for s in snapshots:
#         ts = s['timestamp'].strftime("%Y-%m-%d %H:%M:%S") if isinstance(s['timestamp'], datetime) else s['timestamp']
#         writer.writerow([ts, f"{float(s['total_balance_usd']):.2f}"])

#     await update.message.reply_document(
#         document=io.BytesIO(buffer.getvalue().encode('utf-8')),
#         filename=f"balances_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
#         caption=f"Balance snapshots: {len(snapshots)} rows"
#     )


# async def export_returns(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if not is_authorized(update.effective_user.id):
#         return

#     limit = 1000
#     if context.args:
#         try: limit = int(context.args[0])
#         except: pass

#     await update.message.reply_text("<i>Exporting returns...</i>", parse_mode="HTML")
#     returns = db.get_all_returns(exchange="kraken", limit=limit)
#     if not returns:
#         await update.message.reply_text("No returns data.")
#         return

#     buffer = io.StringIO()
#     writer = csv.writer(buffer)
#     writer.writerow(["date", "previous_date", "return_usd", "return_pct", "balance_usd"])
#     for r in returns:
#         writer.writerow([
#             r['return_date'],
#             r['previous_date'],
#             f"{float(r['daily_return_usd']):.2f}",
#             f"{float(r['daily_return_pct']):.2f}",
#             f"{float(r['current_balance_usd']):.2f}"
#         ])

#     await update.message.reply_document(
#         document=io.BytesIO(buffer.getvalue().encode('utf-8')),
#         filename=f"returns_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
#         caption=f"Returns: {len(returns)} days"
#     )


# async def export_trades(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if not is_authorized(update.effective_user.id):
#         return

#     limit = 5000
#     if context.args:
#         try: limit = int(context.args[0])
#         except: pass

#     await update.message.reply_text(f"<i>Exporting up to {limit} trades...</i>", parse_mode="HTML")

#     trades = db.get_all_trades(limit=limit) if hasattr(db, 'get_all_trades') else []
#     if not trades:
#         await update.message.reply_text("No trades found.")
#         return

#     buffer = io.StringIO()
#     writer = csv.writer(buffer)
#     writer.writerow([
#         "timestamp", "symbol", "side", "type", "amount", "price", "cost",
#         "fee_cost", "fee_currency", "trade_id"
#     ])

#     for t in trades:
#         ts = t['trade_timestamp']
#         if isinstance(ts, datetime):
#             ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")
#         else:
#             ts_str = str(ts)

#         writer.writerow([
#             ts_str,
#             t['symbol'],
#             t['side'].upper(),
#             t.get('type', ''),
#             f"{float(t['amount']):.8f}",
#             f"{float(t['price']):.8f}",
#             f"{float(t['cost']):.2f}",
#             t['fee_cost'] or '',
#             t['fee_currency'] or '',
#             t['trade_id']
#         ])

#     filename = f"trades_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
#     await update.message.reply_document(
#         document=io.BytesIO(buffer.getvalue().encode('utf-8')),
#         filename=filename,
#         caption=f"Exported {len(trades)} trades"
#     )
#     await update.message.reply_text(f"Done! {len(trades)} trades exported.")


# def main():
#     app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

#     app.add_handler(CommandHandler("start", start))
#     app.add_handler(CommandHandler("pull", pull))
#     app.add_handler(CommandHandler("balance", balance))
#     app.add_handler(CommandHandler("trades", trades))
#     app.add_handler(CommandHandler("export", export))
#     app.add_handler(CommandHandler("export_returns", export_returns))
#     app.add_handler(CommandHandler("export_trades", export_trades))

#     logger.info("ZO KRAKEN BOT STARTED — @zo_urera")
#     app.run_polling(drop_pending_updates=True)


# if __name__ == "__main__":
#     main()


import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from database import Database
from config import DATABASE_URL, TELEGRAM_BOT_TOKEN, ALLOWED_USER_IDS
from decimal import Decimal
from telegram import Bot
import csv
import io
from datetime import datetime

# Enhanced logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()],
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logger = logging.getLogger("ZO_KRAKEN_BOT")


db = Database(DATABASE_URL)


def is_authorized(user_id: int) -> bool:
    if not ALLOWED_USER_IDS:
        return False
    allowed = [uid.strip() for uid in ALLOWED_USER_IDS.split(",") if uid.strip()]
    return str(user_id) in allowed


async def notify_owner(text: str):
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        owner_id = ALLOWED_USER_IDS.split(",")[0].strip()
        await bot.send_message(chat_id=owner_id, text=f"BOT LOG: {text}")
    except Exception as e:
        logger.error(f"Failed to notify owner: {e}")


def log_command(user, command: str, args=None):
    username = user.username or "no_username"
    full_name = user.full_name
    user_id = user.id
    args_str = " ".join(args) if args else "(no args)"
    logger.info(f"COMMAND | @{username} ({full_name}, ID: {user_id}) | /{command} {args_str}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_command(user, "start")
    
    if not is_authorized(user.id):
        logger.warning(f"UNAUTHORIZED ACCESS ATTEMPT | User ID: {user.id} | @{user.username or 'unknown'}")
        await update.message.reply_text("Access denied.")
        return

    await update.message.reply_text(
        "ZO KRAKEN TRACKING ACTIVE\n\n"
        "/pull → fetch balance & trades\n"
        "/balance → latest balance\n"
        "/returns → recent returns\n"
        "/trades → recent trades\n"
        "/export [limit] → export balance snapshots\n"
        "/export_returns [limit] → export returns\n"
        "/export_trades [limit] → export all trades as CSV"
    )
    await notify_owner(f"User @{user.username or user.id} started the bot")


async def pull(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_command(user, "pull")
    
    if not is_authorized(user.id):
        return

    await update.message.reply_text("<i>Pulling fresh data from Kraken...</i>", parse_mode="HTML")
    logger.info("Executing run_daily_snapshot() via /pull")
    
    try:
        from main import run_daily_snapshot
        run_daily_snapshot()
        await update.message.reply_text("Fresh data pulled successfully! Use /balance or /trades")
        logger.info("Pull completed successfully")
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Pull failed: {error_msg}")
        await update.message.reply_text(f"Pull failed: {error_msg}")


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_command(user, "balance")
    
    if not is_authorized(user.id):
        return

    logger.info("Fetching latest balance snapshot")
    bal = db.get_latest_balance("kraken")
    if not bal:
        await update.message.reply_text("No data — run /pull first")
        logger.warning("No balance data found in DB")
        return

    import json
    balances_raw = bal["balances"]
    if isinstance(balances_raw, str):
        try:
            balances_dict = json.loads(balances_raw)
        except Exception as e:
            logger.error(f"JSON decode failed for balances: {e}")
            await update.message.reply_text("Corrupted balance data")
            return
    else:
        balances_dict = balances_raw

    asset_values = {}
    for asset, data in balances_dict.items():
        try:
            usd_val = float(data.get("usd_value", 0))
            if usd_val > 0.01:
                asset_values[asset] = usd_val
        except:
            continue

    total = float(bal["total_balance_usd"])
    text = f"<b>LATEST KRAKEN BALANCE</b>\n"
    text += f"<pre>Account: {bal['account_id']}</pre>\n"
    text += f"<pre>Date:    {bal['snapshot_date']}</pre>\n"
    text += f"<b>TOTAL: ${total:,.2f}</b>\n\n"
    text += "<b>Top Assets:</b>\n<code>\n"

    for asset, usd_val in sorted(asset_values.items(), key=lambda x: x[1], reverse=True)[:20]:
        amt = balances_dict[asset].get("amount", "0")
        try:
            amt_float = float(amt)
            text += f"{asset:<8} {amt_float:>15,.8f}  (${usd_val:,.2f})\n"
        except:
            text += f"{asset:<8} {amt:>15}  (${usd_val:,.2f})\n"
    text += "</code>"

    await update.message.reply_text(text, parse_mode="HTML")
    logger.info(f"Balance sent | Total: ${total:,.2f} | Assets: {len(asset_values)}")


async def trades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    limit = 20
    if context.args:
        try:
            limit = int(context.args[0])
            if limit < 1:
                limit = 20
        except:
            limit = 20
    log_command(user, "trades", context.args)

    if not is_authorized(user.id):
        return

    logger.info(f"Fetching {limit} recent trades")
    rows = db.get_all_trades(limit=limit) if hasattr(db, 'get_all_trades') else []
    if not rows:
        await update.message.reply_text("No trades found. Run /pull first.")
        logger.warning("No trades in database")
        return

    text = f"<b>RECENT TRADES</b> (last {len(rows)})\n<code>\n"
    text += f"{'Date':<12} {'Symbol':<12} {'Side':<6} {'Amt':>12} {'Price':>10} {'Cost':>10}\n"
    text += "—" * 60 + "\n"

    for t in rows:
        ts = t['trade_timestamp']
        date_str = ts.strftime("%m-%d %H:%M") if isinstance(ts, datetime) else str(ts)[:16].replace("T", " ")
        symbol = t['symbol'].replace("/", "")[:10]
        side = "BUY" if t['side'] == 'buy' else "SELL"
        side_icon = "BUY" if side == "BUY" else "SELL"
        amt = float(t['amount'])
        price = float(t['price'])
        cost = float(t['cost'])

        text += f"{date_str:<12} {symbol:<12} {side_icon:<6} {amt:>12,.4f} ${price:>9,.2f} ${cost:>9,.0f}\n"

    text += "</code>"
    await update.message.reply_text(text, parse_mode="HTML")
    logger.info(f"Sent {len(rows)} trades to user")


async def export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_command(user, "export", context.args)
    
    if not is_authorized(user.id):
        return

    preview_limit = 10
    if context.args:
        try:
            preview_limit = int(context.args[0])
            if preview_limit < 1:
                preview_limit = 10
        except:
            preview_limit = 10

    logger.info(f"Exporting balance snapshots | preview: {preview_limit}")
    await update.message.reply_text(f"<i>Exporting balance snapshots...</i>", parse_mode="HTML")

    snapshots = db.get_all_balances(exchange="kraken", limit=1000)
    if not snapshots:
        await update.message.reply_text("No balance data.")
        return

    preview_text = f"<b>BALANCE EXPORT</b> — {len(snapshots)} rows\n<code>"
    preview_text += f"{'Date':<20} {'Total USD':>15}\n" + "—"*37 + "\n"
    for s in snapshots[:preview_limit]:
        ts = s['timestamp'].strftime("%Y-%m-%d %H:%M") if isinstance(s['timestamp'], datetime) else str(s['timestamp'])[:16]
        total = float(s['total_balance_usd'])
        preview_text += f"{ts:<20} ${total:>14,.2f}\n"
    preview_text += "</code>"
    await update.message.reply_text(preview_text, parse_mode="HTML")

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["timestamp", "total_balance_usd"])
    for s in snapshots:
        ts = s['timestamp'].strftime("%Y-%m-%d %H:%M:%S") if isinstance(s['timestamp'], datetime) else s['timestamp']
        writer.writerow([ts, f"{float(s['total_balance_usd']):.2f}"])

    filename = f"balances_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    await update.message.reply_document(
        document=io.BytesIO(buffer.getvalue().encode('utf-8')),
        filename=filename,
        caption=f"Balance snapshots: {len(snapshots)} rows"
    )
    logger.info(f"Balance CSV exported | {len(snapshots)} rows | {filename}")


async def export_returns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_command(user, "export_returns", context.args)
    
    if not is_authorized(user.id):
        return

    limit = 1000
    if context.args:
        try:
            limit = int(context.args[0])
        except:
            pass

    logger.info(f"Exporting returns data | limit: {limit}")
    await update.message.reply_text("<i>Exporting returns...</i>", parse_mode="HTML")
    
    returns = db.get_all_returns(exchange="kraken", limit=limit)
    if not returns:
        await update.message.reply_text("No returns data.")
        return

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["date", "previous_date", "return_usd", "return_pct", "balance_usd"])
    for r in returns:
        writer.writerow([
            r['return_date'],
            r['previous_date'],
            f"{float(r['daily_return_usd']):.2f}",
            f"{float(r['daily_return_pct']):.2f}",
            f"{float(r['current_balance_usd']):.2f}"
        ])

    filename = f"returns_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    await update.message.reply_document(
        document=io.BytesIO(buffer.getvalue().encode('utf-8')),
        filename=filename,
        caption=f"Returns: {len(returns)} days"
    )
    logger.info(f"Returns CSV exported | {len(returns)} rows | {filename}")


async def export_trades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_command(user, "export_trades", context.args)
    
    if not is_authorized(user.id):
        return

    limit = 5000
    if context.args:
        try:
            limit = int(context.args[0])
        except:
            pass

    logger.info(f"Exporting trades | limit: {limit}")
    await update.message.reply_text(f"<i>Exporting up to {limit} trades...</i>", parse_mode="HTML")

    trades = db.get_all_trades(limit=limit) if hasattr(db, 'get_all_trades') else []
    if not trades:
        await update.message.reply_text("No trades found.")
        logger.warning("No trades found for export")
        return

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "timestamp", "symbol", "side", "type", "amount", "price", "cost",
        "fee_cost", "fee_currency", "trade_id"
    ])

    for t in trades:
        ts = t['trade_timestamp']
        ts_str = ts.strftime("%Y-%m-%d %H:%M:%S") if isinstance(ts, datetime) else str(ts)
        writer.writerow([
            ts_str,
            t['symbol'],
            t['side'].upper(),
            t.get('type', ''),
            f"{float(t['amount']):.8f}",
            f"{float(t['price']):.8f}",
            f"{float(t['cost']):.2f}",
            t['fee_cost'] or '',
            t['fee_currency'] or '',
            t['trade_id']
        ])

    filename = f"trades_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    await update.message.reply_document(
        document=io.BytesIO(buffer.getvalue().encode('utf-8')),
        filename=filename,
        caption=f"Exported {len(trades)} trades"
    )
    await update.message.reply_text(f"Done! {len(trades)} trades exported.")
    logger.info(f"Trades CSV exported | {len(trades)} trades | {filename}")


def main():
    logger.info("KRAKEN ACCOUNT TRACKING BOT STARTED")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pull", pull))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("trades", trades))
    app.add_handler(CommandHandler("export", export))
    app.add_handler(CommandHandler("export_returns", export_returns))
    app.add_handler(CommandHandler("export_trades", export_trades))

    logger.info("Bot handlers registered. Starting polling...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()