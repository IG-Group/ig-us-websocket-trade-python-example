import FIXPMsgUtil
from typing import Dict
import Constant
from datetime import datetime


class ApplicationMsgUtil:

    @staticmethod
    def create_application_msg(msg_type: str):
        msg = dict()
        msg['MsgType'] = msg_type
        return msg

    @staticmethod
    def decorate_application_msg(msg: dict):
        msg['ApplVerID'] = Constant.APPL_VER_ID
        msg['SendingTime'] = datetime.now().isoformat()
        return msg

    @staticmethod
    def create_new_single_order(account: str,
                                client_order_id: str,
                                security_id: str,
                                side: str,
                                order_qty: str,
                                ord_typ: str,
                                currency: str,
                                time_in_force: str,
                                price: str = None,
                                expire_time: str = None):
        #         {"MsgType": "NewOrderSingle",
        #          "ApplVerID": "FIX50SP2",
        #          "CstmApplVerID": "IGUS/Trade/V1",
        #          "SendingTime": "20190802-21:14:38.717",
        #          "ClOrdID": "12345",
        #          "Account": "PDKKL",
        #          "SecurityID": "CS.D.GBPUSD.CZD.IP",
        #          "SecurityIDSource": "MarketplaceAssignedIdentifier",
        #          "Side": "Buy",
        #          "TransactTime": "20190802-21:14:38.717",
        #          "OrderQty": "6",
        #          "OrdTyp": "2",
        #          "Price": "34.444",
        #          "Currency": "USD",
        #          "TimeInForce": "GoodTillDate",
        #          "ExpireTime": "20190802-17:00:00.000" }
        msg: dict = ApplicationMsgUtil.create_application_msg("NewOrderSingle")
        msg = ApplicationMsgUtil.decorate_application_msg(msg)
        msg['ClOrdID'] = client_order_id
        msg['Account'] = account
        msg['SecurityID'] = security_id
        msg['SecurityIDSource'] = "MarketplaceAssignedIdentifier"
        msg['Side'] = side
        msg['OrderQty'] = order_qty
        msg['OrdType'] = ord_typ
        if expire_time is not None:
            msg['Price'] = price
        msg['Currency'] = currency
        msg['TimeInForce'] = time_in_force
        if expire_time is not None:
            msg['ExpireTime'] = expire_time
        msg['TransactTime'] = msg['SendingTime']
        return msg