from whitebit import *

class Bot:
    pairName = "BTC_USDT"#Название пары
    percents = 0.1#+/- процент для границ цены
    orderAmounts = []#объемы ордеров
    orderAmounts2 = []
    buyTimes = []#Времени между покупками
    tokenName = ""
    #Режим бота
    mode = ""
    config = json.load(open('config.json'))
    account1 = Whitebit(config["account1"])
    account2 = Whitebit(config["account2"])

    #Последовательность действий
    trade_actions = []

    def __init__(self, _mode, _pairName, _percents, _orderAmounts, _orderAmounts2, _buyTimes):
        #Название торговой пары
        self.pairName = _pairName
        #Процент для расчета границ цен
        self.percents = _percents
        #Объемы покупки продажи
        self.orderAmounts = _orderAmounts
        self.orderAmounts2 = _orderAmounts2
        #Название токена
        self.tokenName = _pairName.replace("_USDT", "")
        #Паузы во времени между покупками
        self.buyTimes = _buyTimes
        #Направление покупки-продажи
        self.mode = _mode

        self.minmax = [0,0]

        #Смотрим направление купли-продажи
#        if self.mode == 1:
        #1й продает 2му, 1й покупает у 2го, 1й продает, 1й покупает
#        if self.mode in ["1->2", "1<-2", "1->", "1<-"]:
#            self.ccount1 = Whitebit(self.config["account1"])
#            self.account2 = Whitebit(self.config["account2"])
#        else:
#            self.account2 = Whitebit(self.config["account1"])
#            self.account1 = Whitebit(self.config["account2"])

    def msg(self, message):
        print(message)





    #Количество токенов суммарное для торговли
    def orderAmountsTotal(self):
        tokens_for_sale = 0
        for count_tokens in self.orderAmounts:
            tokens_for_sale += count_tokens
        return  tokens_for_sale       

    def orderAmountsTotal2(self):
        tokens_for_sale = 0
        for count_tokens in self.orderAmounts2:
            tokens_for_sale += count_tokens
        return  tokens_for_sale       

    def accountName2(self):
        if self.mode in ["1->2", "1<-2", "1->", "1<-"]:
            return "Account2"
        else:
            return "Account1"

    def accountName1(self):
        if self.mode in ["1->2", "1<-2", "1->", "1<-"]:
            return "Account1"
        else:
            return "Account2"

    #Проверка количества токенов на балансе для продажи
    def checkTokensOnBalance(self, n):
        res = {"success": False, "errors": []}
        #Первый продает, второй покупает у первого
        mode_ok = False
        acc_name = ""
        if self.mode in ["1->2", "1->", "2<-1"]:
            print("check token balance account1")
            acc_name = "Account1"
            mode_ok = True
            tokens_on_balance = self.account1.getBalance(self.tokenName)
        elif self.mode in ["2->1", "2->", "1<-2"]:
            print("check token balance account2")
            acc_name = "Account2"
            mode_ok = True
            tokens_on_balance = self.account2.getBalance(self.tokenName)
        else:
            res["success"] = True

        #Режим требует проверки
        if mode_ok:
            if n == 1:                
                tokens_for_sale = self.orderAmountsTotal()
            else:
                tokens_for_sale = self.orderAmountsTotal2()
            print(str(tokens_for_sale) + "<=" +str(tokens_on_balance))
            if (tokens_for_sale > tokens_on_balance):
                self.msg("ERROR: Not enough tokens on balance. Found: " + str(tokens_on_balance) + " " + self.tokenName + ". Need: " + str(tokens_for_sale) + " " + self.tokenName)
                res["errors"] = ["Не достаточно токенов на балансе " + acc_name + ".\nЕсть: " + str(tokens_on_balance) + " " + self.tokenName + "\nНеобходимо: " + str(tokens_for_sale) + " " + self.tokenName]
            else:
                res["success"] = True

        return res

    #Проверка USDT на балансе для покупки токенов 
    def checkUSDTBalance(self, n):
        res = {"success": False, "errors": []}
        mode_ok = False
        #Для продажи не проверяем баланс USDT
        if self.mode in ["2->", "1->"]:
            res["success"] = True
        elif self.mode in ["2<-1", "2<-", "1->2"]:
            acc_name = "Account2"
            mode_ok = True
            print("check USDT balance account2")
            usdt_on_balance = self.account2.getBalance("USDT")
        #акк1 покупает
        elif self.mode in ["1<-2", "1<-", "2->1"]:
            acc_name = "Account1"
            mode_ok = True
            print("check USDT balance account1")
            usdt_on_balance = self.account1.getBalance("USDT")
        if mode_ok:
            if self.mode in ["1->", "2->", "1<-", "2<-"]:
                minmax = self.minmax
                print("minmax manual")
            else:
                minmax = self.getMinMaxPrice(0)
                print("minmax from stock")
            print(minmax)
 

            _min_price = minmax[0]
            _price_delta = (minmax[1] - minmax[0])/(len(self.orderAmounts) - 1)

            need_usdt = 0
            price = _min_price

            if n == 1:
                amounts = self.orderAmounts
            else:
                amounts = self.orderAmounts2

            for count_tokens in amounts:
                need_usdt += count_tokens * price
                price += _price_delta

            print(str(need_usdt) + "<=" +str(usdt_on_balance))

            if (need_usdt > usdt_on_balance):
                res["errors"].append("Не достаточно средств на акканте " + acc_name + ". Есть: " + str(round(usdt_on_balance,4)) + " USDT.  Нужно: " + str(round(need_usdt,4)) + " USDT")
