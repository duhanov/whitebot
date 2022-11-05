from bot import *
import telebot
from telebot import types
import time

import json

import re

#Где находимся в меню
menu_position = ""

#Конфиг
config = json.load(open('config.json'))

#Юзеры
users = json.load(open('users.json'))
print("load users:")
print(users)

#Админы
admins = config["admin_nicknames"].split(',')
#Чаты
chats = []

#Бот телеграм
tg_bot=telebot.TeleBot(config["telegram_token"])


#Торговый бот
bot = Bot(1, "DNT_USDT", 0.1, [29, 29, 29, 29], [29, 29, 29, 29], [10,10,10,10]);



#Меню
def menu_markup():
	print(menu_position)
	print("menu_markup(" + menu_position + ")")
	markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
#	markup=types.ReplyKeyboardMarkup(one_time_keyboard=True)

	#Главное меню
	if menu_position == "":
		#markup = types.ReplyKeyboardMarkup([
#		markup.add([types.KeyboardButton("Баланс"), types.KeyboardButton("Ордера")])
#		markup.add(types.KeyboardButton("Баланс"))
		#markup.add(["Баланс", "Ордера"])

#		markup.add([
#			["Баланс", "Ордера"], 
#			"Account1 <- Account2",
#			"Account2 <- Account1",
#			"Account1 -> Account2",
#			"Account2 -> Account1"
#		])

		markup.add(types.KeyboardButton("Баланс"))
		markup.add(types.KeyboardButton("Ордера"))
		markup.add(types.KeyboardButton("Пользователи"))
		markup.add(types.KeyboardButton("Account1 SELL"))
		markup.add(types.KeyboardButton("Account2 SELL"))
		markup.add(types.KeyboardButton("Account1 BUY"))
		markup.add(types.KeyboardButton("Account2 BUY"))
		markup.add(types.KeyboardButton("Account1 <- Account2"))
		markup.add(types.KeyboardButton("Account2 <- Account1"))

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
	elif menu_position in ["orders/delall", "enter_prices/confirm", "users/del", "users/add/confirm", "enter_orders/confirm", "enter_orders2/confirm", "enter_times/confirm", "enter_percent/confirm", "working/cancel"]:
		markup.add(types.KeyboardButton("Да"))
		markup.add(types.KeyboardButton("Нет"))
	#Начать торги
	elif menu_position == "go":
		markup.add(types.KeyboardButton("Начать"))
		markup.add(types.KeyboardButton("Отмена"))
	#Идут торги
	elif menu_position == "working":
		markup.add(types.KeyboardButton("Остановить"))
	#Пользователи
	elif menu_position == "users":
		markup.add(types.KeyboardButton("-Назад"))
		markup.add(types.KeyboardButton("Добавить пользователя"))
		for user in users:
			markup.add(types.KeyboardButton("@" + user))

	elif menu_position == "orders":
		markup.add(types.KeyboardButton("Удалить все ордера"))
		markup.add(types.KeyboardButton("Назад"))
	else:
		markup.add(types.KeyboardButton("Назад"))
	return markup


@tg_bot.message_handler(commands=['start'])
def start_message(message):
	global users
	global admins

	menu_position = ""

	#Для пользователей	
	if message.from_user.username in users:
		#Сохраняем чат_id
		users[message.from_user.username] = message.chat.id
		save_users()

		tg_bot.send_message(message.chat.id, '@' + message.from_user.username + ' вы были подписаны!')

	#Для админов


	if message.from_user.username in admins:
		tg_bot.send_message(message.chat.id,'Приветствую, @' + message.from_user.username,reply_markup=menu_markup())





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
	global chats
	global tg_bot
	global users
	#Рассылка админам
	for chat_id in chats:
		tg_bot.send_message(chat_id, msg, reply_markup=menu_markup())

	#Рассылка юзерам
	for chat_id in users.keys():
		if users[chat_id] != "":
			tg_bot.send_message(users[chat_id], msg, reply_markup=menu_markup())


def getBalance1():
	global bot
	msg = "Аккаунт1:\n"
	msg += str(bot.account1.getBalance("USDT")) + " USDT\n" 
	msg += str(bot.account1.getBalance("DNT")) + " DNT\n\n" 
	return msg	

def getBalance2():
	msg = "Аккаунт2:\n"
	msg += str(bot.account2.getBalance("USDT")) + " USDT\n" 
	msg += str(bot.account2.getBalance("DNT")) + " DNT\n\n" 
	return msg

