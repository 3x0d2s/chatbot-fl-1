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
    bot.send_document(user_id, data=config.DOC_1)
    bot.send_document(user_id, data=config.DOC_2)


@bot.message_handler(commands=['start'])
def start_handler(message):
    start_text(message.from_user.id)


@bot.message_handler(content_types=['text'])
def change_amount(message):
    msg = message.text.lower()
    msg = msg.replace(' ', '')
    user_id = message.from_user.id
    new_amount = msg.replace('цена', '')
    #
    if user_id == config.ADMIN_ID and 'цена' in msg and new_amount != '':
        value = new_amount + '00'
        change_amount_config(config.PATH_SETTINGS, value)
        bot.send_message(chat_id=user_id,
                         text=f'Успешно! Цена теперь {new_amount} рублей.'
                         )
    elif user_id == config.ADMIN_ID and 'цена' in msg and new_amount == '':
        bot.send_message(chat_id=user_id,
                         text=f'Ошибка формата команды.'
                         )


@bot.message_handler(content_types=['document'])
def change_amount(message):
    print(message.document.file_id)


def start_text(user_id):
    msg = config.START_TEXT
    #
    pay_btn = InlineKeyboardButton(text='Оплатить',
                                   callback_data='start_paymant'
                                   )
    inline_markup = InlineKeyboardMarkup().add(pay_btn)
    #
    bot.send_message(chat_id=user_id,
                     text=msg,
                     parse_mode='markdown',
                     reply_markup=inline_markup
                     )
    send_docs(user_id)


@bot.callback_query_handler(func=lambda call: call.data == 'start_paymant')
def start_payment(call):
    tg_id = call.message.chat.id
    msg = 'Выберите способ оплаты...'
    pay_btn_card = InlineKeyboardButton(text='Картой',
                                        callback_data='card_paymant'
                                        )
    pay_btn_qiwi = InlineKeyboardButton(text='Qiwi',
                                        callback_data='qiwi_paymant'
                                        )
    inline_markup = InlineKeyboardMarkup().add(pay_btn_card).add(pay_btn_qiwi)
    #
    bot.send_message(chat_id=tg_id,
                     text=msg,
                     parse_mode='markdown',
                     reply_markup=inline_markup
                     )


@bot.callback_query_handler(func=lambda call: call.data == 'card_paymant')
def start_card_payment(call):
    tg_id = call.message.chat.id
    amount = get_amount_config(config.PATH_SETTINGS)
    bot.send_invoice(chat_id=tg_id,
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
                     invoice_payload='coupon'
                     )


@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(query):
    bot.answer_pre_checkout_query(pre_checkout_query_id=query.id,
                                  ok=True
                                  )


@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    tg_id = message.chat.id
    successful_payment(tg_id)


@bot.callback_query_handler(func=lambda call: call.data == 'qiwi_paymant')
def start_qiwi_payment(call):
    tg_id = call.message.chat.id
    #
    msg_id = call.message.message_id
    bot.delete_message(tg_id, msg_id)
    #
    random_code = randint(100000, 999999)
    #
    db = paymentDirect('db/payment.db')
    if db.get_payment_code(tg_id) == None:
        db.add_payment_to_stack(tg_id, random_code)
    else:
        db.delete_payment(tg_id)
        db.add_payment_to_stack(tg_id, random_code)
    db.close()
    #
    btn_1 = InlineKeyboardButton(text='Проверить оплату',
                                 callback_data='check_payment'
                                 )
    btn_2 = InlineKeyboardButton(text='Отмена',
                                 callback_data='cancel'
                                 )
    inline_markup = InlineKeyboardMarkup().add(btn_1).add(btn_2)
    #
    amount = int(get_amount_config('config/settings.ini')) // 100
    #
    msg = f'Информация об оплате\n🥝 QIWI-кошелек: +{config.QIWI_ACCOUNT}\n📝 Комментарий к переводу: {random_code}\n💰 Сумма для оплаты: {amount} руб.\n*Внимание*\nЗаполняйте номер телефона и комментарий при переводе внимательно!\nПосле перевода нажмите кнопку *Проверить оплату*.\nОплачивая, Вы соглашаетесь с пользовательским соглашением и политикой конфиденциальности.'
    bot.send_message(chat_id=tg_id,
                     text=msg,
                     parse_mode='markdown',
                     reply_markup=inline_markup
                     )


@bot.callback_query_handler(func=lambda call: call.data == 'check_payment')
def check_payment(call):
    db = paymentDirect('db/payment.db')
    user_id = call.from_user.id
    #
    code = db.get_payment_code(user_id)[0]
    #
    isBalanceReplenished = False
    #
    amount_true = int(get_amount_config(config.PATH_SETTINGS)) // 100
    #
    req = get_qiwi_data()
    #
    for i in req['data']:
        step_code = i['comment']
        amount = i['sum']['amount']
        if step_code == code and amount == amount_true:
            isBalanceReplenished = True
            break
    #
    if isBalanceReplenished == True:
        db.delete_payment(user_id)
        successful_payment(user_id)
    else:
        bot.send_message(chat_id=user_id,
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


@bot.callback_query_handler(func=lambda call: call.data == 'cancel')
def cancel_payment(call):
    tg_id = call.message.chat.id
    msg_id = call.message.message_id
    bot.delete_message(chat_id=tg_id, message_id=msg_id)
    #
    db = paymentDirect('db/payment.db')
    db.delete_payment(tg_id)
    db.close()
    #
    pay_btn_card = InlineKeyboardButton(text='Картой',
                                        callback_data='card_paymant'
                                        )
    pay_btn_qiwi = InlineKeyboardButton(text='Qiwi',
                                        callback_data='qiwi_paymant'
                                        )
    inline_markup = InlineKeyboardMarkup().add(pay_btn_card).add(pay_btn_qiwi)
    #
    msg = 'Выберите способ оплаты...'
    bot.send_message(chat_id=tg_id, text=msg, reply_markup=inline_markup)


def successful_payment(user_id):
    url_btn = InlineKeyboardButton(text='Перейти в канал...',
                                   url=config.PRIVATE_URL
                                   )
    inline_markup = InlineKeyboardMarkup().add(url_btn)
    #
    bot.send_message(chat_id=user_id,
                     text='Платёж прошёл, спасибо за оплату!',
                     reply_markup=inline_markup
                     )


# RUN
if __name__ == '__main__':
    # Create a Data Base from a dump file if db.db isn't exists
    if not os.path.isfile(config.PATH_DB):
        createBD_FromDump(config.PATH_DB, config.PATH_DUMP)
    bot.polling(none_stop=True)
