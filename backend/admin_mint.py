# backend/admin_mint.py

import os
import time
import asyncio
import textwrap
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

from aptos_sdk.account import Account
from aptos_sdk.async_client import RestClient
from aptos_sdk.transactions import (
    EntryFunction,
    TransactionArgument,
    TransactionPayload,
    SignedTransaction
)
from aptos_sdk.bcs import Serializer


# ============================================================
#                 PATH FIXES (ABSOLUTE & SAFE)
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))        # /backend
TEMPLATE_PATH = os.path.join(BASE_DIR, "template.png")       # backend/template.png

# Frontend/Fonts folder (InterLocal)
FONT_PATH = os.path.abspath(
    os.path.join(BASE_DIR, "..", "frontend", "fonts", "inter.ttf")
)

print("[PATH] Template:", TEMPLATE_PATH)
print("[PATH] Font:", FONT_PATH)

load_dotenv()

NODE_URL = "https://fullnode.devnet.aptoslabs.com/v1"
PRIVATE_KEY = os.getenv("UNIVERSITY_PRIVATE_KEY")

if not PRIVATE_KEY:
    raise Exception("UNIVERSITY_PRIVATE_KEY missing in .env")

COLLECTION_NAME = "Credlytic - Hack"
university_account = Account.load_key(PRIVATE_KEY)


# ============================================================
#                         FONT HELPERS
# ============================================================

def safe_font(size):
    try:
        if os.path.exists(FONT_PATH):
            return ImageFont.truetype(FONT_PATH, size)
        return ImageFont.load_default()
    except Exception:
        return ImageFont.load_default()


def fit_font_for_width(draw, text, start_size, max_width, min_size=12):
    size = start_size
    while size >= min_size:
        f = safe_font(size)
        width = draw.textbbox((0, 0), text, font=f)[2]
        if width <= max_width:
            return f
        size -= 1
    return safe_font(min_size)


def wrap_text(draw, text, font, max_width):
    if not text:
        return [""]

    lines = textwrap.wrap(text, width=60)
    final = []

    for line in lines:
        if draw.textbbox((0, 0), line, font=font)[2] <= max_width:
            final.append(line)
        else:
            cur = ""
            for ch in line:
                if draw.textbbox((0, 0), cur + ch, font=font)[2] <= max_width:
                    cur += ch
                else:
                    final.append(cur)
                    cur = ch
            if cur:
                final.append(cur)

    return final

# ============================================================
#                CERTIFICATE GENERATOR (PNG + PDF)
# ============================================================

def generate_certificate_png(student_name, course_name, tx_hash, token_name, out_path):
    try:
        # Load template
        if not os.path.exists(TEMPLATE_PATH):
            print("[ERROR] Template missing:", TEMPLATE_PATH)
            return None

        img = Image.open(TEMPLATE_PATH).convert("RGB")
        draw = ImageDraw.Draw(img)

        # Fonts
        font_name = safe_font(60)
        font_course = safe_font(45)
        font_tx_size = 22

        # Coordinates
        name_xy = (726, 526)
        course_xy = (840, 674)
        tx_xy = (699, 765)

        # Draw main text fields
        draw.text(name_xy, student_name, fill="white", font=font_name)
        draw.text(course_xy, course_name, fill="white", font=font_course)

        # TX hash text building
        tx_text = f"Blockchain Verified Tx: {tx_hash}"

        max_tx_width = int(img.size[0] * 0.70)
        font_tx = fit_font_for_width(draw, tx_text, font_tx_size, max_tx_width)

        lines = wrap_text(draw, tx_text, font_tx, max_tx_width)
        line_h = draw.textbbox((0, 0), "Ay", font=font_tx)[3]

        start_y = tx_xy[1] - (line_h * len(lines) // 2)

        for i, line in enumerate(lines):
            draw.text(
                (tx_xy[0], start_y + i * line_h),
                line,
                fill="gray",
                font=font_tx
            )

        # Ensure directories exist
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

        # Save PNG
        try:
            img.save(out_path, "PNG")
        except:
            print("[ERR] PNG save failed")

        # Save PDF
        pdf_path = os.path.splitext(out_path)[0] + ".pdf"
        try:
            img.convert("RGB").save(pdf_path, "PDF", resolution=100.0)
        except Exception as e:
            print("[PDF ERROR]", e)
            return None

        return pdf_path

    except Exception as e:
        print("[CERT GENERATION ERROR]", e)
        return None


# ============================================================
#                 APTOS MINTING LOGIC
# ============================================================

async def _mint_async(student_name, course_name, student_email):
    client = RestClient(NODE_URL)

    try:
        timestamp = int(time.time())
        token_name = f"Certificate: {student_name} #{timestamp}"

        property_key = "student_id"
        property_value = student_email.lower().encode("utf-8")

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
                TransactionArgument([property_key], Serializer.sequence_serializer(Serializer.str)),
                TransactionArgument([property_value], Serializer.sequence_serializer(Serializer.to_bytes)),
                TransactionArgument(["string"], Serializer.sequence_serializer(Serializer.str)),
            ],
        )

        raw_txn = await client.create_bcs_transaction(
            university_account, TransactionPayload(payload)
        )

        signed = SignedTransaction(raw_txn, university_account.sign_transaction(raw_txn))

        tx_hash = await client.submit_bcs_transaction(signed)
        await client.wait_for_transaction(tx_hash)

        return tx_hash, token_name

    finally:
        await client.close()


def mint_certificate_with_email(student_name, course_name, student_email):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    tx_hash, token_name = loop.run_until_complete(
        _mint_async(student_name, course_name, student_email)
    )
    loop.close()
    return tx_hash, token_name