def getBalances():
	return getBalance1() + getBalance2()


def enterPrices(message):
	global bot
	global menu_position
	global tg_bot


	print("bot mode=" + bot.mode)
	#Сохраняем где находимся
	if bot.mode in ["1->2", "2->1", "1<-2", "2<-1"]:		
		#Ввод цен через процент
		#Цены покупки/продажи
		minmax = bot.getMinMaxPrice(0)
		max_percent = (minmax[1] - minmax[0])*100/minmax[0]

		menu_position = "enter_percent"
		msg = getBalances() + "Введите процент для установки границ цены между " + str(minmax[0]) + " USDT - " + str(minmax[1]) + " USDT (не более " + str(round(max_percent ,5)) + "%)"
	else:
		#Ввод цен через 
		menu_position = "enter_prices"


		msg = stock_prices_msg() + "Через пробел введите диапазон цен ордеров:"

	tg_bot.send_message(message.chat.id, msg,reply_markup=menu_markup())

	





user_for_add = ""


def save_users():
	global users
	with open('users.json', 'w') as f:
		json.dump(users, f)



#Ввод цен через процент
def node_prices_percent(message, next_menu):
	global menu_position
	global tg_bot
	global bot


	r = True

	#Ввод процента
	if menu_position == "enter_percent":
		bot.percents = float(message.text)
		#Цены покупки/продажи
		minmax = bot.getMinMaxPrice(bot.percents)

		if(minmax[0] > minmax[1]):
			minmax = bot.getMinMaxPrice(0)

			max_percent = (minmax[1] - minmax[0])*100 / minmax[0]
			tg_bot.send_message(message.chat.id, "Введите значение процента меньше " + str(round(delta_percents,5)), reply_markup=menu_markup())
		else:
			menu_position = "enter_percent/confirm" 
			tg_bot.send_message(message.chat.id, "Процент установлен в значение: " + str(bot.percents) + "%.\nОрдера будут установлены в диапазоне: " + str(minmax[0]) + " USDT - " + str(minmax[1]) + " USDT", reply_markup=menu_markup())
	

	#Повторный ввод проценда
	elif menu_position == "enter_percent/confirm" and message.text == "Нет":
		#Сохраняем где находимся
		menu_position = "enter_percent"
		#Цены покупки/продажи
		minmax = bot.getMinMaxPrice(0)
		max_percent = (minmax[1] - minmax[0])*100/minmax[0]

		tg_bot.send_message(message.chat.id, "Введите процент для установки границ цены между " + str(minmax[0]) + " USDT - " + str(minmax[1]) + " USDT (не более " + str(round(max_percent ,5)) + "%)", reply_markup=menu_markup())
	#Подтверждение параметров
	elif menu_position == "enter_percent/confirm" and message.text == "Да":

		menu_position = next_menu[0]
		msg =  next_menu[1]
		tg_bot.send_message(message.chat.id, msg, reply_markup=menu_markup())
	else:
		r = False

	return r


#Ввод цен через процент
def node_prices_manual(message, next_menu):
	global menu_position
	global tg_bot
	global bot

	r = True

	if menu_position == "enter_prices":
		minmax = message.text.replace("  ", " ").split(" ")
		#Ввели два значения
		if len(minmax) != 2:
			msg = stock_prices_msg() + "Через пробел введите диапазон цен ордеров:"
		else:
			bot.minmax[0] = float(minmax[0])
			bot.minmax[1] = float(minmax[1])
			if bot.minmax[0] >= bot.minmax[1]:
				msg = "Вторая цена должна быть больше первой!\n\n" + stock_prices_msg() + "Через пробел введите диапазон цен ордеров:"
			else:
				menu_position = "enter_prices/confirm"
				msg =  "Минимальная цена ордера: " + str(bot.minmax[0]) + "\nМаксимальная цена ордера: " +str(bot.minmax[1])

		
		tg_bot.send_message(message.chat.id, msg, reply_markup=menu_markup())

	#Подтверждение - нет
	elif menu_position == "enter_prices/confirm" and message.text == "Нет":
		menu_position = "enter_prices"
		tg_bot.send_message(message.chat.id, "Через пробел укажите минимальну и максимальную цену оредеров", reply_markup=menu_markup())
	#Подтверждение - Да
	elif menu_position == "enter_prices/confirm" and message.text == "Да":
		menu_position = next_menu[0]
		tg_bot.send_message(message.chat.id, next_menu[1], reply_markup=menu_markup())

	else:
		r = False

	return r

