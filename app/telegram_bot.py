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
# logging.getLogger("httpx").setLevel(logging.WARNING)  # Silence HTTP
# logging.getLogger("httpcore").setLevel(logging.WARNING)  # Silence HTTP
# logging.getLogger("telegram").setLevel(logging.WARNING)  # Silence telegram.ext
# logger = logging.getLogger(__name__)

# db = Database(DATABASE_URL)


# def is_authorized(user_id: int) -> bool:
#     if not ALLOWED_USER_IDS:
#         return False
#     return str(user_id) in [
#         uid.strip() for uid in ALLOWED_USER_IDS.split(",") if uid.strip()
#     ]


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
#         "ZO KRAKEN BOT ACTIVE\n"
#         "/pull → fetches latest balance and stores in database\n"
#         "/balance → show current balance\n"
#         "/export_balances [limit] → export balance snapshots (default: 10 preview rows)"
#     )
#     await notify_owner(f"@{user.username or user.id} started bot")


# async def pull(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if not is_authorized(update.effective_user.id):
#         return
#     await update.message.reply_text(
#         "<i>Pulling fresh balance...</i>", parse_mode="HTML"
#     )
#     try:
#         from main import run_daily_snapshot

#         run_daily_snapshot()
#         await update.message.reply_text("Saved! Run /balance")
#     except Exception as e:
#         await update.message.reply_text(f"Pull failed: {e}")


# async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     if not is_authorized(update.effective_user.id):
#         return

#     logger.info("Fetching latest balance...")
#     bal = db.get_latest_balance("kraken")
#     if not bal:
#         await update.message.reply_text("No data — run /pull first")
#         return

#     # === SMART PARSING: handle both old (dict) and new (json string) formats ===
#     import json

#     balances_raw = bal["balances"]

#     if isinstance(balances_raw, str):
#         try:
#             balances_dict = json.loads(balances_raw)
#         except json.JSONDecodeError as e:
#             logger.error(f"Failed to parse balances JSON: {e}")
#             await update.message.reply_text("Corrupted balance data")
#             return
#     else:
#         balances_dict = balances_raw  # already a dict

#     # Convert usd_value strings → float, filter small dust
#     try:
#         asset_values = {}
#         for asset, data in balances_dict.items():
#             usd_str = data.get("usd_value", "0")
#             try:
#                 usd_val = float(usd_str)
#                 if usd_val > 0.01:
#                     asset_values[asset] = usd_val
#             except (ValueError, TypeError):
#                 continue
#     except Exception as e:
#         logger.error(f"Error processing balances: {e}")
#         await update.message.reply_text("Balance parse error")
#         return

#     total = float(bal["total_balance_usd"])
#     text = f"<b>LATEST KRAKEN BALANCE</b>\n"
#     text += f"<pre>Account: {bal['account_id']}</pre>\n"
#     text += f"<pre>Date:    {bal['snapshot_date']}</pre>\n"
#     text += f"<b>TOTAL: ${total:,.2f}</b>\n\n"
#     text += "<b>Top Assets:</b>\n<code>\n"

#     for asset, usd_val in sorted(
#         asset_values.items(), key=lambda x: x[1], reverse=True
#     )[:20]:
#         amt = balances_dict[asset].get("amount", "0")
#         try:
#             amt_float = float(amt)
#             text += f"{asset:<8} {amt_float:>15,.8f}  (${usd_val:,.2f})\n"
#         except:
#             text += f"{asset:<8} {amt:>15}  (${usd_val:,.2f})\n"
#     text += "</code>"

#     try:
#         await update.message.reply_text(text, parse_mode="HTML")
#         logger.info("Balance message sent successfully!")
#     except Exception as e:
#         logger.error(f"Telegram send failed: {e}")
#         await update.message.reply_text("Failed to send balance")


# async def export_balances(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """
#     Export balance snapshots as CSV
#     Usage: /export [preview_limit]
#     Default preview_limit is 10
#     """
#     if not is_authorized(update.effective_user.id):
#         return

#     # Parse preview limit from command args
#     preview_limit = 10
#     if context.args and len(context.args) > 0:
#         try:
#             preview_limit = int(context.args[0])
#             if preview_limit < 1:
#                 preview_limit = 10
#         except ValueError:
#             await update.message.reply_text("Invalid limit. Using default: 10")

#     await update.message.reply_text(
#         f"<i>Exporting balance snapshots (preview: {preview_limit} rows)...</i>",
#         parse_mode="HTML"
#     )

#     try:
#         # Fetch all snapshots from database
#         all_snapshots = db.get_all_balances(exchange="kraken", limit=1000)
        
#         if not all_snapshots:
#             await update.message.reply_text("No snapshot data found in database")
#             return

#         # Define columns to export
#         columns = ["timestamp", "total_balance_usd"]
        
