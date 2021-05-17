# Copyright (c) The starcoin Core Contributors

from __future__ import absolute_import
from future.utils import raise_with_traceback
from requests import Session, Request
import json
SUB_ADDRESS_LEN = 8
STARCOIN_HASH_PREFIX = b"STARCOIN::"
CORE_CODE_ADDRESS = "0x00000000000000000000000000000001"
ACCOUNT_ADDRESS_LEN = 16
RESOURCE_TAG = 1


class InvalidServerResponse(Exception):
    pass


class StateNotFoundError(ValueError):
    pass


class JsonResponseError(Exception):
    pass


class Client(object):
    u"""Starcoin sdk client
    """

    def __init__(
            self,
            url,
    ):
        self.request = RpcRequest(url)
        self.session = Session()

    def execute(self, operation):
        u""" Execute a rpc request operation
        operation = {
            "rpc_method": $rpc_method,
            "params": $params,
        }
        such as:
        operation = {
            "rpc_method": "node.info",
            "params": None,
        }

        """
        req = self.request.prepare(
            rpc_method=operation[u"rpc_method"], params=operation[u"params"])
        resp = self.session.send(req)
        resp.raise_for_status()
        try:
            json = resp.json()
        except ValueError as e:
            raise_with_traceback(InvalidServerResponse(
                "Parse response as json failed: {}, response: {}".format(e, resp.text)))
        if json.get(u"error") is not None:
            raise_with_traceback(JsonResponseError(
                "Response:{}".format(resp.text)))
        return json.get(u"result")

    def node_info(self,):
        u"""Starcoin node information

        Return the node information
        """
        operation = {
            u"rpc_method": u"node.info",
            u"params": None,
        }
        return self.execute(operation)

    def node_status(self,):
        u""" Starcoin node status

        """
        operation = {
            u"rpc_method": u"node.status",
            u"params": None,
        }
        ret = self.execute(operation)
        return ret

    def get_transaction(self, txn_hash):
        operation = {
            u"rpc_method": u"chain.get_transaction",
            u"params": [txn_hash],
        }
        ret = self.execute(operation)
        return ret

    def get_transaction_info(self, txn_hash):
        operation = {
            u"rpc_method": u"chain.get_transaction_info",
            u"params": [txn_hash],
        }
        ret = self.execute(operation)
        return ret

    def get_block_by_number(self, number):
        operation = {
            u"rpc_method": u"chain.get_block_by_number",
            u"params": [number],
        }
        ret = self.execute(operation)
        return ret

    def submit(self, txn):
        operation = {
            u"rpc_method": u"txpool.submit_hex_transaction",
            u"params": [txn]
        }
        return self.execute(operation)

    def state_get(self, access_path):
        operation = {
            u"rpc_method": u"state.get",
            u"params": [access_path]
        }
        ret = self.execute(operation)
        if ret is None:
            raise_with_traceback(StateNotFoundError(u"State not found"))
        return ret

    def is_account_exist(self, addr):
        try:
            self.get_account_resource(addr)
        except StateNotFoundError:
            return False
        return True

    def get_account_sequence(self, addr):
        try:
            account_resource = self.get_account_resource(addr)
        except StateNotFoundError:
            return 0
        return int(account_resource.sequence_number)

    def get_account_token(self, addr, module, name):
        type_parm = u"{}::{}::{}".format(CORE_CODE_ADDRESS, module, name)

        struct_tag = u"{}::{}::{}<{}>".format(CORE_CODE_ADDRESS,
                                              u"Account", u"Balance", type_parm)
        path = u"{}/{}/{}".format(addr,
                                  RESOURCE_TAG, struct_tag)
        state = self.state_get(path)
        return state

    def get_account_resource(self, addr):
        struct_tag = u"{}::{}::{}".format(
            CORE_CODE_ADDRESS, u"Account", u"Account")
        path = u"{}/{}/{}".format(addr, RESOURCE_TAG, struct_tag)
        state = self.state_get(path)
        return state

    def sign_txn(self, raw_txn):
        operation = {
            u"rpc_method": u"account.sign_txn_request",
            u"params": [raw_txn],
        }
        ret = self.execute(operation)
        return ret

    def get_block_reward(self, block_number):
        u""" get block reward by blcok_number,block_number shoule less than header.block_number
        return coin_reward, author, gas_fee
        """
        operation = {
            u"rpc_method": u"chain.get_block_by_number",
            u"params": [block_number+1],
        }
        state_root = self.execute(operation).get("header").get("state_root")
        operation = {
            u"rpc_method": u"state.get_account_state_set",
            u"params": ["0x1", state_root],
        }
        state_set = self.execute(operation)
        infos = state_set.get("resources").get(
            "0x00000000000000000000000000000001::BlockReward::RewardQueue").get(
                "value")[1][1].get("Vector")

        for info in infos:
            info = info.get("Struct").get("value")
            if int(info[0][1].get("U64")) != block_number:
                continue
            reward = int(info[1][1].get("U128"))
            author = info[2][1].get("Address")
            gas_fee = int(info[3][1].get("Struct").get(
                "value")[0][1].get("U128"))
        return (reward, author, gas_fee)


class RpcRequest(object):
    def __init__(self, url):
        self.setting = {
            u"url": url,
            u"method": u"POST",
            u"request_id": u"sdk-client",
            u"headers": {u"Content-type": u"application/json"},
        }

    def prepare(self, rpc_method, params=None):
        method = self.setting[u"method"]
        url = self.setting[u"url"]
        post_data = {
            u"jsonrpc": u"2.0",
            u"id": self.setting[u"request_id"],
            u"method": rpc_method,
            u"params": params,
        }
        headers = self.setting[u"headers"]
        req = Request(method=method, url=url, json=post_data, headers=headers)
        return req.prepare()