#Меню с вводом диапазона цен
def node_prices(message):
	global menu_position
	global tg_bot
	global bot


	r = False



	next_menu = ["enter_orders", ""]

	next_menu[1] = "Через запятую укажите количество токенов для ордеров на " + bot.what("продажу", "покупку")+ ":"

	#Ввод рукчной цен
	if bot.mode in ["1->", "2->", "1<-", "2<-"]:
		r = node_prices_manual(message, next_menu)		
	#Ввод через процент
	elif bot.mode in ["1->2", "1<-2", "2->1", "2<-1"]:
		r =  node_prices_percent(message, next_menu)

	return r


def stock_prices_msg():
	minmax = bot.getMinMaxPrice(0)
	msg = "Биржевая цена покупки токена " + bot.tokenName + ": " +  str(minmax[0]) + " USD\n"
	msg += "Биржевая цена продажи токена " + bot.tokenName + ": " +  str(minmax[1]) + " USD\n\n"
	return msg

#Меню с пользователям
def node_users(message):
	global users
	global menu_position
	global tg_bot
	global user_for_add
	r = True

	#Пользователи
	if menu_position == "" and message.text == "Пользователи":
		msg = "Выберите действие или Пользователя"
		menu_position = "users"	
		print("change menu_position to " + menu_position)

		tg_bot.send_message(message.chat.id, msg, reply_markup=menu_markup())

	#Добавление Пользователя
	elif menu_position =="users" and message.text == "Добавить пользователя":
		menu_position = "users/add"
		msg = "Введите имя пользователя для добавления"
		tg_bot.send_message(message.chat.id, msg, reply_markup=menu_markup())
	#Удаление Пользователя  - выбрали
	elif menu_position =="users" and re.match(r'^\@.+', message.text):# /\@.+/, message.text):
		print("addd user")
		menu_position = "users/del"
		msg = "! Удалить пользователя @" + message.text.replace("@", "") + " ?"
		#Запоминаем для Добавления		
		user_for_add = message.text.replace("@", "")
		tg_bot.send_message(message.chat.id, msg, reply_markup=menu_markup())

	#Удаление Пользователя Подтверждение
	elif menu_position =="users/del" and message.text == "Нет":
		menu_position = "users"
		msg = "Выберите действие или Пользователя"
		tg_bot.send_message(message.chat.id, msg, reply_markup=menu_markup())

	#Удаление Пользователя - ДА
	elif menu_position =="users/del" and message.text == "Да":
		menu_position = "users"
		#Удаляем пользователя
		del users[user_for_add]
		save_users()
		msg = "Пользователь @" + user_for_add + " удален!"
		tg_bot.send_message(message.chat.id, msg, reply_markup=menu_markup())

	#Подтверждения добавления
	elif menu_position =="users/add" :
		menu_position = "users/add/confirm"
		msg = "Добавить пользователя @" + message.text.replace("@", "") + " ?"
		user_for_add = message.text.replace("@", "")
		tg_bot.send_message(message.chat.id, msg, reply_markup=menu_markup())
	# Добавление пользователя
	elif menu_position =="users/add/confirm" and message.text == "Нет":
		menu_position = "users/add"
		msg = "Введите имя пользователя для добавления"
		
		tg_bot.send_message(message.chat.id, msg, reply_markup=menu_markup())

	# Добавление пользователя
	elif menu_position =="users/add/confirm" and message.text == "Да":
		#фЫ
		menu_position = "users"
		if not user_for_add in users:
			users[user_for_add] = ""
			save_users()

		msg = "Пользователь @" +user_for_add + " добавлен!"
		tg_bot.send_message(message.chat.id, msg, reply_markup=menu_markup())
	else:
		r = False

	return r

def deleteAllOrders(message):
	global bot
	global tg_bot

	msg = ""

	orders = bot.account1.getMyOrders(bot.pairName)
	if orders["success"]:
		account_orders = ""
		for order in orders["items"]:
			res = bot.account1.cancelOrder(bot.pairName, order["orderId"])
			if res["success"]:
				msg += "Удален ордер " + str(order["orderId"]) + "\n"
			else:
				msg += "Ошибка при удалении ордера " + str(order["orderId"]) + "\n"
	else:
		msg += "Ошибка при получении списка ордеров Account1" + "\n"

	orders = bot.account2.getMyOrders(bot.pairName)
	if orders["success"]:
		account_orders = ""
		for order in orders["items"]:
			res = bot.account2.cancelOrder(bot.pairName, order["orderId"])
			if res["success"]:
				msg += "Удален ордер " + str(order["orderId"]) + "\n"
			else:
				msg += "Ошибка при удалении ордера " + str(order["orderId"]) + "\n"
	else:
		msg += "Ошибка при получении списка ордеров Account2" + "\n"

	tg_bot.send_message(message.chat.id, msg, reply_markup=menu_markup())



