# -*- coding: utf8 -*-
import requests
import json
import sqlite3
from random import randint
#
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
#
from payment_request import paymentDirect
from config_pars import *
import config.config as config
#
bot = telebot.TeleBot(config.BOT_TOKEN)


bot.message_handler(content_types=['document'])


def ddd(msg):
    print(msg.document.file_id)


def createBD_FromDump(path_db, path_dump):
    cur = sqlite3.connect(path_db)
    f = open(path_dump, 'r', encoding='utf-8')
    dump = f.read()
    cur.executescript(dump)


def send_docs(user_id):
    # bot.send_document(user_id, data=config.DOC_1)
    # bot.send_document(user_id, data=config.DOC_2)
    pass


@bot.message_handler(commands=['start'])
def start_handler(message):
    start_text(message.from_user.id)


@bot.message_handler(content_types=['text'])
def change_amount(message):
    msg = message.text.lower().replace(' ', '')

    user_id = message.from_user.id

    product_id: str = msg[0]
    new_amount: str = msg[1:].replace('цена', '')

    if user_id == config.ADMIN_ID and 'цена' in msg and new_amount != '' and product_id.isnumeric() == True:
        value = new_amount + '00'

        change_amount_config(config.PATH_SETTINGS, product_id, value)

        bot.send_message(
            chat_id=user_id,
            text=f'Успешно! Цена теперь {new_amount} рублей.'
        )
    elif user_id == config.ADMIN_ID and 'цена' in msg:
        bot.send_message(
            chat_id=user_id,
            text=f'Ошибка формата команды.'
        )


@bot.message_handler(content_types=['document'])
def change_amount(message):
    print(message.document.file_id)


def start_text(user_id):
    msg = config.START_TEXT
    #
    pay_btn = InlineKeyboardButton(text='Оплатить',
                                   callback_data='choose_product'
                                   )
    inline_markup = InlineKeyboardMarkup().add(pay_btn)
    #
    bot.send_message(chat_id=user_id,
                     text=msg,
                     parse_mode='markdown',
                     reply_markup=inline_markup
                     )
    send_docs(user_id)


@bot.callback_query_handler(func=lambda call: call.data == 'choose_product')
def start_payment(call):
    tg_id = call.message.chat.id
    msg = 'Выберите вариант...'

    amounts = get_amount_config(config.PATH_SETTINGS)

    inline_markup = InlineKeyboardMarkup()
    for product in config.PRODUCTS:
        product_id = product["id"]
        product_name = product["name"]
        product_amount = amounts[product_id-1]["amount"][:-2]

        product = InlineKeyboardButton(text=f"{product_name} - {product_amount} р.",
                                       callback_data=f'product_{product["id"]}'
                                       )
        inline_markup.add(product)

    bot.send_message(
        chat_id=tg_id,
        text=msg,
        parse_mode='markdown',
        reply_markup=inline_markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("product_"))
def start_payment(call):
    product_id = call.data[8:]

    tg_id = call.message.chat.id

    inline_markup = InlineKeyboardMarkup()
    pay_btn_card = InlineKeyboardButton(
        text='Картой',
        callback_data=f'card_paymant_{product_id}'
    )
    pay_btn_qiwi = InlineKeyboardButton(
        text='Qiwi',
        callback_data=f'qiwi_paymant_{product_id}'
    )
    inline_markup.add(pay_btn_card)
    inline_markup.add(pay_btn_qiwi)

    msg = 'Выберите способ оплаты...'
    bot.send_message(chat_id=tg_id,
                     text=msg,
                     parse_mode='markdown',
                     reply_markup=inline_markup
                     )


@bot.callback_query_handler(func=lambda call: call.data.startswith("card_paymant_"))
def start_card_payment(call):
    product_id = int(call.data[13:])

    tg_id = call.message.chat.id
    amount = get_amount_config(config.PATH_SETTINGS)[product_id-1]["amount"]

    msg_id = call.message.message_id
    bot.delete_message(tg_id, msg_id)

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(
        text="Оплатить",
        pay=True)
    )
    keyboard.add(InlineKeyboardButton(
        text="Отмена",
        callback_data=f'product_{product_id}')
    )

    bot.send_invoice(
        chat_id=tg_id,
        title='Доступ к сказкам',
        description=config.INVOICE_DESCRIPTION_TEXT,
        provider_token=config.PROVIDER_TOKEN,
        currency='RUB',
        photo_url=None,
        need_phone_number=False,
        need_email=False,
        is_flexible=False,
        prices=[LabeledPrice(label='Доступ к сказкам',
                             amount=int(amount))],
        start_parameter='start_parameter',
        invoice_payload=str(product_id),
        reply_markup=keyboard
    )


