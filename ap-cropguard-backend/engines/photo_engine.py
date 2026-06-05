"""
AP-CropGuard — Photo Crop Damage Assessment Engine
====================================================
Photo crop damage assessment engine.
Primary: Google Gemini Vision (gemini-1.5-flash,
free tier).
Backup: Groq LLaMA Vision (llama-4-scout, free tier).
Fallback: Rule-based conservative estimate.
Designed for bulletproof demo-day reliability.
"""

import os
import json
import base64
import io

from PIL import Image
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="google")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="google")

import google.generativeai as genai
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# MODULE-LEVEL SETUP
# ---------------------------------------------------------------------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

_groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# ---------------------------------------------------------------------------
# ASSESSMENT PROMPT
# ---------------------------------------------------------------------------

ASSESSMENT_PROMPT = (
    "You are an expert agricultural scientist working "
    "for the Andhra Pradesh Agriculture Department "
    "disaster loss assessment system.\n\n"
    "Analyze this crop photograph and respond ONLY "
    "with a valid JSON object. No explanation, no "
    "markdown, no extra text. Just the JSON.\n\n"
    "JSON structure required:\n"
    "{\n"
    '  "damage_class": "Healthy" OR "Partially Damaged" OR "Severely Damaged",\n'
    '  "confidence_score": float between 0.0 and 1.0,\n'
    '  "estimated_photo_loss_pct": integer 0 to 100,\n'
    '  "crop_identified": "name of crop you see",\n'
    '  "disease_pest_detected": true or false,\n'
    '  "disease_details": [\n'
    "    {\n"
    '      "name": "disease or pest name",\n'
    '      "confidence": float 0.0 to 1.0,\n'
    '      "severity": "LOW" OR "MEDIUM" OR "HIGH",\n'
    '      "agronomic_advice": "specific actionable treatment recommendation"\n'
    "    }\n"
    "  ],\n"
    '  "analysis_notes": "brief observation about crop condition and visible symptoms"\n'
    "}\n\n"
    "Crop context: Kurnool district, Andhra Pradesh, "
    "Kharif season. Common crops: Groundnut, Cotton, "
    "Redgram, Jowar, Sunflower. Post-disaster assessment."
)

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def image_to_base64(image_bytes: bytes) -> tuple:
    """
    Convert raw image bytes to a base64-encoded string and detect media type.

    Media type detection uses magic byte signatures:
      JPEG: starts with FF D8 FF
      PNG:  starts with 89 50 4E 47

    Returns (base64_string, media_type).
    """
    if image_bytes[:3] == b"\xff\xd8\xff":
        media_type = "image/jpeg"
    elif image_bytes[:4] == b"\x89PNG":
        media_type = "image/png"
    else:
        media_type = "image/jpeg"

    b64_string = base64.b64encode(image_bytes).decode("utf-8")
    return b64_string, media_type


def parse_vision_response(response_text: str) -> dict:
    """
    Parse and validate a JSON response from a vision model.

    Strips markdown code fences, parses JSON, validates required fields,
    and clamps numeric fields to their valid ranges.

    Raises ValueError if required fields are missing or JSON is malformed.
    """
    text = response_text.strip()

    # Strip markdown fences
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(
            line for line in lines
            if not line.strip().startswith("```")
        ).strip()

    parsed = json.loads(text)

    required_fields = [
        "damage_class",
        "confidence_score",
        "estimated_photo_loss_pct",
        "crop_identified",
        "disease_pest_detected",
        "disease_details",
        "analysis_notes",
    ]
    for field in required_fields:
        if field not in parsed:
            raise ValueError(f"Missing required field in vision response: '{field}'")

    parsed["confidence_score"] = float(
        max(0.0, min(1.0, float(parsed["confidence_score"])))
    )
    parsed["estimated_photo_loss_pct"] = int(
        max(0, min(100, int(parsed["estimated_photo_loss_pct"])))
    )

    return parsed


