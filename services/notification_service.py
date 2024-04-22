import telebot
from db.orm import get_active_trade_processes
from db.config import Session
from services.config import notifier_config

bot = telebot.TeleBot(notifier_config.NOTIFIER_KEY)


def notification_service(context: str = None, session: Session = None) -> None:
    print(session)
    if session:
        context = generate_stat_report(session)
    print(context)
    bot.send_message(
        notifier_config.NOTIFICATION_CHANNEL_ID,
        text=context,
    )
    print('sent')


def generate_stat_report(session: Session) -> str:
    active_trade_processes = get_active_trade_processes(session)
    reports_strings = []
    for active_trade_process in active_trade_processes:
        try:
            f_string = (
                f"Symbol: {active_trade_process.symbol} \n"
                f"Unclosed PnL: {round(active_trade_process.unclosed_pnl, 3)} \n"
                f"Grid PnL: {round(active_trade_process.closed_pnl, 3)} \n"
                f"Total PnL: {round(active_trade_process.total_pnl, 3)} \n\n"
            )
            reports_strings.append(f_string)
        except Exception as e:
            print(e)
            pass

    return " ".join(map(str, reports_strings))
