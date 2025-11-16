# backend/create_collec.py
# ONE TIME USE ONLY!!

import asyncio
import time
from dotenv import load_dotenv
import os

from aptos_sdk.account import Account
from aptos_sdk.async_client import RestClient
from aptos_sdk.transactions import (
    EntryFunction,
    TransactionArgument,
    TransactionPayload,
    SignedTransaction
)
from aptos_sdk.bcs import Serializer

load_dotenv()

NODE_URL = "https://fullnode.devnet.aptoslabs.com/v1"
PRIVATE_KEY = os.getenv("UNIVERSITY_PRIVATE_KEY")

COLLECTION_NAME = "Credlytic - Hack"
COLLECTION_DESCRIPTION = "Official NFTs issued by Credlytic"
COLLECTION_URI = "https://i.imgur.com/T0aCg0C.png"  # or your own

if not PRIVATE_KEY:
    raise Exception("UNIVERSITY_PRIVATE_KEY missing in .env")

account = Account.load_key(PRIVATE_KEY)


async def create_collection():
    client = RestClient(NODE_URL)

    payload = EntryFunction.natural(
        "0x3::token",
        "create_collection_script",
        [],
        [
            TransactionArgument(COLLECTION_NAME, Serializer.str),
            TransactionArgument(COLLECTION_DESCRIPTION, Serializer.str),
            TransactionArgument(COLLECTION_URI, Serializer.str),
            TransactionArgument(1000000, Serializer.u64),  # max supply
            TransactionArgument([False, False, False], Serializer.sequence_serializer(Serializer.bool))
        ]
    )

    raw_txn = await client.create_bcs_transaction(
        account,
        TransactionPayload(payload)
    )

    signed = SignedTransaction(raw_txn, account.sign_transaction(raw_txn))

    tx_hash = await client.submit_bcs_transaction(signed)
    print("Submitted TX:", tx_hash)

    await client.wait_for_transaction(tx_hash)
    print("\n🎉 SUCCESS!")
    print(f"Collection '{COLLECTION_NAME}' created!")
    print(f"Explorer: https://explorer.aptoslabs.com/txn/{tx_hash}?network=devnet")

    await client.close()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(create_collection())
    loop.close()
