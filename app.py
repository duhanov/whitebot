from bot import *
import telebot
from telebot import types
import time

import json


#Где находимся в меню
menu_position = ""

#Конфиг
config = json.load(open('config.json'))

#Админы
admins = config["admin_nicknames"].split(',')
#Чаты
chats = []

#Бот телеграм
tg_bot=telebot.TeleBot(config["telegram_token"])


#Торговый бот
bot = Bot(1, "DNT_USDT", 0.1, [29, 29, 29, 29], [10,10,10,10]);



#Меню
def menu_markup():
	print(menu_position)
	print("menu_markup(" + menu_position + ")")
	markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
	#Главное меню
	if menu_position == "":
		markup.add(types.KeyboardButton("Баланс"))
		markup.add(types.KeyboardButton("Account1 -> Account2"))
		markup.add(types.KeyboardButton("Account2 -> Account1"))
	#Кнопка назад для ввода сумм ордеров и времени выкупа, процента
	elif menu_position in ["enter_orders", "enter_times"]:
		markup.add(types.KeyboardButton("Назад"))
	#Кнопка назад для ввода сумм ордеров и времени выкупа, процента
	elif menu_position == "enter_percent":
		markup.add(types.KeyboardButton("0.1"))
		markup.add(types.KeyboardButton("Назад"))

	#Подтверждения Да/Нет для ввода сумм ордеров и времени выкупа, процента
	elif menu_position in ["enter_orders/confirm", "enter_times/confirm", "enter_percent/confirm", "working/cancel"]:
		markup.add(types.KeyboardButton("Да"))
		markup.add(types.KeyboardButton("Нет"))
	#Начать торги
	elif menu_position == "enter_percent/confirm/go":
		markup.add(types.KeyboardButton("Начать"))
		markup.add(types.KeyboardButton("Отмена"))
	#Идут торги
	elif menu_position == "working":
		markup.add(types.KeyboardButton("Остановить"))
	return markup


@tg_bot.message_handler(commands=['start'])
def start_message(message):
	print(message)
	tg_bot.send_message(message.chat.id,'Приветствую, ' + message.from_user.username,reply_markup=menu_markup())

@tg_bot.message_handler(commands=['button'])
def button_message(message):
	markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
	item1=types.KeyboardButton("Кнопка")
	markup.add(item1)		
	tg_bot.send_message(message.chat.id,'Выберите что вам надо',reply_markup=markup)



#Массив с временем в строку с секундами
def arr2secs(arr):
	res = []
	for item in arr:
		res.append(str(item) + " сек")
	return ", ".join(res)

#Массив с временем в строку с секундами
def arr2amounts(arr):
	res = []
	for item in arr:
		res.append(str(item) + " " + bot.tokenName)
	return ", ".join(res)


#Отправка сообщения во все чаты
def send2chats(msg):
	global chats, tg_bot
	for chat_id in chats:
		tg_bot.send_message(chat_id, msg, reply_markup=menu_markup())


def getBalances():
	global bot
	msg = "Аккаунт1:\n"
	msg += str(bot.account1.getBalance("USDT")) + " USDT\n" 
	msg += str(bot.account1.getBalance("DNT")) + " DNT\n\n" 
	msg += "Аккаунт2:\n"
	msg += str(bot.account2.getBalance("USDT")) + " USDT\n" 
	msg += str(bot.account2.getBalance("DNT")) + " DNT\n\n" 
	return msg

