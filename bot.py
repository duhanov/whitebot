from whitebit import *

class Bot:
    pairName = "BTC_USDT"#Название пары
    percents = 0.1#+/- процент для границ цены
    orderAmounts = []#объемы ордеров
    buyTimes = []#Времени между покупками
    tokenName = ""
    direction = 1#Направление покупки-продажи
    config = json.load(open('config.json'))
    account1 = Whitebit(config["account1"])
    account2 = Whitebit(config["account2"])

    def __init__(self, _direction, _pairName, _percents, _orderAmounts, _buyTimes):
        #Название торговой пары
        self.pairName = _pairName
        #Процент для расчета границ цен
        self.percents = _percents
        #Объемы покупки продажи
        self.orderAmounts = _orderAmounts
        #Название токена
        self.tokenName = _pairName.replace("_USDT", "")
        #Паузы во времени между покупками
        self.buyTimes = _buyTimes
        #Направление покупки-продажи
        self.direction = _direction

        #Смотрим направление купли-продажи
        if self.direction == 1:
            self.ccount1 = Whitebit(self.config["account1"])
            self.account2 = Whitebit(self.config["account2"])
        else:
            self.account2 = Whitebit(self.config["account1"])
            self.account1 = Whitebit(self.config["account2"])

    def msg(self, message):
        print(message)


    #Количество токенов суммарное для торговли
    def orderAmountsTotal(self):
        tokens_for_sale = 0
        for count_tokens in self.orderAmounts:
            tokens_for_sale += count_tokens
        return  tokens_for_sale       

    def accountName2(self):
        if self.direction == 1:
            return "Account2"
        else:
            return "Account1"

    def accountName1(self):
        if self.direction == 1:
            return "Account1"
        else:
            return "Account2"

    #Проверка количества токенов на балансе для продажи
    def checkTokensOnBalance(self):
        if self.direction == 1:
            tokens_on_balance = self.account1.getBalance(self.tokenName)
        else:
            tokens_on_balance = self.account2.getBalance(self.tokenName)

        tokens_for_sale = self.orderAmountsTotal()
        if (tokens_for_sale > tokens_on_balance):
            self.msg("ERROR: Not enough tokens on balance. Found: " + str(tokens_on_balance) + " " + self.tokenName + ". Need: " + str(tokens_for_sale) + " " + self.tokenName)
            return False;
        else:
            return True;

    #Проверка USDT на балансе для покупки токенов 
    def checkUSDTBalance(self, _min_price, _price_delta):
        res = {"success": False, "errors": []}
        if self.direction == 1:
            usdt_on_balance = self.account2.getBalance("USDT")
        else:
            usdt_on_balance = self.account1.getBalance("USDT")
        need_usdt = 0
        price = _min_price
        for count_tokens in self.orderAmounts:
            need_usdt += count_tokens * price
            price += _price_delta
        if (need_usdt > usdt_on_balance):
            res["errors"].append("Не достаточно средств на акканте " + self.accountName2() + "Есть: " + str(round(usdt_on_balance,4)) + " USDT.  Нужно: " + str(round(need_usdt,4)) + " USDT")
#            self.msg("ERROR: Not enough USDT on balance for buy (step 2). Found: " + str(usdt_on_balance) + " USDT" + ". Need: " + str(need_usdt) + " USDT")
            return res;
        else:
            res["success"] = True
            return res;


    def getMinMaxPrice(self, _percents):
        orders = self.account1.getAllOrders(self.pairName);
        #Получаем верхнюю цену покупки
        min_price = float(orders["bids"][0][0])
        #Получаем верхнюю цену подажи
        max_price = float(orders["asks"][0][0])
        print(_percents)
        print(min_price)
        print(max_price)
        min_price = min_price + (min_price * _percents  / 100)
        max_price = max_price - (max_price * _percents  / 100)
        print(min_price)
        print(max_price)

        return [min_price, max_price]


    #Проверка минимальной суммы закупки
    def checkMinAmounts(self):
        res = {"success": False, "errors": []}
        minmax = self.getMinMaxPrice(self.percents)
        price = minmax[0]
        for count_tokens in self.orderAmounts:
            if count_tokens * price < 5.05:
                res["errors"].append(str(count_tokens) + " " + self.tokenName + " * " + str(round(price,5)) + " USDT = " + str(round(count_tokens*price, 5)) + " USDT < 5.05 USD")
        if(len(res["errors"]) == 0):
            res["success"] = True

        return res

    #Для отладки - предполагаемые шаги
    def workPreviewText(self):
        text = "Шаг 1. Оредра на продажу.\n"
        minmax = self.getMinMaxPrice(self.percents)
        text += "Создание " + str(len(self.orderAmounts)) + " ордеров на продажу с ценой " + str(round(minmax[0],5)) + " USD до " + str(round(minmax[1],5)) + " USD\n";

        price = minmax[0]
        price_delta = (minmax[1] - minmax[0])/(len(self.orderAmounts)-1)


        n = 0
        for count_tokens in self.orderAmounts:
            n+=1
            text += str(n) + ". " + str(count_tokens) + " " + self.tokenName + " по " + str(round(price,5)) + " USDT\n"
            price = price + price_delta


        text += "\nШаг 2. Выкуп токенов\n"
        price = minmax[0]
        n = 0
        for count_tokens in self.orderAmounts:
            text += str(n+1) + ". Через " + str(self.buyTimes[n]) + " сек " + str(count_tokens) + " " + self.tokenName + " по " + str(round(price,5)) + " USDT\n"
            price = price + price_delta
            n += 1
        return text

    #Создание ордеров на продажу
    def createSellOrders(self):
        print("get orders for " + self.pairName);
        orders = self.account1.getAllOrders(self.pairName);

        if (len(orders["bids"]) > 0) and (len(orders["asks"]) > 0):

            #Получаем верхнюю цену покупки
            min_price = float(orders["bids"][0][0])
            #Получаем верхнюю цену подажи
            max_price = float(orders["asks"][0][0])
            print("Buy price: " + str(min_price) + " - Sell price: " + str(max_price))
            #Получаем цены
            min_price = round(min_price + (min_price * self.percents  / 100), 2)
            max_price = round(max_price - (max_price * self.percents  / 100), 2)
            

            if(min_price > max_price):
                print("Bad Value!")
                delta_percents = (float(orders["asks"][0][0]) - float(orders["bids"][0][0]))*100/float(orders["asks"][0][0])
                print(str(orders["bids"][0][0]) + "/" +  str(orders["asks"][0][0]) + " (" + str(round(delta_percents,5)) + "%) " + " < " + str(self.percents) + "%")
                print("decrease the value " + str(self.percents)+"%")
            else:


                #Шаг цены
                price = float(min_price)
                price_delta = (max_price - min_price)/len(self.orderAmounts)

                #Проверяем достаточно ли токенов на балансе
                if self.checkTokensOnBalance() and self.checkUSDTBalance(min_price, price_delta):
                    #Создаем ордера на продажу
                    print("Create " + str(len(self.orderAmounts)) + " orders from " + str(min_price) + " to " + str(max_price));
                    for count_tokens in self.orderAmounts:
                        print("SELL " + str(count_tokens) + " " + self.tokenName + " by " + str(price) + " USDT")
                        price = price + price_delta

                    #Создаем ордера по покупку
                    price = min_price
                    n = 0
                    for count_tokens in self.orderAmounts:
                        print("Sleep " + str(self.buyTimes[n]) + "sec")
                        print("BUY " + str(count_tokens) + " " + self.tokenName + " by " + str(price) + " USDT")
                        price = price + price_delta
                        n += 1




