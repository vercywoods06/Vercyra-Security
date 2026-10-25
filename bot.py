import asyncio
import logging
import os

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import bankroll
import db
import web

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("vercyra")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Vercyra Aviator AI is online. Send /help for commands.")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/add <multiplier> - log a round result, e.g. /add 2.35\n"
        "/history - last 10 rounds\n"
        "/stats - summary of all logged rounds\n"
        "/risk <bankroll> <stake> <cashout> - what flat betting costs, e.g. /risk 100 2 1.5\n\n"
        "These are your own logged results. Aviator multipliers cannot be reliably predicted."
    )


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        m = float(context.args[0].lower().rstrip("x"))
        if not 1.0 <= m <= 1_000_000:
            raise ValueError
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /add 2.35 (a multiplier of 1.00 or more)")
        return
    user = update.effective_user
    await asyncio.to_thread(db.add_round, m, user.username or str(user.id))
    await update.message.reply_text(f"Logged {m:.2f}x")


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = await asyncio.to_thread(db.recent, 10)
    if not rows:
        await update.message.reply_text("No rounds logged yet. Use /add 2.35")
        return
    await update.message.reply_text("Last rounds (newest first):\n" + "\n".join(f"#{r['id']}  {r['multiplier']:.2f}x" for r in rows))


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = await asyncio.to_thread(db.stats)
    if not s["count"]:
        await update.message.reply_text("No rounds logged yet. Use /add 2.35")
        return
    await update.message.reply_text(
        f"Rounds: {s['count']}\nAverage: {s['average']}x\nMax: {s['max']}x  Min: {s['min']}x\n"
        f"Below 2x: {s['pct_below_2x']}%\nCurrent run below 2x: {s['current_streak_below_2x']}"
    )


async def risk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        b, st, c = (float(x) for x in context.args[:3])
        if len(context.args) < 3 or b <= 0 or st <= 0 or c <= 1.0 or st > b:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Usage: /risk <bankroll> <stake> <cashout>\nExample: /risk 100 2 1.5\n(stake must not exceed bankroll, cashout above 1.0)")
        return
    r = await asyncio.to_thread(bankroll.analyse, b, st, c)
    await update.message.reply_text(
        f"Flat bet {st:g} at {c:g}x, bankroll {b:g}\n"
        f"Win chance per round: {r['p_win']*100:.1f}%\n"
        f"Expected result per round: {r['ev_round']:+.2f} (always negative: the house keeps ~3%)\n"
        f"Expected after {r['rounds']} rounds: {r['ev_total']:+.2f}\n"
        f"Simulated: {r['p_ruin']*100:.0f}% chance of going broke within {r['rounds']} rounds, "
        f"average ending bankroll {r['avg_final']:.2f}\n"
        f"{r['losses_to_bust']} straight losses empties you; chance of that streak at any given start: {r['p_streak']*100:.3g}%\n\n"
        "No cash-out target beats the house edge. Only stake what you can afford to lose."
    )


async def post_init(app: Application):
    app.bot_data["web"] = await web.start_web()
    log.info("Dashboard listening on port %s", os.environ.get("PORT", 8080))


async def post_shutdown(app: Application):
    runner = app.bot_data.get("web")
    if runner:
        await runner.cleanup()


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set")
    db.init()
    app = Application.builder().token(token).post_init(post_init).post_shutdown(post_shutdown).build()
    for name, fn in [("start", start), ("help", help_cmd), ("add", add), ("history", history), ("stats", stats), ("risk", risk)]:
        app.add_handler(CommandHandler(name, fn))
    log.info("Bot starting (polling)")
    app.run_polling()


if __name__ == "__main__":
    main()