#         # Create preview message with first X rows
#         preview_text = f"<b>BALANCE SNAPSHOTS EXPORT</b>\n"
#         preview_text += f"<b>Total rows:</b> {len(all_snapshots)}\n"
#         preview_text += f"<b>Preview (first {min(preview_limit, len(all_snapshots))} rows):</b>\n\n"
#         preview_text += "<code>"
#         preview_text += f"{'Timestamp':<20} {'Total USD':>15}\n"
#         preview_text += "-" * 37 + "\n"
        
#         for snapshot in all_snapshots[:preview_limit]:
#             timestamp = snapshot.get("timestamp", "N/A")
#             if isinstance(timestamp, datetime):
#                 timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
#             else:
#                 timestamp_str = str(timestamp)[:19]
            
#             total_usd = snapshot.get("total_balance_usd", 0)
#             try:
#                 total_usd_float = float(total_usd)
#                 preview_text += f"{timestamp_str:<20} ${total_usd_float:>14,.2f}\n"
#             except (ValueError, TypeError):
#                 preview_text += f"{timestamp_str:<20} ${str(total_usd):>14}\n"
        
#         preview_text += "</code>"
        
#         await update.message.reply_text(preview_text, parse_mode="HTML")
        
#         # Generate CSV file with all data
#         csv_buffer = io.StringIO()
#         csv_writer = csv.DictWriter(csv_buffer, fieldnames=columns)
#         csv_writer.writeheader()
        
#         for snapshot in all_snapshots:
#             row_data = {}
#             for col in columns:
#                 value = snapshot.get(col)
#                 # Format timestamp
#                 if col == "timestamp" and isinstance(value, datetime):
#                     row_data[col] = value.strftime("%Y-%m-%d %H:%M:%S")
#                 # Format decimal/float values
#                 elif col == "total_balance_usd":
#                     try:
#                         row_data[col] = f"{float(value):.2f}"
#                     except (ValueError, TypeError):
#                         row_data[col] = str(value)
#                 else:
#                     row_data[col] = str(value) if value is not None else ""
            
#             csv_writer.writerow(row_data)
        
#         # Send CSV file
#         csv_bytes = csv_buffer.getvalue().encode('utf-8')
#         filename = f"balance_snapshots_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
#         await update.message.reply_document(
#             document=io.BytesIO(csv_bytes),
#             filename=filename,
#             caption=f"📊 Complete export: {len(all_snapshots)} snapshots"
#         )
        
#         logger.info(f"Export successful: {len(all_snapshots)} rows sent")
        
#     except Exception as e:
#         logger.error(f"Export failed: {e}")
#         await update.message.reply_text(f"Export failed: {str(e)}")


# def main():
#     app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
#     app.add_handler(CommandHandler("start", start))
#     app.add_handler(CommandHandler("balance", balance))
#     app.add_handler(CommandHandler("pull", pull))
#     app.add_handler(CommandHandler("export_balances", export_balances))
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


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler()],
)
logging.getLogger("httpx").setLevel(logging.WARNING)  # Silence HTTP
logging.getLogger("httpcore").setLevel(logging.WARNING)  # Silence HTTP
logging.getLogger("telegram").setLevel(logging.WARNING)  # Silence telegram.ext
logger = logging.getLogger(__name__)

db = Database(DATABASE_URL)


def is_authorized(user_id: int) -> bool:
    if not ALLOWED_USER_IDS:
        return False
    return str(user_id) in [
        uid.strip() for uid in ALLOWED_USER_IDS.split(",") if uid.strip()
    ]


async def notify_owner(text: str):
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        owner_id = ALLOWED_USER_IDS.split(",")[0].strip()
        await bot.send_message(chat_id=owner_id, text=f"DEBUG: {text}")
    except:
        pass


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_authorized(user.id):
        await update.message.reply_text("Access denied.")
        return
    await update.message.reply_text(
        "ZO KRAKEN BOT ACTIVE\n"
        "/pull → fetch balance & calculate returns\n"
        "/balance → show latest balance\n"
        "/returns → show recent returns\n"
        "/export [limit] → export balance snapshots\n"
        "/export_returns [limit] → export returns data"
    )
    await notify_owner(f"@{user.username or user.id} started bot")


