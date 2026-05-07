# -*- coding: utf-8 -*-
"""
Scam Simulator Router
Simulates realistic Malaysian scam scenarios for educational purposes.
The bot acts as a scammer and tracks whether the user identifies or falls for the scam.
"""

import uuid
import random
from fastapi import APIRouter
from typing import Dict, Any

from models.schemas import (
    SimulatorChatRequest,
    SimulatorChatResponse,
    SimulatorResetRequest,
    SimulatorResetResponse,
    ScamReport,
)

router = APIRouter(prefix="/api/simulator", tags=["simulator"])

# In-memory session store (replace with Redis/DB in production)
sessions: Dict[str, Dict[str, Any]] = {}


# ─────────────────────────────────────────────
# Scam Scenario Definitions
# ─────────────────────────────────────────────

SCAM_SCENARIOS = {
    "shopee_delivery": {
        "name": "Shopee Parcel Delivery Scam",
        "intro": (
            "Selamat pagi! Saya dari Shopee Express. Nama saya Encik Razif. "
            "Saya ada bungkusan untuk anda tapi ia ditahan di kastam. "
            "Ada bayaran kastam RM150 yang perlu dibayar dalam masa 24 jam atau bungkusan akan dimusnahkan. "
            "Boleh saya dapatkan nombor IC dan maklumat bank anda untuk proses pembayaran?"
        ),
        "escalation_1": (
            "Saya faham anda ragu-ragu, tapi ini prosedur standard Shopee. "
            "Ramai pelanggan dah bayar tadi. Kalau tak bayar sekarang, bungkusan bernilai RM800 tu akan dibuang. "
            "Saya boleh tolong proses kalau anda bagi nombor akaun bank anda."
        ),
        "escalation_2": (
            "Okay, saya bagi anda diskaun — bayar RM80 je. "
            "Transfer ke akaun Maybank: 1234-5678-9012. Nama: SHOPEE EXPRESS SDN BHD. "
            "Lepas transfer, hantar resit kepada saya. Cepat sikit, masa hampir tamat!"
        ),
        "red_flags": [
            "Legitimate courier companies never request payment via personal bank transfer",
            "Real Shopee Express never asks for IC number or bank account details",
            "Creating artificial urgency (24-hour deadline) is a classic pressure tactic",
            "Offering sudden 'discounts' on fees is a manipulation technique",
            "Official companies use proper payment portals, not personal transfers",
        ],
        "scam_type": "Parcel Delivery Scam (Shopee Impersonation)",
    },
    "lhdn_officer": {
        "name": "LHDN Tax Authority Scam",
        "intro": (
            "Good afternoon. This is Officer Hafizuddin from LHDN (Inland Revenue Board Malaysia). "
            "We have detected irregularities in your tax filing for year 2022-2023. "
            "You are required to pay an outstanding tax penalty of RM3,200 immediately to avoid legal action. "
            "Failure to comply within 2 hours will result in a warrant of arrest being issued. "
            "Please provide your bank account details so we can verify your identity."
        ),
        "escalation_1": (
            "I understand your concern, but this is a serious matter. "
            "We have already filed the case with the court. "
            "To stop the arrest warrant, you must pay RM3,200 via online transfer NOW. "
            "Our account: CIMB 7654-3210-9876. Name: LHDN MALAYSIA. "
            "This is your last chance before we proceed with legal action."
        ),
        "escalation_2": (
            "Sir/Madam, I am trying to help you here. My supervisor has approved a settlement of RM1,500. "
            "But you must pay in the next 30 minutes. "
            "Please also provide your MyKad number for our records. "
            "After payment, all charges will be dropped immediately."
        ),
        "red_flags": [
            "LHDN never demands immediate payment over phone calls",
            "Government agencies do not threaten arrest via phone",
            "Real LHDN uses official portals (mytax.hasil.gov.my) for payments",
            "Requesting IC/MyKad number over phone is identity theft",
            "Artificial time pressure (30 minutes, 2 hours) is a manipulation tactic",
            "Legitimate agencies never ask for bank account details over the phone",
        ],
        "scam_type": "Authority Impersonation Scam (LHDN)",
    },
    "bank_officer": {
        "name": "Bank Officer Impersonation Scam",
        "intro": (
            "Hello, selamat petang. Saya Nurul dari bahagian keselamatan Maybank. "
            "Kami mengesan aktiviti mencurigakan pada akaun anda — ada percubaan log masuk dari luar negara. "
            "Untuk melindungi akaun anda, kami perlu verify identiti anda sekarang. "
            "Boleh anda berikan nombor akaun dan OTP yang akan dihantar ke telefon anda?"
        ),
        "escalation_1": (
            "Saya faham anda bimbang, tapi ini untuk keselamatan akaun anda sendiri. "
            "Kalau anda tak verify sekarang, akaun anda akan dibekukan dalam masa 1 jam. "
            "OTP tu hanya untuk proses verification — kami tak akan guna untuk transaksi. "
            "Tolong berikan OTP tu sekarang supaya saya boleh selamatkan akaun anda."
        ),
        "escalation_2": (
            "Okay, saya nampak OTP dah dihantar. Sila beritahu saya nombor tu. "
            "Lepas ini, akaun anda akan selamat dan kami akan tambah lapisan keselamatan. "
            "Ini adalah prosedur standard Maybank untuk kes seperti ini. "
            "Nombor OTP tu? Cepat sikit sebelum ia tamat tempoh."
        ),
        "red_flags": [
            "Banks NEVER ask for OTP over the phone — OTP is strictly confidential",
            "Real bank officers never call asking for account numbers",
            "Threatening account freezing is a pressure tactic",
            "Legitimate banks use secure in-app verification, not phone calls",
            "If you receive such a call, hang up and call the bank's official hotline directly",
        ],
        "scam_type": "Bank Impersonation Scam (Maybank)",
    },
    "love_scam": {
        "name": "Love Scam (Online Romance Fraud)",
        "intro": (
            "Hi there! I came across your profile and I must say, you seem like a wonderful person. "
            "My name is Dr. James Chen, I'm a Malaysian-American surgeon currently working with MSF in Switzerland. "
            "I've been feeling quite lonely lately and would love to get to know you better. "
            "I hope you don't mind me reaching out like this. 😊"
        ),
        "escalation_1": (
            "I feel like we have such a deep connection already! I've never felt this way before. "
            "I was supposed to fly back to KL next week, but there's been a complication. "
            "My medical equipment worth USD 50,000 is stuck at customs in Dubai. "
            "I just need RM5,000 to pay the customs fee and I'll pay you back double when I arrive. "
            "I know this is sudden, but I trust you completely. Can you help me, sayang?"
        ),
        "escalation_2": (
            "I understand you're hesitant, but I'm desperate. I've already paid so much. "
            "If I don't get the equipment released, I'll lose my job and my visa. "
            "I promise I'll transfer RM20,000 to you the moment I land in KL. "
            "Please, you're the only one I can trust. Just RM3,000 for now? "
            "I'll video call you tonight to prove I'm real. I love you. 💕"
        ),
        "red_flags": [
            "Romance developed unusually fast — 'love' declared within days",
            "Claims to be overseas professional (doctor, engineer, military) — common love scam profile",
            "Never able to meet in person despite promising to visit",
            "Requests money for 'emergencies' — customs fees, medical bills, travel costs",
            "Promises to repay double — classic advance-fee fraud element",
            "Emotional manipulation — using affection to lower financial guard",
        ],
        "scam_type": "Love Scam (Online Romance Fraud)",
    },
}