# ---------------------------------------------------------------------------
# ASSESSMENT FUNCTIONS
# ---------------------------------------------------------------------------

def assess_with_gemini(image_bytes: bytes, claimed_crop: str) -> dict:
    """
    Assess crop damage using Google Gemini Vision (gemini-1.5-flash).

    Builds a PIL Image from bytes, sends it alongside the structured
    assessment prompt, and parses the JSON response.

    Raises an exception on any API or parsing failure.
    """
    model = genai.GenerativeModel("gemini-1.5-flash")

    pil_image = Image.open(io.BytesIO(image_bytes))
    prompt = ASSESSMENT_PROMPT + f"\n\nFarmer declared crop: {claimed_crop}"

    response = model.generate_content([prompt, pil_image])
    result = parse_vision_response(response.text)
    result["analysis_source"] = "Gemini Vision (gemini-1.5-flash)"
    return result


def assess_with_groq(image_bytes: bytes, claimed_crop: str) -> dict:
    """
    Assess crop damage using Groq LLaMA Vision (llama-4-scout-17b).

    Encodes the image as a base64 data URL and sends it via the
    Groq chat completions API with an image_url content block.

    Raises an exception on any API or parsing failure.
    """
    if _groq_client is None:
        raise RuntimeError("Groq client not initialised — GROQ_API_KEY missing.")

    b64_string, media_type = image_to_base64(image_bytes)
    prompt_text = ASSESSMENT_PROMPT + f"\n\nFarmer declared crop: {claimed_crop}"

    response = _groq_client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{b64_string}"
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt_text,
                    },
                ],
            }
        ],
        max_tokens=1024,
    )

    response_text = response.choices[0].message.content
    result = parse_vision_response(response_text)
    result["analysis_source"] = "Groq LLaMA Vision (llama-4-scout)"
    return result


def rule_based_fallback(claimed_crop: str) -> dict:
    """
    Return a conservative rule-based assessment when all vision APIs are unavailable.

    Does not use image bytes. Applies a 45% loss estimate as a safe
    default that will trigger manual field verification without
    automatically approving or denying a claim.
    """
    return {
        "damage_class":              "Partially Damaged",
        "confidence_score":          0.45,
        "estimated_photo_loss_pct":  45,
        "crop_identified":           claimed_crop,
        "disease_pest_detected":     False,
        "disease_details":           [],
        "analysis_notes":            (
            "Automated vision API unavailable. "
            "Conservative estimate applied. Manual field "
            "verification required."
        ),
        "analysis_source":           "Rule-based fallback (Vision API unavailable)",
    }


def assess_photo(image_bytes: bytes, claimed_crop: str) -> dict:
    """
    Main entry point for crop photo assessment.

    Fallback chain:
      1. Gemini Vision (gemini-1.5-flash)  — primary
      2. Groq LLaMA Vision (llama-4-scout) — secondary
      3. Rule-based conservative estimate  — guaranteed fallback

    Never raises an exception. Always returns a result dict with
    a 'fallback_used' field indicating which path was taken.
    """
    # 1. Try Gemini
    try:
        result = assess_with_gemini(image_bytes, claimed_crop)
        result["fallback_used"] = None
        print(f"[photo_engine] Assessment via Gemini Vision — crop: {claimed_crop}")
        return result
    except Exception as gemini_err:
        print(f"[photo_engine] Gemini failed: {gemini_err}")

    # 2. Try Groq
    try:
        result = assess_with_groq(image_bytes, claimed_crop)
        result["fallback_used"] = "groq"
        print(f"[photo_engine] Assessment via Groq LLaMA — crop: {claimed_crop}")
        return result
    except Exception as groq_err:
        print(f"[photo_engine] Groq failed: {groq_err}")

    # 3. Rule-based fallback
    print(f"[photo_engine] Both APIs failed — using rule-based fallback for crop: {claimed_crop}")
    result = rule_based_fallback(claimed_crop)
    result["fallback_used"] = "rule_based"
    return result
