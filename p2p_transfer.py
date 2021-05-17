import client

cli = client.Client("http://sanlee1:9850")
node_info = cli.node_info()
now_seconds = int(node_info.get('now_seconds'))
raw_txn = {
    u"sender": u"0x319ccfe5fc73a2cdae11c40f31ca1b61",  # sender address
    u"script": {
        u"code": u"0x1::TransferScripts::peer_to_peer",
        u"type_args": [
            u"0x1::STC::STC"
        ],
        u"args": [
            u"0x35b24637da69a8dad8473eff6d0a3ccc",  # receiver address
            # receiver auth key
            u"x\"61491ab613e4ea9b177c19cf7e3481a735b24637da69a8dad8473eff6d0a3ccc\"",
            u"100000u128"  # amount
        ]
    },
    u"max_gas_amount": 10000000,
    u"gas_unit_price": 1,
    u"gas_token_code": u"0x1::STC::STC",
    u"expiration_timestamp_secs": now_seconds + 43200,
    u"chain_id": 251,
    u"modules": []
}

signed_txn = cli.sign_txn(raw_txn)
print(cli.submit(signed_txn))
print(cli.get_block_reward(1024))