#               self.msg("ERROR: Not enough USDT on balance for buy (step 2). Found: " + str(usdt_on_balance) + " USDT" + ". Need: " + str(need_usdt) + " USDT")
                return res;
            else:
                res["success"] = True
        print(res)
        return res;


    def getMinMaxPrice(self, _percents):
        orders = self.account1.getAllOrders(self.pairName);
        #Получаем верхнюю цену покупки
        min_price = float(orders["bids"][0][0])
        #Получаем верхнюю цену подажи
        max_price = float(orders["asks"][0][0])

        min_price = min_price + (min_price * _percents  / 100)
        max_price = max_price - (max_price * _percents  / 100)

        return [min_price, max_price]


    #Проверка минимальной суммы закупки
    def checkMinAmounts(self, n = 1):
        if n == 1:
            amounts = self.orderAmounts
        else:
            amounts = self.orderAmounts2

        res = {"success": False, "errors": []}

        if self.mode in ["1->", "2->", "1<-", "2<-"]:
            minmax = self.minmax
            print("manual minmax")
            print(minmax)
        else:
            minmax = self.getMinMaxPrice(self.percents)
            print("stock minmax")
            print(minmax)

        price = minmax[0]
        for count_tokens in amounts:
            if count_tokens * price < 5.05:
                res["errors"].append(str(count_tokens) + " " + self.tokenName + " * " + str(round(price,5)) + " USDT = " + str(round(count_tokens*price, 5)) + " USDT < 5.05 USD")
        if(len(res["errors"]) == 0):
            res["success"] = True

        return res


    #Названия для режимов работы
    def what(self, s1, s2):
        if self.mode in ["1->2", "2->1", "1->", "2->"]:
            return s1
        else:
            return s2


    def tradePlan(self):
        return self.workPreviewText()


    #Текстовое отображение плана (номер,действие)
    def tradePlanItemText(self, n, trade):
        acc_name = trade[0]
        action = trade[1]
        print("tradePlanItemText return")
        if action == "sleep":
            sleep_time = trade[2]
            return str(n) + ". " + acc_name + " ждем " + str(sleep_time) + " сек\n"
        else:
            count_tokens = trade[2]
            price = trade[3]
            return str(n) + ". " + acc_name + " " + action + " " + str(count_tokens) + " " + self.tokenName + " по " + str(price) + " USDT\n"

    #Добавить действие бота
    def addTrade(self, trade):
        self.trade_actions.append(trade)
        print("addTrade complete")
        return self.tradePlanItemText(len(self.trade_actions), trade)

    def backMode(self):
        return self.mode in ["1<-2", "2<-1"]

    #Для отладки - предполагаемые шаги
    def workPreviewText(self):
        self.trade_actions = []

        if self.mode in ["1->2", "1<-2", "1<-", "1->"]:
            acc1 = "Account1"
            acc2 = "Account2"
        else:
            acc1 = "Account2"
            acc2 = "Account1"

        text = "Шаг 1. " + acc1 + ". Ордера на " + self.what("продажу", "покупку") + ".\n"
        if self.mode in ["1->", "2->", "1<-", "2<-"]:
            minmax = self.minmax
            print("manual minmax")
            print(minmax)
        else:
            minmax = self.getMinMaxPrice(self.percents)
            print("stock minmax")
            print(minmax)

        #text += "Создание " + str(len(self.orderAmounts)) + " ордеров на " + self.what("продажу", "покупку") + " с ценой " + str(round(minmax[0],5)) + " USD до " + str(round(minmax[1],5)) + " USD\n";

        price = minmax[0]
        price_delta = (minmax[1] - minmax[0])/(len(self.orderAmounts)-1)
        print("price_delta=" + str(price_delta))

        #Для второго шага
        price_delta2 = 0
        price2 = 0
        if self.mode in ["1->2", "2->1", "1<-2", "2<-1"]:
            #text += "\nШаг 2. " + acc2 + ". " + self.what("выкуп", "продажа") + " токенов\n"
            price_delta2 = (minmax[1] - minmax[0])/(len(self.orderAmounts2)-1)
            #Вначале продажа потом покупка
            if self.backMode():
                print("start_price min for 2th step")
                price = minmax[1]
                price2 = minmax[1]
