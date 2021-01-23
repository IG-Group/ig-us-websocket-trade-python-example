import argparse
import json
import threading
import uuid
from argparse import Namespace
from datetime import datetime

from autobahn.twisted.websocket import WebSocketClientProtocol, \
    WebSocketClientFactory, connectWS
from twisted.internet import reactor, ssl, defer

from ApplicationMsgUtil import ApplicationMsgUtil
from FIXPMsgUtil import FIXPMsgUtil

# Protocol class extending WebSocketClientProtocol
from RunMe import RunMe


class IGUSPreTradeWebSocketClientProtocol(WebSocketClientProtocol):
    clientOrderIdCounter: int = 0
    securityListRequestCounter: int = 0
    isShuttingDown: bool = False

    receivedQuoteCounter: int = 0
    heartBeatInterval: int = 3
    sessionId: str = None

    isShuttingDown: bool = False

    run_me: RunMe = RunMe()
    example_thread: threading.Thread = None

    # override
    def onConnect(self, response):
        print("Server connected: {0}".format(response.peer))
        self.sessionId = str(uuid.uuid1())
        print("Session ID generated: {0}".format(self.sessionId))
        # example of starting thread
        self.example_thread = threading.Thread(target=self.run_me.run,
                                               args=(lambda count: self.callback_example(count),
                                                     lambda: self.isShuttingDown),
                                               daemon=True)
        self.example_thread.start()

    # override
    def onConnecting(self, transport_details):
        print("Connecting")

    # override
    def onOpen(self):
        print("WebSocket connection open.")
        # send Negotiate message
        self.send_negotiate_msg()

    # override
    def onMessage(self, payload, is_binary):
        if is_binary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            decoded_payload = payload.decode('utf8')
            print("Text message received: {0}".format(decoded_payload))
            msg = json.loads(decoded_payload)
            # Type is defined in FIXP messages by "MsgType", in Application Messages by "MessageType"
            msg_type = None
            if "MessageType" in msg:
                msg_type = msg["MessageType"]
            elif "MsgType" in msg:
                msg_type = msg["MsgType"]
            if msg_type == "ExecutionReport":
                print("ExecutionReport message received")
                # shutdown in 30 seconds
                self.factory.reactor.callLater(10, self.shut_down)
            # FIXP message types follow
            elif msg_type == "UnsequencedHeartbeat":
                self.send_heartbeat()
            elif msg_type == "NegotiationResponse":
                # Negotiation successful so send FIXP msg to establish session
                self.send_establish_msg()
            elif msg_type == "EstablishmentAck":
                # Session established, get list of securities
                self.factory.reactor.callLater(self.heartBeatInterval, self.send_heartbeat)
                self.send_new_order_single(account=self.factory.params['accountID'],
                                           security_id="CS.D.AEURGBP.CZD.IP",
                                           currency="GBP",
                                           side="Buy",
                                           order_qty="1",
                                           ord_typ="Market",
                                           time_in_force="ImmediateOrCancel")
            elif msg_type == "EstablishmentReject":
                print("EstablishmentReject message received : Stopping")
                self.shut_down()

    # override
    def onClose(self, was_clean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))
        # Connection closed, reactor can be stopped without connection error
        self.factory.reactor.stop()

    # dispatch msg via WebSocket
    def dispatch(self, msg: dict):
        msg_string: str = json.dumps(msg)
        print("Text message sent    : {0}".format(msg_string))
        self.sendMessage(msg_string.encode('utf8'))

    def send_heartbeat(self):
        self.dispatch(FIXPMsgUtil.create_heart_beat_msg())

    def send_negotiate_msg(self):
        self.dispatch(FIXPMsgUtil.create_negotiate_msg(self.sessionId, self.factory.params['userName'],
                                                       self.factory.params['password']))

    def send_establish_msg(self):
        self.dispatch(FIXPMsgUtil.create_establish_msg(self.sessionId, self.heartBeatInterval))

    def send_new_order_single(self, account: str, security_id: str, currency: str, side: str, order_qty: str,
                              ord_typ: str, time_in_force: str):
        self.clientOrderIdCounter += 1
        self.dispatch(ApplicationMsgUtil.create_new_single_order(account=account,
                                                                 security_id=security_id,
                                                                 side=side,
                                                                 order_qty=order_qty,
                                                                 ord_typ=ord_typ,
                                                                 currency=currency,
                                                                 time_in_force=time_in_force,
                                                                 client_order_id=f"{self.clientOrderIdCounter}-{datetime.now().timestamp()}"))

    #
    def is_shutting_down(self):
        return self.isShuttingDown

    def shut_down(self):
        if self.factory.reactor.running and not self.isShuttingDown:
            print("Shutting down.")
            self.isShuttingDown = True
            # give run_me a chance to stop
            self.example_thread.join(3)
            self.sendClose()

    def callback_example(self, count: int):
        print("Callback received with count {}.".format(count))


if __name__ == '__main__':
    import sys

    from twisted.python import log
    from twisted.internet import reactor

    parser = argparse.ArgumentParser(description='Demonstrate Trade WebSocket API.')
    parser.add_argument('--URL',
                        metavar='wss://....',
                        type=str,
                        help="URL for the WebSocket endpoint",
                        default="wss://demo-iguspretrade.ig.com/trade")
    parser.add_argument('--userName',
                        metavar='<user-name>',
                        type=str,
                        help="User Name",
                        required=True)
    parser.add_argument('--password',
                        metavar="<password>",
                        type=str,
                        help="Password",
                        required=True)
    parser.add_argument('--accountID',
                        metavar='N',
                        type=str,
                        help="Account ID",
                        default="1")

    args: Namespace = parser.parse_args()
    print("args : {0} ".format(args))

    log.startLogging(sys.stdout)
    factory = WebSocketClientFactory(args.URL)
    factory.params = {'userName': args.userName, 'password': args.password, 'accountID': args.accountID}
    print(factory.params)
    factory.protocol = IGUSPreTradeWebSocketClientProtocol
    contextFactory = ssl.ClientContextFactory()

    print("Ready to connect WebSocket")
    connector = connectWS(factory, contextFactory)
    reactor.run()
    print("Returned from reactor.run()")
