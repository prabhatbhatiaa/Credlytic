# This script creates the main "Collection" for our NFTs.
# It uses the ASYNC client and must be run only ONCE.

import os
import asyncio # async functions ke lie
import traceback
from dotenv import load_dotenv

# Required tools APTOS me se
from aptos_sdk.account import Account
from aptos_sdk.async_client import RestClient
from aptos_sdk.transactions import (
    EntryFunction, TransactionArgument, TransactionPayload,
    RawTransaction, SignedTransaction
)
from aptos_sdk.authenticator import AccountAuthenticator
from aptos_sdk.bcs import Serializer

# Loads admin key from .env
load_dotenv()
PRIVATE_KEY = os.getenv("UNIVERSITY_PRIVATE_KEY")

# Connecting to the aptos DEVNET
NODE_URL = "https://fullnode.devnet.aptoslabs.com/v1"

# Creating a collection on the blockchain
COLLECTION_NAME = "Credlytic - Hack"


# === MAIN SETUP ===

# Initialize the ASYNC client
rest_client = RestClient(NODE_URL) # async client to talk to the node url
try:
    university_account = Account.load_key(PRIVATE_KEY) # Trying to load the account from key
except ValueError as e:
    print(f"🔴 Error loading private key: {e}")
    print("🔴 Make sure the key in .env starts with 0x and is 66 chars long.")
    exit()
except Exception as e:
    print(f"🔴 Unexpected error loading key: {e}")
    exit()

# async function that handles the entire FREAKING PROCESS!!!!
async def main():
    print(f"✅ Using wallet address (University): {university_account.address()}")
    print(f"✨ Creating collection named: '{COLLECTION_NAME}'")
    print("   (This might take 10-20 seconds...)")

    # Creates NFT collection on the aptos standard (locker room me ek locker banara hu)
    payload = EntryFunction.natural(
        "0x3::token", "create_collection_script", [],
        [
            TransactionArgument(COLLECTION_NAME, Serializer.str), # Arg 1: Name of coll
            TransactionArgument("Official Academic Records", Serializer.str), # Arg 2: Desc of col
            TransactionArgument("", Serializer.str), # Arg 3: icon (opt)
            TransactionArgument(1_000_000, Serializer.u64), # Arg 4: define the max supply
            TransactionArgument([False, False, False], Serializer.sequence_serializer(Serializer.bool)), # Arg 5: mutable!!!
        ],
    )

    try:
        # Step 1: Build the unsigned RawTransaction
        raw_txn: RawTransaction = await rest_client.create_bcs_transaction(
            sender=university_account,
            payload=TransactionPayload(payload)
        )
        print("-> Raw transaction created.")

        # Step 2: Sign the RawTransaction to get the Authenticator
        authenticator: AccountAuthenticator = university_account.sign_transaction(raw_txn)
        print("-> Transaction signed.")

        # Step 3: Combine them into a SignedTransaction object
        signed_txn_object = SignedTransaction(raw_txn, authenticator)
        print("-> SignedTransaction object created.")

        # Step 4: Submit the SignedTransaction OBJECT
        tx_hash = await rest_client.submit_bcs_transaction(signed_txn_object)
        print(f"⏳ Transaction submitted! Hash: {tx_hash}")

        # Step 5: Wait for confirmation
        print(" Waiting for confirmation...")
        await rest_client.wait_for_transaction(tx_hash)

        # Success!
        print("\n" + "="*50)
        print("🎉 SUCCESS! Collection created successfully!")
        print(f"🔗 View the transaction details here:")
        print(f"   https://explorer.aptoslabs.com/txn/{tx_hash}?network=devnet")
        print("="*50 + "\n")

    except Exception as e:
        print(f"\n🔴 FAILED! Error during collection creation: {e}")
        if "INSUFFICIENT_BALANCE" in str(e).upper():
             print("   Hint: Your wallet doesn't have enough Devnet APT. Go to Petra and click 'Faucet' 10-15 times.")
        elif "already published" in str(e).lower() or "abort" in str(e).lower():
             print(f"   Hint: You already created a collection named '{COLLECTION_NAME}' with this account. You can continue.")
        else:
             traceback.print_exc() # Print full error for debugging
    finally:
        # Always close the connection
        await rest_client.close()
        print("Connection closed.")


if __name__ == "__main__":
    asyncio.run(main()) # asyncio.run() creates and closes its own event loop.