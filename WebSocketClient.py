import argparse
import json
import uuid
from argparse import Namespace

from autobahn.twisted.websocket import WebSocketClientProtocol, \
    WebSocketClientFactory, connectWS
from twisted.internet import reactor, ssl, defer

from ApplicationMsgUtil import ApplicationMsgUtil
from FIXPMsgUtil import FIXPMsgUtil


# Protocol class extending WebSocketClientProtocol
class IGUSPreTradeWebSocketClientProtocol(WebSocketClientProtocol):
    clientOrderIdCounter: int = 0
    securityListRequestCounter: int = 0

    receivedQuoteCounter: int = 0
    heartBeatInterval: int = 3
    sessionId: str = None

    # override
    def onConnect(self, response):
        print("Server connected: {0}".format(response.peer))
        self.sessionId = str(uuid.uuid1())
        print("Session ID generated: {0}".format(self.sessionId))

    # override
    def onConnecting(self, transport_details):
        print("Connecting")
        return None  # ask for defaults

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
                print("EstablishmentReject message received : Stopping")
                # TODO close WebSocket "cleanly"
                reactor.stop()
            # FIXP message types follow
            elif msg_type == "UnsequencedHeartbeat":
                self.send_heartbeat()
            elif msg_type == "NegotiationResponse":
                # Negotiation successful so send FIXP msg to establish session
                self.send_establish_msg()
            elif msg_type == "EstablishmentAck":
                # Session established, get list of securities
                self.factory.reactor.callLater(self.heartBeatInterval, self.send_heartbeat)
                self.send_new_order_single("CS.D.NOKJPY.CZD.IP")
            elif msg_type == "EstablishmentReject":
                print("EstablishmentReject message received : Stopping")
                # TODO close WebSocket "cleanly"
                reactor.stop()

    # override
    def onClose(self, was_clean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))

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

    def send_new_order_single(self, security_id: str):
        self.clientOrderIdCounter += 1
        account = self.factory.params['userName']
        security_id = security_id
        side = "Buy"
        order_qty = "1"
        ord_typ = "Market"
        currency = "USD"
        time_in_force = "FillOrKill"
        self.dispatch(ApplicationMsgUtil.create_new_single_order(account="Z33UVI",
                                                                 security_id="CS.D.NOKJPY.CZD.IP",
                                                                 side="Buy",
                                                                 order_qty="1",
                                                                 ord_typ="Market",
                                                                 currency="USD",
                                                                 time_in_force="FillOrKill",
                                                                 client_order_id="{0}".format(self.clientOrderIdCounter)))


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
    connectWS(factory, contextFactory)
    reactor.run()
    print("Returned from reactor.run()")