#                price = minmax[0]
#                price2 = minmax[0]
            #Вначале покупка потом продажа
            else:
                print("start_price max for 2th step")

            #price2 = minmax[0]
            print("start_price2=" + str(price2))
            print("price_delta2=" + str(price_delta2))


        #Создаем торговые дейтвия
        n = 0
        for count_tokens in self.orderAmounts:
            #TRADE!!!!!!
            text += self.addTrade([acc1, self.what("sell", "buy"), count_tokens, round(price,5)])

            #Второе действие если есть
            if self.mode in ["1->2", "2->1", "1<-2", "2<-1"]:
                #Торги второго шага
                if n < len(self.orderAmounts2):
                    count_tokens2 = self.orderAmounts2[n]
                    text += self.addTrade([acc2, self.what("buy", "sell"), count_tokens2, round(price2,5)])

                    #Обратный порядок цен
                    if self.backMode():
                        price2 = price2 - price_delta2
                    else:
                        price2 = price2 + price_delta2
                    #Вначале покупка потом продажа
                    #price2 = price2 + price_delta2
                #Пауза
                if n < len(self.buyTimes):
                    #Пауза
                    text += self.addTrade([acc2, "sleep", self.buyTimes[n]])
            
            #Next trade
            n+=1

            #Обратный порядок цен
            if self.backMode():
                print("backMode")
                print(str(price_delta))
                price = price - price_delta
            else:
                price = price + price_delta
 
            #price = price + price_delta


        print(self.trade_actions)
        return text


    #Для отладки - предполагаемые шаги
    def workPreviewText_old(self):
        self.trade_actions = []

        if self.mode in ["1->2", "1<-2", "1<-", "1->"]:
            acc1 = "Account1"
            acc2 = "Account2"
        else:
            acc1 = "Account2"
            acc2 = "Account1"

        text = "Шаг 1. " + acc1 + ". Ордера на " + self.what("продажу", "покупку") + ".\n"
        if self.mode in ["1->", "2->", "1<-", "2<-"]:
            minmax = self.minmax
            print("manual minmax")
            print(minmax)
        else:
            minmax = self.getMinMaxPrice(self.percents)
            print("stock minmax")
            print(minmax)

        text += "Создание " + str(len(self.orderAmounts)) + " ордеров на " + self.what("продажу", "покупку") + " с ценой " + str(round(minmax[0],5)) + " USD до " + str(round(minmax[1],5)) + " USD\n";

        price = minmax[0]
        price_delta = (minmax[1] - minmax[0])/(len(self.orderAmounts)-1)

        print("price_delta=" + str(price_delta))

        n = 0
        for count_tokens in self.orderAmounts:
            self.trade_actions.append([acc1, self.what("sell", "buy"), count_tokens, round(price,5)])
            n+=1
            text += str(n) + ". " + str(count_tokens) + " " + self.tokenName + " по " + str(round(price,5)) + " USDT\n"
            price = price + price_delta


        #Второй шаг
        if self.mode in ["1->2", "2->1", "1<-2", "2<-1"]:
            text += "\nШаг 2. " + acc2 + ". " + self.what("выкуп", "продажа") + " токенов\n"
            price_delta = (minmax[1] - minmax[0])/(len(self.orderAmounts2)-1)
            #Вначале продажа потом покупка
            if self.mode in ["1->2", "2->1"]:
                print("start_price min")
                price = minmax[0]
            #Вначале покупка потом продажа
            else:
                print("start_price max")
                price = minmax[1]
            print(price)
            n = 0
            for count_tokens in self.orderAmounts2:
                self.trade_actions.append([acc2, "sleep", self.buyTimes[n]])
                self.trade_actions.append([acc2, self.what("buy", "sell"), count_tokens, round(price,5)])

                text += str(n+1) + ". Через " + str(self.buyTimes[n]) + " сек " + str(count_tokens) + " " + self.tokenName + " по " + str(round(price,5)) + " USDT\n"
                #Вначале продажа потом покупка
                if self.mode in ["1->2", "2->1"]:
                    price = price + price_delta
                else:
                #Вначале покупка потом продажа
                    price = price - price_delta

                n += 1

        print(self.trade_actions)
        return text