@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(query):
    bot.answer_pre_checkout_query(
        pre_checkout_query_id=query.id,
        ok=True
    )


@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    tg_id = message.chat.id
    product_id = int(message.successful_payment.invoice_payload)
    successful_payment(tg_id, product_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("qiwi_paymant_"))
def start_qiwi_payment(call):
    product_id = int(call.data[13:])

    tg_id = call.message.chat.id

    msg_id = call.message.message_id
    bot.delete_message(tg_id, msg_id)

    random_code = randint(100000, 999999)
    db = paymentDirect('db/payment.db')
    if db.get_payment_code(tg_id) == None:
        db.add_payment_to_stack(tg_id, random_code)
    else:
        db.delete_payment(tg_id)
        db.add_payment_to_stack(tg_id, random_code)
    db.close()

    inline_markup = InlineKeyboardMarkup()
    btn_1 = InlineKeyboardButton(
        text='Проверить оплату',
        callback_data=f'check_payment_{product_id}'
    )
    btn_2 = InlineKeyboardButton(
        text='Отмена',
        callback_data=f'product_{product_id}'
    )
    inline_markup.add(btn_1)
    inline_markup.add(btn_2)

    amount = get_amount_config(config.PATH_SETTINGS)[
        product_id-1]["amount"][:-2]

    msg = f'Информация об оплате\n🥝 QIWI-кошелек: +{config.QIWI_ACCOUNT}\n' \
        f'📝 Комментарий к переводу: {random_code}\n💰 Сумма для оплаты: {amount} руб.\n' \
        '*Внимание*\nЗаполняйте номер телефона и комментарий при переводе внимательно!\n' \
        'После перевода нажмите кнопку *Проверить оплату*.\nОплачивая, Вы соглашаетесь с ' \
        'пользовательским соглашением и политикой конфиденциальности.'
    bot.send_message(
        chat_id=tg_id,
        text=msg,
        parse_mode='markdown',
        reply_markup=inline_markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("check_payment_"))
def check_payment(call):
    product_id = int(call.data[14:])

    db = paymentDirect('db/payment.db')
    user_id = call.from_user.id
    code = db.get_payment_code(user_id)[0]

    isBalanceReplenished = False

    amount_true = get_amount_config(config.PATH_SETTINGS)[
        product_id - 1]["amount"][:-2]

    req = get_qiwi_data()
    for i in req['data']:
        step_code = i['comment']
        amount = i['sum']['amount']
        if step_code == code and amount == amount_true:
            isBalanceReplenished = True
            break

    if isBalanceReplenished == True:
        db.delete_payment(user_id)
        successful_payment(user_id, product_id)
    else:
        bot.send_message(
            chat_id=user_id,
            text="*Ошибка:* платежа не обнаружено.",
            parse_mode="markdown",
        )


def get_qiwi_data():
    s = requests.Session()
    s.headers['authorization'] = 'Bearer ' + config.QIWI_TOKEN
    parameters = {'rows': '50'}
    h = s.get('https://edge.qiwi.com/payment-history/v1/persons/' +
              config.QIWI_ACCOUNT + '/payments', params=parameters)
    h = h.text
    # Если выдает ошибку, возможно истек срок действия токена киви
    return json.loads(h)


def successful_payment(user_id, product_id: int):
    url_btn = InlineKeyboardButton(text='Перейти в канал...',
                                   url=config.PRODUCTS[product_id-1]["url"]
                                   )
    inline_markup = InlineKeyboardMarkup().add(url_btn)
    #
    bot.send_message(
        chat_id=user_id,
        text='✅ Платёж прошёл, спасибо за оплату!',
        reply_markup=inline_markup
    )


# RUN
if __name__ == '__main__':
    # Create a Data Base from a dump file if db.db isn't exists
    if not os.path.isfile(config.PATH_DB):
        createBD_FromDump(config.PATH_DB, config.PATH_DUMP)
    bot.polling(none_stop=True)