def showOrders(message):
	global menu_position
	global bot
	global tg_bot

	menu_position = "orders"
	msg = ""
	#Ордера аккаунта 2
	orders = bot.account1.getMyOrders(bot.pairName)
	if orders["success"]:
		account_orders = ""
		for order in orders["items"]:
			account_orders += str(order["orderId"]) + ". " + order["market"] + " " + order["side"] + " " + order["amount"] + "/" + order["left"] + " by " + order["price"] + "\n"
		if account_orders == "":
			account_orders = "-Нет"
		msg = "Ордера Account1:\n" + account_orders
		

	else:
		msg = "Ошибка при получении списка ордеров"
	
	#Ордера аккаунта 2
	orders = bot.account2.getMyOrders(bot.pairName)
	if orders["success"]:
		account_orders = ""
		for order in orders["items"]:
			account_orders += str(order["orderId"]) + ". " + order["market"] + " " + order["side"] + " " + order["amount"] + "/" + order["left"] + " by " + order["price"] + "\n"
		if account_orders == "":
			account_orders = "-Нет"

		msg += "\n\nОрдера Account2:\n" + account_orders
	else:
		msg = "Ошибка при получении списка ордеров"
	
	tg_bot.send_message(message.chat.id, msg, reply_markup=menu_markup())

def node_enter_orders(message):
	global menu_position
	global bot

	r = True
	if menu_position in ["enter_orders", "enter_orders2"]:
		amounts_strs = message.text.split(',')
		if menu_position == "enter_orders":
			bot.orderAmounts = []
			for amount in amounts_strs:
				bot.orderAmounts.append(float(amount))
			min_amounts = bot.checkMinAmounts(1)
			check_tokens = bot.checkTokensOnBalance(1)
		else:
			bot.orderAmounts2 = []
			for amount in amounts_strs:
				bot.orderAmounts2.append(float(amount))
			min_amounts = bot.checkMinAmounts(2)
			check_tokens = bot.checkTokensOnBalance(2)
		#Проверяем достаточно ли на балансе токенов

		print("checkMinAmounts()")
		print(min_amounts)
		if not min_amounts["success"]:
			print("errors")
			tg_bot.send_message(message.chat.id, "Минимальная сумма ордера: 5.05 USDT\n\n" + "\n".join(min_amounts["errors"]) + "\n\nЧерез запятую укажите количество токенов для ордеров",reply_markup=menu_markup())
		elif not check_tokens["success"]:
			tg_bot.send_message(message.chat.id, "Ошибка\n" + "\n".join(check_tokens["errors"]) + "\n\nЧерез запятую укажите количество токенов для ордеров",reply_markup=menu_markup())
		else:
