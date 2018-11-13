import os
import sys
import random
import logging
import telegram
from time import sleep
from telegram import Bot
from telegram.ext import Updater, CommandHandler, Dispatcher, MessageHandler, \
    Filters, CallbackQueryHandler

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from bot.communication import Communication
from bot.config_reader import retrieve_default
from bot.screening.screening import Screening


class Application:
    """
    The chatbot per se, it contains the Communication class to deal with
    oncoming messages and also handles all Telegram related commands.
    Might soon have a sibling to deal with Facebook.
    """

    def __init__(self, token, train=True, use_watson=True):
        if train:
            self.comm = Communication(use_watson)

        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            level=logging.INFO,
        )
        self.screening = Screening()
        self.logger = logging.getLogger("log")
        self.app = Bot(token)
        self.updater = Updater(token)
        self.dispatcher = self.updater.dispatcher

        start_handler = CommandHandler("start", self.start)
        self.dispatcher.add_handler(start_handler)

        info_handler = CommandHandler("info", self.info)
        self.dispatcher.add_handler(info_handler)

        helpme_handler = CommandHandler("helpme", self.helpme)
        self.dispatcher.add_handler(helpme_handler)

        contatos_handler = CommandHandler("contatos", self.contatos)
        self.dispatcher.add_handler(contatos_handler)

        message_handler = MessageHandler(Filters.text, self.text_message)
        self.dispatcher.add_handler(message_handler)

        self.dispatcher.add_handler(CallbackQueryHandler(self.button_clicked))

        self.dispatcher.add_error_handler(self.error)

    def start(self, bot, update):
        """
        Start command to receive /start message on Telegram.
        @bot = information about the bot
        @update = the user info.
        """
        bot.send_chat_action(
            chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING
        )
        sleep(3.5)
        name = update.message["chat"]["first_name"]
        start_text = (
            f"Olá {name}, eu sou o Rabot.\n" +
            "Um robô bem simpático criado para alegrar seu dia!\n"
        )
        bot.send_message(chat_id=update.message.chat_id, text=start_text)
        start_text = (
            "Se quiser saber mais sobre mim ou meus criadores " +
            "basta digitar `/info` ;)"
        )
        bot.send_message(
            chat_id=update.message.chat_id,
            text=start_text,
            parse_mode=telegram.ParseMode.MARKDOWN,
        )
        start_text = "Agora vamos lá. Em que posso ajudá-lo?"
        bot.send_message(chat_id=update.message.chat_id, text=start_text)
        return 0

    def info(self, bot, update):
        """
        Info command to know more about the developers.
        @bot = information about the bot
        @update = the user info.
        """
        # bot.send_chat_action(
        #     chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING
        # )
        # with open(f"{os.getcwd()}/bot/dialogs/info.md") as info_file:
        #     info_text = info_file.read()
        #     bot.send_message(
        #         chat_id=update.message.chat_id,
        #         text=info_text,
        #         parse_mode=telegram.ParseMode.MARKDOWN,
        #     )
        #     return 0
        # TODO: remove. made this for testing proposes
        self.screening.initial_screen(bot, update)
        return 1

    def helpme(self, bot, update):
        """
        Helpme command to show information about help sources
        for people in critical situations
        """
        bot.send_chat_action(
            chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING
        )
        with open(f"{os.getcwd()}/bot/dialogs/help.md") as help_file:
            helpme_text = help_file.read()
            bot.send_message(
                chat_id=update.message.chat_id,
                text=helpme_text,
                parse_mode=telegram.ParseMode.MARKDOWN,
            )

    def contatos(self, bot, update):
        """
        Shows all contact centers to the bot user
        """
        bot.send_chat_action(
            chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING
        )

        with open(f"{os.getcwd()}/bot/dialogs/contacts.md") as contatos_file:
            contatos_text = contatos_file.read()
            bot.send_message(
                chat_id=update.message.chat_id,
                text=contatos_text,
                parse_mode=telegram.ParseMode.MARKDOWN,
            )

    def text_message(self, bot, update):
        bot.send_chat_action(
            chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING
        )
        message = update.effective_message.text
        update.effective_message.reply_text(str(self.comm.respond(message)))
        return 0

    def button_clicked(self, bot, update):
        # query = update.callback_query
        # query_str = query.data
        self.screening.button_clicked(bot, update)
        return 0

    def error(self, bot, update, error):
        self.logger.warning(f'Update "{update}" caused error "{error}"')
        return 0

    def run(self):
        # Start the Bot
        print("Bot configured. Receiving messages now.")
        self.updater.start_polling()

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        self.updater.idle()
        return 0


if __name__ == "__main__":
    # Variables set on Heroku
    TOKEN = os.environ.get("TOKEN")
    NAME = os.environ.get("NAME")
    # Port is given by Heroku
    PORT = os.environ.get("PORT")
    if TOKEN is not None:
        bot = Application(TOKEN, use_watson=False)
        bot.updater.start_webhook(
            listen="0.0.0.0", port=int(PORT), url_path=TOKEN)
        bot.updater.bot.set_webhook(f"https://{NAME}.herokuapp.com/{TOKEN}")
        bot.updater.idle()

    # Run on local system once detected that it's not on Heroku
    else:
        try:
            token = retrieve_default("TELEGRAM")["token"]
            watson = eval(retrieve_default()["IBM Watson"])
            x = Application(token=token, use_watson=watson).run()
        except FileNotFoundError:
            print("Configuration file not found.")
            sys.exit(1)
