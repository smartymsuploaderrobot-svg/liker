import os
import sys
import time
from threading import Thread

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import inject
from flask import Flask
from telebot import apihelper
from tengi import App

from liker.setup.dependencies import bind_app_dependencies
from liker.setup.daemons import create_daemon_instances

# Required for middleware
apihelper.ENABLE_MIDDLEWARE = True

# Flask app for Render port binding
flask_app = Flask(__name__)

@flask_app.route('/health')
def health():
    return 'OK', 200

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)


@inject.autoparams()
def main():
    inject.configure(bind_app_dependencies)
    create_daemon_instances()

    from tengi import TelegramBot
    bot = inject.instance(TelegramBot).bot

    # Fix 409: delete webhook and wait for old instance to die
    for attempt in range(5):
        try:
            bot.delete_webhook(drop_pending_updates=True)
            break
        except Exception:
            time.sleep(3)
    time.sleep(5)  # extra wait for old instance to fully stop

    # Fix em dash: Telegram converts "--" to "—"
    @bot.middleware_handler(update_types=['message'])
    def fix_em_dash(bot_instance, message):
        if message.text:
            message.text = message.text \
                .replace('\u2014', '--') \
                .replace('\u2013', '--') \
                .replace('\u2012', '--')

    # Flask in background thread
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Bot in main thread
    app = inject.instance(App)
    app.run()


if __name__ == '__main__':
    main()
