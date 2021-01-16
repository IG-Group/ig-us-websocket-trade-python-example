from datetime import datetime
from typing import Dict


class FIXPMsgUtil:

    @staticmethod
    def create_fixp_msg(msg_type: str):
        msg = dict()
        msg["MessageType"] = msg_type
        return msg

    @staticmethod
    def decorate_fixp_msg(msg: dict, session_id: str):
        msg["SessionId"] = session_id
        msg["Timestamp"] = datetime.now().timestamp()
        return msg

    @staticmethod
    def create_negotiate_msg(session_id: str, user_name: str, password: str):
        # '{"MessageType":"Negotiate","ApplVerID":"FIX50SP2","SendingTime":"2020-07-24T17:16:20.000","Timestamp":1595610929414,"SessionId":"17b7f610-cc30-11ea-99b8-5fd27dae0d36","ClientFlow":"Unsequenced","Credentials":{"CredentialsType":"login","Token":"<user-name:password>"}}'
        msg: dict = FIXPMsgUtil.create_fixp_msg("Negotiate")
        msg = FIXPMsgUtil.decorate_fixp_msg(msg, session_id)
        msg["ClientFlow"] = "Unsequenced"
        credentials: Dict[str, str] = {"CredentialsType": "login", "Token": user_name + ':' + password}
        msg["Credentials"] = credentials
        return msg

    @staticmethod
    def create_establish_msg(session_id: str, heartbeat_interval_seconds: int):
        # '{"MessageType":"Establish","Timestamp":159543175368000000,"SessionId":"17b7f610-cc30-11ea-99b8-5fd27dae0d36","KeepaliveInterval":30000}'
        msg: dict = FIXPMsgUtil.create_fixp_msg("Establish")
        msg = FIXPMsgUtil.decorate_fixp_msg(msg, session_id)
        msg["KeepaliveInterval"] = heartbeat_interval_seconds * 10000
        return msg

    @staticmethod
    def create_heart_beat_msg():
        return {"MessageType": "UnsequencedHeartbeat"}