# Keywords that indicate user is falling for the scam
FALLING_FOR_SCAM_KEYWORDS = [
    "okay", "ok", "sure", "yes", "ya", "yep", "alright", "fine",
    "transfer", "send", "pay", "payment", "bank", "account",
    "otp", "ic number", "my ic", "my account", "here it is",
    "done", "transferred", "paid", "sent",
    "baik", "boleh", "okay boleh", "saya setuju", "saya bayar",
    "nombor ic saya", "akaun saya", "saya dah transfer",
]

# Keywords that indicate user identified the scam
CAUGHT_SCAM_KEYWORDS = [
    "scam", "fraud", "fake", "not real", "impersonator", "lie", "liar",
    "report", "police", "block", "refuse", "no way", "suspicious",
    "penipuan", "penipu", "palsu", "lapor", "polis", "syak",
    "i won't", "i will not", "i don't believe", "this is a scam",
    "you're a scammer", "stop", "goodbye", "hang up",
    "verify", "official website", "call back", "hotline",
    "i'm not giving", "i won't give", "tidak", "tak nak", "tak percaya",
]


def get_random_scenario():
    """Pick a random scam scenario."""
    key = random.choice(list(SCAM_SCENARIOS.keys()))
    return key, SCAM_SCENARIOS[key]