#				minmax = bot.getMinMaxPrice(0)
#				check_usdt = bot.checkUSDTBalance(minmax[0], (minmax[0] - minmax[1])/(len(bot.orderAmounts) - 1) )
			if menu_position == "enter_orders":
				check_usdt = bot.checkUSDTBalance(1)
			else:
				check_usdt = bot.checkUSDTBalance(2)
			if not check_usdt["success"]:
				tg_bot.send_message(message.chat.id, "Ошибка2\n" + "\n".join(check_usdt["errors"]) + "\n\nЧерез запятую укажите количество токенов для ордеров",reply_markup=menu_markup())
			#Проверяем соотвествие количества токенов в ордерах в шагах 1 и 2
			elif menu_position == "enter_orders2" and bot.orderAmountsTotal() != bot.orderAmountsTotal2():
				menu_position = "enter_orders2"
				tg_bot.send_message(message.chat.id, "Суммы токенов не совпадают (" + str(bot.orderAmountsTotal()) + " <> " + str(bot.orderAmountsTotal2()) + "). Через запятую укажите количество токенов для ордеров на " + bot.what("покупку", "продажу"),reply_markup=menu_markup())
			else:
				menu_position += "/confirm"

				if menu_position == "enter_orders/confirm":
					msg = bot.accountName1() + ". Будут созданы ордера на " + bot.what("продажу", "покупку") + ": " + arr2amounts(bot.orderAmounts)
				else:
					msg = bot.accountName2() + ". Будут созданы ордера на " + bot.what("покупку", "продажу") + ": " + arr2amounts(bot.orderAmounts2)
				
				tg_bot.send_message(message.chat.id, msg,reply_markup=menu_markup())


	#Повторный ввод сумм ордеров
	elif menu_position in ["enter_orders/confirm", "enter_orders2/confirm"] and message.text == "Нет":
		#Сохраняем где находимся
		menu_position = menu_position.replace("/confirm", "")
		if menu_position == "enter_orders":
			msg = "Через запятую укажите количество токенов для ордеров на " + bot.what("продажу", "покупку")
		else:
			msg = "Через запятую укажите количество токенов для ордеров на " + bot.what("покупку", "продажу")

		tg_bot.send_message(message.chat.id, msg,reply_markup=menu_markup())
	#Запоминаем объемы оредров
	elif menu_position == "enter_orders/confirm" and message.text == "Да":
		print("mode=" + bot.mode)
		if bot.mode in ["1->", "2->", "1<-", "2<-"]:
			menu_position = "go"
			msg = stock_prices_msg()
			msg += bot.workPreviewText() + "\n\nНачать торги?"
		else:
			menu_position = "enter_orders2"
			msg = "Через запятую укажите количество токенов для ордеров на " + bot.what("покупку", "продажу")
		tg_bot.send_message(message.chat.id, msg,reply_markup=menu_markup())
	#Запоминаем объемы оредров
	elif menu_position == "enter_orders2/confirm" and message.text == "Да":
		menu_position = "enter_times"
		tg_bot.send_message(message.chat.id, "Через запятую укажите время в секундах между " + bot.what("покупками", "продажами"),reply_markup=menu_markup())
	else:
		r = False
	
	return r


