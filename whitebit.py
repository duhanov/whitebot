import requests
import time
import hashlib
import base64
import json
import hmac


class Whitebit:
    end_point = "https://whitebit.com"

    nonce = round(time.time() * 1000)

    API_SECRET = ""
    API_KEY = ""

    def __init__(self, _keys):
        self.API_KEY = _keys["API_KEY"]
        self.API_SECRET = _keys["API_SECRET"]

    def post(self, url, data):
#        print('nonce:' + str(self.nonce))


        data['request'] = url
        data['nonce'] = self.nonce

        data_json = json.dumps(data, separators=(',', ':'))  # use separators param for deleting spaces
        payload = base64.b64encode(data_json.encode('ascii'))
        signature = hmac.new(self.API_SECRET.encode('ascii'), payload, hashlib.sha512).hexdigest()

        r = requests.post(url = self.end_point + url, data = data_json, headers = {'Content-type': 'application/json', 'X-TXC-APIKEY': self.API_KEY, 'X-TXC-PAYLOAD': payload, 'X-TXC-SIGNATURE': signature})

        #Увеличиваем nonce
        self.nonce += 1

        return r


    #Получить ордера на покупку
    def getBids(self, pairName):
        return getAllOrders(pairName)["bids"]

    #Ордера на продажу
    def getAsks(self):
        return getAllOrders(pairName)["asks"]


    #Ордера
    def getAllOrders2(self, pairName):
        r = requests.get(url = self.end_point + "/api/v4/public/orderbook/" + pairName + "?limit=100&level=2" )#, headers = {'Content-type': 'application/json', 'X-TXC-APIKEY': API_KEY, 'X-TXC-PAYLOAD': payload, 'X-TXC-SIGNATURE': signature})
        return r.json()

    #Ордера
    def getAllOrders(self, pairName):
        r = requests.get(url = self.end_point + "/api/v1/public/depth/result?market=" + pairName)#, headers = {'Content-type': 'application/json', 'X-TXC-APIKEY': API_KEY, 'X-TXC-PAYLOAD': payload, 'X-TXC-SIGNATURE': signature})
        return r.json()

    #Получить пары
    def getPairs(self):
        r = requests.get(url = self.end_point + "/api/v1/public/markets")#, headers = {'Content-type': 'application/json', 'X-TXC-APIKEY': API_KEY, 'X-TXC-PAYLOAD': payload, 'X-TXC-SIGNATURE': signature})
        return r.json()
    

    #Создать ордер
    def createOrder(self, pairName, side, amount, price):
        data = {'market': pairName, 'side': side, 'amount': amount, 'price': price}
        r = self.post('/api/v4/order/new' , data)
        print('/api/v4/order/new')
        print(data)
        print(r.status_code)
        if r.status_code == 200:
            return {"success": True, "item": r.json()}
        else:
            print(r.text)
            return {"success": False, "message": str(r.status_code) + " " + r.text}

    #Удалить ордер
    def cancelOrder(self, pairName, orderId):
        r = self.post("/api/v4/order/cancel", {"market": pairName, "orderId": orderId})
        if r.status_code == 200:
            return {"success": True, "result": r.json()}
        else:
            return {"success": False, "message": str(r.status_code) + " " + r.text}
            return False

    def getMyOrders(self, pairName):
        r = self.post("/api/v4/orders", {"market": pairName})
        if r.status_code == 200:
            return {"success": True, "items": r.json()}
        else:
            return {"success": False, "message": str(r.status_code) + " " + r.text}
            return False
        


    #Получить баланс
    def getBalance(self, tokenName = "USDT"):
#       self.post("/api/v4/main-account/balance", {});
        r = self.post('/api/v4/trade-account/balance' , {'ticker': tokenName})

        if r.status_code == 200:
            return float(r.json()["available"])
        else:
            return -1
#        print("Status Code", r.status_code);
 #       print("JSON Response ", r.json());

#        self.post('/api/v4/main-account/balance' , {'ticker': 'USDT'})

 