def check_user_response(message: str):
    """
    Determine if user is falling for scam or catching it.
    Returns: "falling", "caught", or "neutral"
    """
    msg_lower = message.lower()

    caught_hits = sum(1 for kw in CAUGHT_SCAM_KEYWORDS if kw in msg_lower)
    falling_hits = sum(1 for kw in FALLING_FOR_SCAM_KEYWORDS if kw in msg_lower)

    if caught_hits >= 1:
        return "caught"
    elif falling_hits >= 2:
        return "falling"
    return "neutral"


def build_scam_report(scenario: dict, outcome: str) -> ScamReport:
    """Build the end-of-simulation report."""

    if outcome == "caught":
        outcome_text = "SUCCESS — You identified the scam!"
        advice = (
            "Tahniah! Anda berjaya mengenal pasti penipuan ini. / Congratulations! You successfully identified this scam.\n\n"
            "In real life, you should:\n"
            "• Report to CCID (Cyber Crime Investigation Department): 03-2610 5000\n"
            "• Report to BNMTELELINK (Bank Negara): 1-300-88-5465\n"
            "• Block the scammer's number immediately\n"
            "• Warn friends and family about this scam pattern\n"
            "• File a report at www.semakmule.rmp.gov.my"
        )
    else:
        outcome_text = "FAILED — You fell for the scam"
        advice = (
            "Jangan risau — ini adalah simulasi untuk pembelajaran. / Don't worry — this is a simulation for learning.\n\n"
            "If this happened in real life:\n"
            "• Contact your bank IMMEDIATELY to freeze transactions: Maybank 1-300-88-6688, CIMB 1-300-880-900\n"
            "• Report to CCID: 03-2610 5000\n"
            "• Report to BNMTELELINK: 1-300-88-5465\n"
            "• File a police report at your nearest police station\n"
            "• Remember: Banks NEVER ask for OTP. Government agencies NEVER demand immediate payment by phone."
        )

    return ScamReport(
        scam_type=scenario["scam_type"],
        red_flags=scenario["red_flags"],
        summary=(
            f"This simulation demonstrated a '{scenario['name']}'. "
            f"The scammer used psychological pressure tactics including urgency, authority impersonation, "
            f"and emotional manipulation to attempt to extract money or personal information. "
            f"These scams are extremely common in Malaysia and cost victims millions of ringgit annually."
        ),
        outcome=outcome_text,
        advice=advice,
    )


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@router.post("/chat", response_model=SimulatorChatResponse)
async def simulator_chat(request: SimulatorChatRequest):
    """
    Handle a chat turn in the scam simulation.
    Bot acts as a scammer and responds based on conversation state.
    """

    # ============================================================
    # TODO: WIRE BEDROCK HERE
    # Replace this mock response with actual AWS Bedrock API call
    # Model: Use BEDROCK_MODEL_ID from .env
    #
    # Suggested prompt structure:
    # system_prompt = f"""You are playing the role of a scammer in an educational simulation.
    # Scenario: {scenario['name']}
    # Your goal is to realistically simulate a Malaysian scammer to help users learn to identify scams.
    # Use a mix of English and Malay. Gradually escalate pressure tactics.
    # Current conversation turn: {session['turn']}
    # If the user shows suspicion, try to reassure them. If they comply, escalate your demands.
    # IMPORTANT: This is purely educational. Always stay in character as the scammer."""
    #
    # Also use Bedrock to detect if user caught the scam or fell for it, rather than keyword matching.
    # ============================================================

    # Initialize or retrieve session
    session_id = request.session_id or str(uuid.uuid4())

    if session_id not in sessions:
        # New session — pick a scenario and send opening message
        scenario_key, scenario = get_random_scenario()
        sessions[session_id] = {
            "scenario_key": scenario_key,
            "scenario": scenario,
            "turn": 0,
            "scam_ended": False,
            "user_caught_scam": False,
        }
        return SimulatorChatResponse(
            reply=scenario["intro"],
            session_id=session_id,
            scam_ended=False,
            user_caught_scam=False,
            report=None,
        )

    session = sessions[session_id]

    # If scam already ended, return a reminder
    if session["scam_ended"]:
        return SimulatorChatResponse(
            reply="Simulasi telah tamat. / Simulation has ended. Please reset to start a new simulation.",
            session_id=session_id,
            scam_ended=True,
            user_caught_scam=session["user_caught_scam"],
            report=None,
        )

    scenario = session["scenario"]
    turn = session["turn"]
    user_status = check_user_response(request.message)

    session["turn"] += 1

    # Check if user caught the scam
    if user_status == "caught":
        session["scam_ended"] = True
        session["user_caught_scam"] = True
        report = build_scam_report(scenario, "caught")

        caught_replies = [
            "...You caught me. This was indeed a simulation of a real scam. Well done for staying vigilant! 🎉",
            "Anda betul — ini adalah simulasi penipuan. Tahniah kerana berjaya mengenal pasti! You're right — this was a scam simulation. Congratulations!",
            "Simulation ended. You successfully identified the scam! In real life, this awareness could save you thousands of ringgit.",
        ]

        return SimulatorChatResponse(
            reply=random.choice(caught_replies),
            session_id=session_id,
            scam_ended=True,
            user_caught_scam=True,
            report=report,
        )

    # Check if user fell for the scam (gave money/details)
    if user_status == "falling" and turn >= 1:
        session["scam_ended"] = True
        session["user_caught_scam"] = False
        report = build_scam_report(scenario, "fell")

        fell_replies = [
            "Terima kasih! Saya akan proses sekarang... [SIMULATION ENDED] — Unfortunately, you fell for this scam. In real life, you would have lost money.",
            "Bagus! Saya akan hantar resit kepada anda... [SIMULATION ENDED] — This is where a real scammer would disappear with your money.",
            "Perfect. Processing now... [SIMULATION ENDED] — In a real scenario, the scammer would now vanish and you would lose your money.",
        ]

        return SimulatorChatResponse(
            reply=random.choice(fell_replies),
            session_id=session_id,
            scam_ended=True,
            user_caught_scam=False,
            report=report,
        )

    # Continue the scam — escalate based on turn
    if turn == 0:
        reply = scenario.get("escalation_1", scenario["intro"])
    elif turn == 1:
        reply = scenario.get("escalation_2", scenario["escalation_1"])
    else:
        # After 3+ turns of neutral responses, end the simulation
        if turn >= 3:
            session["scam_ended"] = True
            session["user_caught_scam"] = False
            report = build_scam_report(scenario, "fell")
            return SimulatorChatResponse(
                reply=(
                    "Saya rasa anda tidak akan bayar... [SIMULATION ENDED]\n\n"
                    "The simulation has ended after multiple exchanges. "
                    "Review the report to learn about the red flags in this scenario."
                ),
                session_id=session_id,
                scam_ended=True,
                user_caught_scam=False,
                report=report,
            )

        # Generic pressure responses
        pressure_responses = [
            "Masa semakin singkat! Anda perlu buat keputusan sekarang atau anda akan rugi. Time is running out! You need to decide now.",
            "Saya faham anda ragu-ragu, tapi ini peluang terakhir anda. I understand your hesitation, but this is your last chance.",
            "Ramai orang dah ambil tindakan dan mereka selamat. Many people have already acted and they are safe. Why are you hesitating?",
            "Supervisor saya kata kalau anda tak bayar dalam 10 minit, kes anda akan diserahkan kepada pihak berkuasa. My supervisor says if you don't pay in 10 minutes, your case will be escalated.",
        ]
        reply = random.choice(pressure_responses)

    return SimulatorChatResponse(
        reply=reply,
        session_id=session_id,
        scam_ended=False,
        user_caught_scam=False,
        report=None,
    )


@router.post("/reset", response_model=SimulatorResetResponse)
async def simulator_reset(request: SimulatorResetRequest):
    """
    Reset a simulator session to start a new scam scenario.
    """
    # Clear old session if provided
    if request.session_id and request.session_id in sessions:
        del sessions[request.session_id]

    new_session_id = str(uuid.uuid4())

    return SimulatorResetResponse(
        session_id=new_session_id,
        message="Session reset. Send any message to start a new simulation.",
    )