#Обработка сообщений бота
@tg_bot.message_handler(content_types='text')
def message_reply(message):
	global menu_position
	global bot
	global minmax
	global admins
	global chats


	#Только для админов
	if message.from_user.username in admins:
		#Сохраняем админский чат
		if not message.chat.id in chats:
			chats.append(message.chat.id)

		#Если бот начал работу
		if menu_position == "working":
			if message.text == "Остановить":
				menu_position = "working/cancel"
				tg_bot.send_message(message.chat.id, "Идут торги... Остановить?", reply_markup=menu_markup())
			else:
				tg_bot.send_message(message.chat.id, "Идут торги... Остановить?", reply_markup=menu_markup())
				return ""
		elif menu_position == "working/cancel":
			if message.text == "Да":
				menu_position = ""
				tg_bot.send_message(message.chat.id, "Торги остановлены!!!", reply_markup=menu_markup())
			else:
				menu_position = "working"
				tg_bot.send_message(message.chat.id, "Идут торги...", reply_markup=menu_markup())
				return ""

		print("Menu:" + menu_position + ", message_reply: " + message.text)
	

		if message.text == "Баланс":
			msg = "Account1:\n"
			msg += str(bot.account1.getBalance("USDT")) + " USDT\n" 
			msg += str(bot.account1.getBalance("DNT")) + " DNT\n\n" 
			msg += "Account2:\n"
			msg += str(bot.account2.getBalance("USDT")) + " USDT\n" 
			msg += str(bot.account2.getBalance("DNT")) + " DNT\n" 
			tg_bot.send_message(message.chat.id, msg,reply_markup=menu_markup())
		elif message.text == "Ордера1":
			orders = bot.account1.getMyOrders(bot.pairName)
			msg = ""
			if orders["success"]:
				msg = "Ордера Account1:\n"
				for order in orders["items"]:
					msg += str(order["orderId"] + ". " + order["market"] + " " + order["side"] + " " + str(order["amount"]) + "/" + str(order["left"]) + " by " + str(order["price"])) + "\n"
			else:
				msg = "Ошибка при получении списка ордеров"
			tg_bot.send_message(message.chat.id, msg, reply_markup=menu_markup())
		elif message.text == "Ордера2":
			orders = bot.account2.getMyOrders(bot.pairName)
			msg = ""
			if orders["success"]:
				msg = "Ордера Account2:\n"
				for order in orders["items"]:
					msg += str(order["orderId"] + ". " + order["market"] + " " + order["side"] + " " + str(order["amount"]) + "/" + str(order["left"]) + " by " + str(order["price"])) + "\n"
			else:
				msg = "Ошибка при получении списка ордеров"
			tg_bot.send_message(message.chat.id, msg, reply_markup=menu_markup())

		#Назад
		elif message.text in ["Назад", "Отмена"]:
			menu_position = ""
			tg_bot.send_message(message.chat.id, "Выберите, что вам надо",reply_markup=menu_markup())
		#Направление торговли
		elif message.text == "Account1 -> Account2":
			#Сохраняем направление торговли
			bot.direction = 1
			#Сохраняем где находимся
			menu_position = "enter_orders"
	

			msg = getBalances() + "\n"
			msg +=  "Через запятую укажите количество токенов для ордеров:"
	
			tg_bot.send_message(message.chat.id, msg,reply_markup=menu_markup())
		#Направление торговли
		elif message.text == "Account2 -> Account1":
			#Сохраняем направление торговли
			bot.direction = 2
			#Сохраняем где находимся
			menu_position = "enter_orders"
	
			msg = getBalances() + "\n"
			msg +=  "Через запятую укажите количество токенов для ордеров:"
	
			tg_bot.send_message(message.chat.id, msg,reply_markup=menu_markup())
		#Ввод через запятую сумм оредеров
		elif menu_position == "enter_orders":
			amounts_strs = message.text.split(',')
			bot.orderAmounts = []
			for amount in amounts_strs:
				bot.orderAmounts.append(float(amount))
			#Проверяем достаточно ли на балансе токенов

			min_amounts = bot.checkMinAmounts()
			print("checkMinAmounts()")
			print(min_amounts)
			if not min_amounts["success"]:
				print("errors")
				tg_bot.send_message(message.chat.id, "Минимальная сумма ордера: 5.05 USDT\n\n" + "\n".join(min_amounts["errors"]) + "\n\nЧерез запятую укажите количество токенов для ордеров",reply_markup=menu_markup())
			elif not bot.checkTokensOnBalance():
				tg_bot.send_message(message.chat.id, "Не хватает токенов на балансе " + bot.accountName1() + "  (нужно " + str(bot.orderAmountsTotal()) + " " + bot.tokenName + ")\n\nЧерез запятую укажите количество токенов для ордеров",reply_markup=menu_markup())
			else:
				minmax = bot.getMinMaxPrice(0)
				check_usdt = bot.checkUSDTBalance(minmax[0], (minmax[0] - minmax[1])/(len(bot.orderAmounts) - 1) )
				if not check_usdt["success"]:
					tg_bot.send_message(message.chat.id, "\n".join(check_usdt["errors"]) + "\n\nЧерез запятую укажите количество токенов для ордеров",reply_markup=menu_markup())
				else:
					menu_position = "enter_orders/confirm"
					tg_bot.send_message(message.chat.id, bot.accountName1() + ". Будут созданы ордера на продажу: " + arr2amounts(bot.orderAmounts),reply_markup=menu_markup())
	
	
		#Повторный ввод сумм ордеров
		elif menu_position == "enter_orders/confirm" and message.text == "Нет":
			#Сохраняем где находимся
			menu_position = "enter_orders"
			tg_bot.send_message(message.chat.id, "Через запятую укажите количество токенов для ордеров",reply_markup=menu_markup())
		#Запоминаем объемы оредров
		elif menu_position == "enter_orders/confirm" and message.text == "Да":
		#Сохраняем где находимся
			menu_position = "enter_times"
			tg_bot.send_message(message.chat.id, "Через запятую время в секундах между покупками",reply_markup=menu_markup())
		#Ввод через запятую времени закупки
		elif menu_position == "enter_times":
			values_strs = message.text.split(',')
			bot.buyTimes = []
			for value in values_strs:
				bot.buyTimes.append(int(value))
			
			#Смотрим чтобы совпадало кол-во ордеров с количеством выкупов
			if(len(bot.orderAmounts) != len(bot.buyTimes)):
				menu_position = "enter_times"
				tg_bot.send_message(message.chat.id, "Введите " + str(len(bot.orderAmounts)) + " значений времени через запятую в секундах между покупками",reply_markup=menu_markup())
			else:
				menu_position = "enter_times/confirm"

				tg_bot.send_message(message.chat.id, bot.accountName2() + ". Выкуп токенов произойдет через: " + arr2secs(bot.buyTimes),reply_markup=menu_markup())
	
		#Повторный ввод времени
		elif menu_position == "enter_times/confirm" and message.text == "Нет":
		#Сохраняем где находимся
			menu_position = "enter_times"
			tg_bot.send_message(message.chat.id, "Через запятую время в секундах между покупками",reply_markup=menu_markup())
		#Запоминаем время выкупа
		elif menu_position == "enter_times/confirm" and message.text == "Да":
			#Сохраняем где находимся
			menu_position = "enter_percent"
			#Цены покупки/продажи
			minmax = bot.getMinMaxPrice(0)
			max_percent = (minmax[1] - minmax[0])*100/minmax[0]
	
			tg_bot.send_message(message.chat.id, "Введите процент для установки границ цены между " + str(minmax[0]) + " USDT - " + str(minmax[1]) + " USDT (не более " + str(round(max_percent ,5)) + "%)", reply_markup=menu_markup())
		#Подтверждение процента
		elif menu_position == "enter_percent":
			bot.percents = float(message.text)
			#Цены покупки/продажи
			minmax = bot.getMinMaxPrice(bot.percents)
	
			if(minmax[0] > minmax[1]):
				minmax = bot.getMinMaxPrice(0)
	
				max_percent = (minmax[1] - minmax[0])*100/minmax[0]
				tg_bot.send_message(message.chat.id, "Введите значение процента меньше " + str(round(delta_percents,5)), reply_markup=menu_markup())
			else:
				menu_position = "enter_percent/confirm" 
				tg_bot.send_message(message.chat.id, "Процент установлен в значение: " + str(bot.percents) + "%.\nОрдера будут установлены в диапазоне: " + str(minmax[0]) + " USDT - " + str(minmax[1]) + " USDT", reply_markup=menu_markup())
		#Повторный ввод времени
		elif menu_position == "enter_percent/confirm" and message.text == "Нет":
			#Сохраняем где находимся
			menu_position = "enter_percent"
			#Цены покупки/продажи
			minmax = bot.getMinMaxPrice(0)
			max_percent = (minmax[1] - minmax[0])*100/minmax[0]
	
			tg_bot.send_message(message.chat.id, "Введите процент для установки границ цены между " + str(minmax[0]) + " USDT - " + str(minmax[1]) + " USDT (не более " + str(round(max_percent ,5)) + "%)", reply_markup=menu_markup())
		#Подтверждение параметров
		elif menu_position == "enter_percent/confirm" and message.text == "Да":
			minmax = bot.getMinMaxPrice(0)
			minmax2 = bot.getMinMaxPrice(bot.percents)
			msg = "Текущая цена покупки токена " + bot.tokenName + ": " +  str(minmax[0]) + " USD\n"
			msg += "Текущая цена продажи токена " + bot.tokenName + ": " +  str(minmax[1]) + " USD\n\n"
			msg += bot.workPreviewText() + "\n\nНачать торги?"

			menu_position = "enter_percent/confirm/go"

			tg_bot.send_message(message.chat.id, msg, reply_markup=menu_markup())
		#Начинаем торги
		elif menu_position == "enter_percent/confirm/go" and message.text == "Начать":
			menu_position = "working"
			#Пока не остановили работу
			print("Started!!!")
			send2chats("Торги запущены!")

			
			#while menu_position in ["working", "working/cancel"]:
			if True:
				print("bot direction: " + str(bot.direction))
				if bot.direction == 1:
					name1 = "Account1"
					name2 = "Account2"
					acc1 = bot.account1
					acc2 = bot.account2
				else:
					name1 = "Account2"
					name2 = "Account1"
					acc1 = bot.account2
					acc2 = bot.account1

				#Создаем ордера
				minmax = bot.getMinMaxPrice(bot.percents)
				price = minmax[0]
				price_delta = (minmax[1] - minmax[0])/(len(bot.orderAmounts) - 1)
				#Создаем ордера на продажу
				n = 0
				for count_tokens in bot.orderAmounts:
					#Выход из торогов
					if not menu_position in ["working", "working/cancel"]:
						break;
					res = acc1.createOrder(bot.pairName, "sell", str(count_tokens), str(round(price,5)))
					if res["success"]:
						item = res["item"]
						send2chats(str(n+1) + "/" + str(len(bot.orderAmounts)) + ". " + name1 + ". Создан ордер на продажу #" + str(item["orderId"]) + " (" + str(count_tokens) + " " + bot.tokenName + " по цене " + str(round(price,5)) + " USDT)")
					else:
						send2chats(str(n+1) + "/" + str(len(bot.orderAmounts)) + ". " + name1 + ". Ошибка при содании ордера на продажу")

					price = price + price_delta
					n += 1

    		    #Создаем ордера на покупку
				price = minmax[0]
				n = 0
				print("step2")
				send2chats("Шаг 2. Выкуп токенов")

				for count_tokens in bot.orderAmounts:
					send2chats("Ждем " + str(bot.buyTimes[n]) + " сек.")
					time.sleep(bot.buyTimes[n])

					#Выход из торогов
					if not menu_position in ["working", "working/cancel"]:
						break;

					res = acc2.createOrder(bot.pairName, "buy", str(count_tokens), str(round(price,5)))
					if res["success"]:
						item = res["item"]
						send2chats(str(n+1) + "/" + str(len(bot.orderAmounts)) + ". " + name2 + ". Создан ордер на покупку #" + str(item["orderId"]) + " (" + str(count_tokens) + " " + bot.tokenName + " по цене " + str(round(price,5)) + " USDT).")
					else:
						send2chats(str(n+1) + "/" + str(len(bot.orderAmounts)) + ". " + name2 + ". Ошибка при содании ордера на покупку")

					price = price + price_delta
					n += 1
				menu_position = ""
				send2chats("Торги завершены!\n\n" + getBalances())

				#if menu_position == "working":
				#	send2chats("Идут торги...")
			print("END!")

tg_bot.infinity_polling()



#bot = Bot(1, "DNT_USDT", 0.1, [29, 29, 29, 29], [10,10,10,10]);

#print("Balances 1:")
#print(str(bot.account1.getBalance("USDT")) + " USDT")
#print(str(bot.account1.getBalance("DNT")) + " DNT")

#print("Balances 2:")
#print(str(bot.account2.getBalance("USDT")) + " USDT")
#print(str(bot.account2.getBalance("DNT")) + " DNT")

#bot.createSellOrders();


print("Complete.");
