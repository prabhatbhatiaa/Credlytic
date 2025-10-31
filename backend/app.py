"""
Credlytic Backend - Certificate Minting & Verification API
Handles NFT certificate creation on Aptos blockchain and student verification
"""

import os
import asyncio
import traceback
import time
import requests
import urllib3

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

from aptos_sdk.account import Account
from aptos_sdk.async_client import RestClient 
from aptos_sdk.transactions import (
    EntryFunction, 
    TransactionArgument, 
    TransactionPayload,
    RawTransaction, 
    SignedTransaction
)
from aptos_sdk.authenticator import AccountAuthenticator
from aptos_sdk.bcs import Serializer

# Suppress SSL warnings when using IP fallback
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ========== Configuration ==========
load_dotenv()

NODE_URL = "https://fullnode.devnet.aptoslabs.com/v1"
PRIVATE_KEY = os.getenv("UNIVERSITY_PRIVATE_KEY")
COLLECTION_NAME = "Credlytic - Hack"

# Indexer fallback configuration (IP workaround for DNS issues)
INDEXER_URL = "https://34.148.21.218/v1/graphql"
INDEXER_HOST = "indexer-devnet.staging.gcp.aptosdev.com"

if not PRIVATE_KEY:
    raise Exception("UNIVERSITY_PRIVATE_KEY not found in .env file")

try:
    university_account = Account.load_key(PRIVATE_KEY)
    print(f"✅ University Wallet: {university_account.address()}")
except ValueError as e:
    raise Exception(f"Invalid private key in .env: {e}")

# ========== Helper Functions ==========

def is_valid_aptos_address(address):
    """Validates Aptos wallet address format"""
    if not address or not address.startswith("0x"):
        return False
    
    if len(address) < 3 or len(address) > 66:
        return False
    
    try:
        int(address[2:], 16)
        return True
    except ValueError:
        return False


def generate_certificate_png(student_name, course_name, tx_hash, token_name):
    """Generates personalized certificate image with student details"""
    try:
        # Load template and fonts
        img = Image.open("template.png").convert("RGB")
        draw = ImageDraw.Draw(img)
        
        font_name = ImageFont.truetype("inter.ttf", 60)
        font_course = ImageFont.truetype("inter.ttf", 45)
        font_tx = ImageFont.truetype("inter.ttf", 20)
        
        # Draw text on certificate
        draw.text((726, 526), student_name, fill="white", font=font_name)
        draw.text((840, 674), course_name, fill="white", font=font_course)
        
        short_hash = f"Blockchain Verified Tx: {tx_hash[:10]}...{tx_hash[-8:]}"
        draw.text((699, 765), short_hash, fill="gray", font=font_tx)
        
        # Save with safe filename
        safe_filename = token_name.replace(":", "").replace("#", "").replace(" ", "_") + ".png"
        os.makedirs("generated", exist_ok=True)
        
        filepath = os.path.join("generated", safe_filename)
        img.save(filepath, "PNG")
        
        print(f"📄 Certificate generated: {filepath}")
        return safe_filename
        
    except FileNotFoundError:
        print("❌ Template or font file not found")
        return None
    except Exception as e:
        print(f"❌ Error generating certificate: {e}")
        return None

# ========== Flask App Setup ==========

app = Flask(__name__)
CORS(app)

# ========== API Endpoints ==========

@app.route("/create-cert", methods=["POST"])
def create_cert_endpoint():
    """Mints a new NFT certificate on Aptos blockchain"""
    
    data = request.get_json()
    student_name = data.get("name")
    course_name = data.get("course")
    student_id = data.get("student_id")
    
    # Validation
    if not all([student_name, course_name, student_id]):
        return jsonify({
            "success": False, 
            "error": "Missing required fields: name, course, or student_id"
        }), 400
    
    if not is_valid_aptos_address(student_id):
        return jsonify({
            "success": False, 
            "error": "Invalid wallet address format"
        }), 400
    
    print(f"\n🎓 Minting certificate for {student_name} (ID: {student_id})")
    
    try:
        # Blockchain minting process
        async def mint_certificate():
            rest_client = RestClient(NODE_URL)
            
            try:
                # Create unique token name
                timestamp = int(time.time())
                token_name = f"Certificate: {student_name} #{timestamp}"
                print(f"   Token name: {token_name}")
                
                # Build transaction payload
                payload = EntryFunction.natural(
                    "0x3::token",
                    "create_token_script",
                    [],
                    [
                        TransactionArgument(COLLECTION_NAME, Serializer.str),
                        TransactionArgument(token_name, Serializer.str),
                        TransactionArgument(f"Awarded for: {course_name}", Serializer.str),
                        TransactionArgument(1, Serializer.u64),
                        TransactionArgument(1, Serializer.u64),
                        TransactionArgument("https://i.imgur.com/T0aCg0C.png", Serializer.str),
                        TransactionArgument(university_account.address(), Serializer.struct),
                        TransactionArgument(0, Serializer.u64),
                        TransactionArgument(0, Serializer.u64),
                        TransactionArgument([False] * 5, Serializer.sequence_serializer(Serializer.bool)),
                        TransactionArgument(["student_id"], Serializer.sequence_serializer(Serializer.str)),
                        TransactionArgument([student_id.lower().encode('utf-8')], Serializer.sequence_serializer(Serializer.to_bytes)),
                        TransactionArgument(["string"], Serializer.sequence_serializer(Serializer.str)),
                    ],
                )
                
                # Sign and submit transaction
                print("   Signing transaction...")
                raw_txn = await rest_client.create_bcs_transaction(
                    university_account, 
                    TransactionPayload(payload)
                )
                
                authenticator = university_account.sign_transaction(raw_txn)
                signed_txn = SignedTransaction(raw_txn, authenticator)
                
                print("   Submitting to blockchain...")
                tx_hash = await rest_client.submit_bcs_transaction(signed_txn)
                
                print(f"   ⏳ Waiting for confirmation ({tx_hash})...")
                await rest_client.wait_for_transaction(tx_hash)
                
                print(f"   ✅ Certificate minted successfully!")
                return tx_hash, token_name
                
            finally:
                await rest_client.close()
        
        # Execute async minting
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tx_hash, token_name = loop.run_until_complete(mint_certificate())
        loop.close()
        
        # Generate certificate image
        print("   Generating certificate image...")
        filename = generate_certificate_png(student_name, course_name, tx_hash, token_name)
        
        # Prepare response
        explorer_url = f"https://explorer.aptoslabs.com/txn/{tx_hash}?network=devnet"
        base_url = request.host_url.replace("http://", "https://") if 'pythonanywhere' in request.host_url else request.host_url
        
        response_data = {
            "success": True,
            "tx_hash": tx_hash,
            "explorer_url": explorer_url,
            "message": "Certificate minted successfully!"
        }
        
        if filename:
            response_data["download_url"] = f"{base_url}download/{filename}"
            print(f"   🖼️ Download available at: {response_data['download_url']}")
        else:
            response_data["message"] = "Minted successfully, but image generation failed"
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Minting failed: {e}")
        traceback.print_exc()
        return jsonify({
            "success": False, 
            "error": f"Server error: {str(e)}"
        }), 500