async def pull(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return
    await update.message.reply_text(
        "<i>Pulling fresh balance...</i>", parse_mode="HTML"
    )
    try:
        from main import run_daily_snapshot

        run_daily_snapshot()
        await update.message.reply_text("Saved! Run /balance")
    except Exception as e:
        await update.message.reply_text(f"Pull failed: {e}")


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    logger.info("Fetching latest balance...")
    bal = db.get_latest_balance("kraken")
    if not bal:
        await update.message.reply_text("No data — run /pull first")
        return

    # === SMART PARSING: handle both old (dict) and new (json string) formats ===
    import json

    balances_raw = bal["balances"]

    if isinstance(balances_raw, str):
        try:
            balances_dict = json.loads(balances_raw)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse balances JSON: {e}")
            await update.message.reply_text("Corrupted balance data")
            return
    else:
        balances_dict = balances_raw  # already a dict

    # Convert usd_value strings → float, filter small dust
    try:
        asset_values = {}
        for asset, data in balances_dict.items():
            usd_str = data.get("usd_value", "0")
            try:
                usd_val = float(usd_str)
                if usd_val > 0.01:
                    asset_values[asset] = usd_val
            except (ValueError, TypeError):
                continue
    except Exception as e:
        logger.error(f"Error processing balances: {e}")
        await update.message.reply_text("Balance parse error")
        return

    total = float(bal["total_balance_usd"])
    text = f"<b>LATEST KRAKEN BALANCE</b>\n"
    text += f"<pre>Account: {bal['account_id']}</pre>\n"
    text += f"<pre>Date:    {bal['snapshot_date']}</pre>\n"
    text += f"<b>TOTAL: ${total:,.2f}</b>\n\n"
    text += "<b>Top Assets:</b>\n<code>\n"

    for asset, usd_val in sorted(
        asset_values.items(), key=lambda x: x[1], reverse=True
    )[:20]:
        amt = balances_dict[asset].get("amount", "0")
        try:
            amt_float = float(amt)
            text += f"{asset:<8} {amt_float:>15,.8f}  (${usd_val:,.2f})\n"
        except:
            text += f"{asset:<8} {amt:>15}  (${usd_val:,.2f})\n"
    text += "</code>"

    try:
        await update.message.reply_text(text, parse_mode="HTML")
        logger.info("Balance message sent successfully!")
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        await update.message.reply_text("Failed to send balance")


async def export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Export balance snapshots as CSV
    Usage: /export [preview_limit]
    Default preview_limit is 10
    """
    if not is_authorized(update.effective_user.id):
        return

    # Parse preview limit from command args
    preview_limit = 10
    if context.args and len(context.args) > 0:
        try:
            preview_limit = int(context.args[0])
            if preview_limit < 1:
                preview_limit = 10
        except ValueError:
            await update.message.reply_text("Invalid limit. Using default: 10")

    await update.message.reply_text(
        f"<i>Exporting balance snapshots (preview: {preview_limit} rows)...</i>",
        parse_mode="HTML"
    )

    try:
        # Fetch all snapshots from database
        all_snapshots = db.get_all_balances(exchange="kraken", limit=1000)
        
        if not all_snapshots:
            await update.message.reply_text("No snapshot data found in database")
            return

        # Define columns to export
        columns = ["timestamp", "total_balance_usd"]
        
        # Create preview message with first X rows
        preview_text = f"<b>BALANCE SNAPSHOTS EXPORT</b>\n"
        preview_text += f"<b>Total rows:</b> {len(all_snapshots)}\n"
        preview_text += f"<b>Preview (first {min(preview_limit, len(all_snapshots))} rows):</b>\n\n"
        preview_text += "<code>"
        preview_text += f"{'Timestamp':<20} {'Total USD':>15}\n"
        preview_text += "-" * 37 + "\n"
        
        for snapshot in all_snapshots[:preview_limit]:
            timestamp = snapshot.get("timestamp", "N/A")
            if isinstance(timestamp, datetime):
                timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            else:
                timestamp_str = str(timestamp)[:19]
            
            total_usd = snapshot.get("total_balance_usd", 0)
            try:
                total_usd_float = float(total_usd)
                preview_text += f"{timestamp_str:<20} ${total_usd_float:>14,.2f}\n"
            except (ValueError, TypeError):
                preview_text += f"{timestamp_str:<20} ${str(total_usd):>14}\n"
        
        preview_text += "</code>"
        
        await update.message.reply_text(preview_text, parse_mode="HTML")
        
        # Generate CSV file with all data
        csv_buffer = io.StringIO()
        csv_writer = csv.DictWriter(csv_buffer, fieldnames=columns)
        csv_writer.writeheader()
        
        for snapshot in all_snapshots:
            row_data = {}
            for col in columns:
                value = snapshot.get(col)
                # Format timestamp
                if col == "timestamp" and isinstance(value, datetime):
                    row_data[col] = value.strftime("%Y-%m-%d %H:%M:%S")
                # Format decimal/float values
                elif col == "total_balance_usd":
                    try:
                        row_data[col] = f"{float(value):.2f}"
                    except (ValueError, TypeError):
                        row_data[col] = str(value)
                else:
                    row_data[col] = str(value) if value is not None else ""
            
            csv_writer.writerow(row_data)
        
        # Send CSV file
        csv_bytes = csv_buffer.getvalue().encode('utf-8')
        filename = f"balance_snapshots_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        await update.message.reply_document(
            document=io.BytesIO(csv_bytes),
            filename=filename,
            caption=f"📊 Complete export: {len(all_snapshots)} snapshots"
        )
        
        logger.info(f"Export successful: {len(all_snapshots)} rows sent")
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        await update.message.reply_text(f"Export failed: {str(e)}")


def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("pull", pull))
    app.add_handler(CommandHandler("export", export))
    logger.info("ZO KRAKEN BOT STARTED — @zo_urera")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()