#Обработка сообщений бота
@tg_bot.message_handler(content_types='text')
def message_reply(message):
	global menu_position
	global bot
	global minmax
	global admins
	global chats
	global users
	global user_for_add

	print("message_reply()")
	print("menu_position=" + menu_position)
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
	




		#Назад
		if message.text in ["Назад", "Отмена", "-Назад"]:
			menu_position = ""
			tg_bot.send_message(message.chat.id, "Выберите, что вам надо",reply_markup=menu_markup())
			return
		#Меню с пользователями
		elif node_users(message):
			print("node_users - RUN")
		#Ввод оредров
		elif node_enter_orders(message):
			print("node_enter_orders - RUN")
		#Нода с вводом цены
		elif node_prices(message):
			print("node_prices - RUN")
		
		
		#Баланс
		elif message.text == "Баланс" and menu_position == "":
			msg = "Account1:\n"
			msg += str(bot.account1.getBalance("USDT")) + " USDT\n" 
			msg += str(bot.account1.getBalance("DNT")) + " DNT\n\n" 
			msg += "Account2:\n"
			msg += str(bot.account2.getBalance("USDT")) + " USDT\n" 
			msg += str(bot.account2.getBalance("DNT")) + " DNT\n" 
			tg_bot.send_message(message.chat.id, msg,reply_markup=menu_markup())
		


		#Ордера		
		elif message.text == "Ордера" and menu_position == "":
			showOrders(message)


	
		#Направление торговли
		elif message.text == "Account1 -> Account2" and menu_position == "":
			#Сохраняем направление торговли
			bot.mode = "1->2"
			enterPrices(message)
		#Направление торговли
		elif message.text == "Account2 -> Account1" and menu_position == "":
			#Сохраняем направление торговли
			bot.mode = "2->1"
			enterPrices(message)
		#Направление торговли
		elif message.text == "Account1 <- Account2" and menu_position == "":
			#Сохраняем направление торговли
			bot.mode = "1<-2"
			enterPrices(message)
		#Направление торговли
		elif message.text == "Account2 <- Account1" and menu_position == "":
			#Сохраняем направление торговли
			bot.mode = "2<-1"
			enterPrices(message)
		#Направление торговли
		elif message.text == "Account1 SELL" and menu_position == "":
			#Сохраняем направление торговли
			bot.mode = "1->"
			tg_bot.send_message(message.chat.id, getBalance1())
			enterPrices(message)
		#Направление торговли
		elif message.text == "Account2 SELL" and menu_position == "":			
			#Сохраняем направление торговли
			bot.mode = "2->"
			tg_bot.send_message(message.chat.id, getBalance2())
			enterPrices(message)
		#Направление торговли
		elif message.text == "Account1 BUY" and menu_position == "":
			#Сохраняем направление торговли
			bot.mode = "1<-"
			tg_bot.send_message(message.chat.id, getBalance1())
			enterPrices(message)
		elif message.text == "Account2 BUY" and menu_position == "":
			#Сохраняем направление торговли
			bot.mode = "2<-"
			tg_bot.send_message(message.chat.id, getBalance2())
			enterPrices(message)


		elif menu_position == "orders" and message.text == "Удалить все ордера":
			menu_position = "orders/delall"
			msg = "Вы действительно хотите удалить все ордера?"
			tg_bot.send_message(message.chat.id, msg,reply_markup=menu_markup())
		elif menu_position == "orders/delall" and message.text == "Нет":
			menu_position = "orders"
			msg = "Выберите действие"
			tg_bot.send_message(message.chat.id, msg,reply_markup=menu_markup())
		elif menu_position == "orders/delall" and message.text == "Да":
			menu_position = "orders"
			#Удаляем ордера
			deleteAllOrders(message)
			#Заново показываем
			showOrders(message)


		#Ввод через запятую времени закупки
		elif menu_position == "enter_times":
			values_strs = message.text.split(',')
			bot.buyTimes = []
			for value in values_strs:
				bot.buyTimes.append(int(value))
			
			#Смотрим чтобы совпадало кол-во ордеров с количеством выкупов
			if(len(bot.orderAmounts2) != len(bot.buyTimes)):
				menu_position = "enter_times"

				tg_bot.send_message(message.chat.id, "Введите " + str(len(bot.orderAmounts2)) + " значений времени через запятую в секундах между " + bot.what("покупками", "продажами"),reply_markup=menu_markup())
			else:
				menu_position = "enter_times/confirm"

				tg_bot.send_message(message.chat.id, bot.accountName2() + ". " + bot.what("Выкуп", "Продажа") + " токенов произойдет через: " + arr2secs(bot.buyTimes),reply_markup=menu_markup())
	
		#Повторный ввод времени
		elif menu_position == "enter_times/confirm" and message.text == "Нет":
		#Сохраняем где находимся
			menu_position = "enter_times"


			tg_bot.send_message(message.chat.id, "Через запятую время в секундах между " + bot.what("покупками", "продажами"),reply_markup=menu_markup())
		#Запоминаем время выкупа
		elif menu_position == "enter_times/confirm" and message.text == "Да":
			#Сохраняем где находимся
			menu_position = "go"

			msg = stock_prices_msg()
			msg += bot.workPreviewText() + "\n\nНачать торги?"


			tg_bot.send_message(message.chat.id, msg,reply_markup=menu_markup())

		#Начинаем торги
		elif menu_position == "go" and message.text == "Начать":
			menu_position = "working"
			#Пока не остановили работу
			print("Started!!!")
			send2chats("Торги запущены!")

			n = 0
			print("actions:")
			print(bot.trade_actions)
			for action in bot.trade_actions:
				n += 1
				#Выход из торогов
				if not menu_position in ["working", "working/cancel"]:
					print("break")
					break;
				res = {"success": False}
				print("action:")
				print(action)
				if action[1] == "sleep":
					send2chats(str(n) + "/" + str(len(bot.trade_actions)) + ". Ждем " + str(action[2]) + " сек.")
					time.sleep(action[2])
				elif action[1] in ["buy", "sell"]:
					if action[0] == "Account1":
						acc = bot.account1
					else:
						acc = bot.account2
					count_tokens = action[2]
					price = action[3]
					res = acc.createOrder(bot.pairName, action[1], str(count_tokens), str(price))
					a_title = {"sell": "продажу", "buy": "покупку"}
					if res["success"]:
						item = res["item"]
						send2chats(str(n) + "/" + str(len(bot.trade_actions)) + ". " + action[0] + ". Создан ордер на " + a_title[action[1]] + " #" + str(item["orderId"]) + " (" + str(count_tokens) + " " + bot.tokenName + " по цене " + str(round(price,5)) + " USDT)")
					else:
						send2chats(str(n) + "/" + str(len(bot.trade_actions)) + ". " + action[1] + ". Ошибка при содании ордера на " + a_title[action[1]])

			bot.trade_actions = []
			menu_position = ""
			send2chats("Торги завершены!\n\n" + getBalances())

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