@app.route("/download/<filename>")
def download_file(filename):
    """Serves generated certificate images for download"""
    
    safe_filename = os.path.basename(filename)
    
    if not safe_filename.endswith(".png"):
        return "Invalid file type", 400
    
    try:
        return send_from_directory("generated", safe_filename, as_attachment=True)
    except FileNotFoundError:
        return "Certificate not found", 404


@app.route("/get-my-certs", methods=["POST"])
def get_student_certs():
    """Retrieves all certificates for a student wallet address"""
    
    data = request.get_json()
    student_id = data.get("student_id")
    
    if not is_valid_aptos_address(student_id):
        return jsonify({
            "certificates": [], 
            "error": "Invalid wallet address"
        }), 400
    
    print(f"\n🔍 Searching certificates for: {student_id}")
    
    # Multiple indexer endpoints for fallback
    endpoints = [
        {
            "name": "Official Devnet API",
            "url": "https://api.devnet.aptoslabs.com/v1/graphql",
            "verify": True
        },
        {
            "name": "Staging Indexer",
            "url": "https://indexer-devnet.staging.gcp.aptosdev.com/v1/graphql",
            "verify": True
        },
        {
            "name": "IP Fallback",
            "url": INDEXER_URL,
            "verify": False,
            "headers": {"Host": INDEXER_HOST}
        }
    ]
    
    # GraphQL query
    query = """
    query GetStudentCerts($creator: String!, $collection: String!, $student_id: String!) {
      current_token_datas(
        where: {
          collection_data: {
            collection_name: {_eq: $collection}, 
            creator_address: {_eq: $creator}
          }
          current_token_properties: {
            property_key: {_eq: "student_id"}, 
            property_value: {_eq: $student_id}
          }
        }
        order_by: {transaction_version: desc}
      ) {
        token_name
        transaction_version
      }
    }
    """
    
    variables = {
        "creator": str(university_account.address()),
        "collection": COLLECTION_NAME,
        "student_id": student_id.lower()
    }
    
    # Try each endpoint until one succeeds
    for endpoint in endpoints:
        try:
            print(f"   Trying {endpoint['name']}...")
            
            headers = endpoint.get("headers", {})
            headers["Content-Type"] = "application/json"
            
            response = requests.post(
                endpoint["url"],
                json={"query": query, "variables": variables},
                headers=headers,
                verify=endpoint.get("verify", True),
                timeout=15
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "errors" in result:
                raise Exception(str(result["errors"]))
            
            tokens = result.get("data", {}).get("current_token_datas", [])
            print(f"   ✅ Found {len(tokens)} certificate(s) via {endpoint['name']}")
            
            # Format response
            base_url = request.host_url.replace("http://", "https://") if 'pythonanywhere' in request.host_url else request.host_url
            
            certificates = []
            for token in tokens:
                token_name = token.get("token_name")
                version = token.get("transaction_version")
                safe_filename = token_name.replace(":", "").replace("#", "").replace(" ", "_") + ".png"
                
                certificates.append({
                    "name": token_name,
                    "explorer_url": f"https://explorer.aptoslabs.com/txn/{version}?network=devnet",
                    "download_url": f"{base_url}download/{safe_filename}"
                })
            
            return jsonify({"certificates": certificates})
            
        except requests.exceptions.Timeout:
            print(f"   ⏱️ Timeout with {endpoint['name']}")
            continue
            
        except Exception as e:
            print(f"   ❌ Failed with {endpoint['name']}: {e}")
            continue
    
    # All endpoints failed
    print("❌ All indexer endpoints failed")
    return jsonify({
        "certificates": [], 
        "error": "Unable to connect to indexer. Please try again later."
    }), 500


# ========== Server Startup ==========

if __name__ == "__main__":
    os.makedirs("generated", exist_ok=True)
    print("\n" + "="*50)
    print("🚀 Credlytic Backend Server")
    print("="*50)
    print(f"📍 Running at: http://127.0.0.1:5000")
    print("⌨️  Press CTRL+C to stop\n")
    
    app.run(port=5000, debug=True)