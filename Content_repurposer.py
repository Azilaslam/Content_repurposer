import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq
import json

# ----------------------------
# Setup
# ----------------------------
load_dotenv()

st.set_page_config(
    page_title="Script Repurposer",
    layout="centered"
)

st.title("♻️ YouTube Script Repurposer")
st.caption("Turn one long-form script into structured posts across platforms.")

# ----------------------------
# LLM
# ----------------------------
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.3
)

# ----------------------------
# CONSTANTS (MVP)
# ----------------------------
FREE_SCRIPT_LIMIT = 1
FREE_REDO_LIMIT = 3
UPI_ID = "9074474119@ybl"
PRICE = "499"

# ----------------------------
# Session state init
# ----------------------------
defaults = {
    "blocks": None,
    "twitter": None,
    "instagram": None,
    "linkedin": None,
    "email": None,
    "script_count": 0,
    "redo_count": 0,
    "paid": False,
    "show_paywall": False
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ----------------------------
# UI
# ----------------------------
script = st.text_area(
    "Paste full YouTube script",
    height=300,
    placeholder="Paste your full video script here..."
)

platforms = st.multiselect(
    "Select platforms to generate",
    ["Twitter / X", "Instagram Carousel", "LinkedIn Post", "Email Newsletter"]
)

# Free users: max 2 platforms
if not st.session_state.paid and len(platforms) > 2:
    st.warning("Free plan allows only 2 platforms.")
    platforms = platforms[:2]

tone = st.selectbox(
    "Tone",
    ["Neutral", "Casual", "Bold", "Professional"]
)

# ----------------------------
# STEP 1: Extract content blocks
# ----------------------------
def extract_blocks(script):
    prompt = f"""
Extract reusable content blocks from a YouTube script.

Rules:
- Do NOT add new ideas
- Use only information from the script

Return JSON with keys:
thesis
key_points
examples
one_liners
cta

SCRIPT:
{script}

Output ONLY valid JSON.
"""

    raw = llm.invoke(prompt).content.strip()

    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError
        return json.loads(raw[start:end])
    except Exception:
        st.error("❌ Failed to parse content blocks")
        st.code(raw)
        st.stop()

# ----------------------------
# Generators
# ----------------------------
def gen_twitter(blocks, tone):
    return llm.invoke(f"""
Create a Twitter/X thread (5–7 tweets).
Rules: short lines, no emojis, no hashtags.
CONTENT: {json.dumps(blocks)}
Tone: {tone}
""").content.strip()

def gen_instagram_carousel(blocks, tone):
    return llm.invoke(f"""
Create an Instagram carousel:
- 7–8 slides
- ONE sentence per slide
- MAX 70 characters
- No emojis or hashtags
- Slide 1 hook, last CTA
Also include caption.

CONTENT: {json.dumps(blocks)}
Tone: {tone}

Format:
SLIDES:
1. ...
CAPTION:
...
""").content.strip()

def gen_linkedin(blocks, tone):
    return llm.invoke(f"""
Write a LinkedIn post.
Rules: professional, line breaks, no emojis.
CONTENT: {json.dumps(blocks)}
Tone: {tone}
""").content.strip()

def gen_email(blocks, tone):
    return llm.invoke(f"""
Write a short email newsletter.
Rules: conversational, no hype, no emojis.
CONTENT: {json.dumps(blocks)}
Tone: {tone}
""").content.strip()

# ----------------------------
# Generate button
# ----------------------------
if st.button("🚀 Repurpose Script"):

    if not st.session_state.paid and st.session_state.script_count >= FREE_SCRIPT_LIMIT:
        st.session_state.show_paywall = True
        st.error("Free script limit reached. Upgrade to continue.")
        st.stop()

    if not script or not platforms:
        st.error("Paste a script and select platforms.")
        st.stop()

    st.session_state.blocks = extract_blocks(script)
    st.session_state.script_count += 1
    st.session_state.redo_count = 0

    for k in ["twitter", "instagram", "linkedin", "email"]:
        st.session_state[k] = None

    st.success("Content blocks extracted ✔️")

# ----------------------------
# Redo guard
# ----------------------------
def redo_guard():
    if not st.session_state.paid and st.session_state.redo_count >= FREE_REDO_LIMIT:
        st.session_state.show_paywall = True
        st.error("Redo limit reached. Upgrade for unlimited regenerations.")
        st.stop()
    st.session_state.redo_count += 1

# ----------------------------
# PAYWALL (ONLY WHEN TRIGGERED)
# ----------------------------
if st.session_state.show_paywall and not st.session_state.paid:
    st.divider()
    st.subheader("🔒 Upgrade to Pro")

    st.markdown(f"""
    **₹{PRICE} / month**

    Unlock:
    - Unlimited scripts
    - All platforms
    - Unlimited redo
    - Email newsletter
    """)

    st.markdown(
        f"[👉 Pay with GPay / UPI](upi://pay?pa={UPI_ID}&pn=Script%20Repurposer&am={PRICE}&cu=INR)",
        unsafe_allow_html=True
    )

    st.caption("After payment, click below to unlock.")

    if st.button("✅ I have paid"):
        st.session_state.paid = True
        st.session_state.show_paywall = False
        st.success("Pro unlocked 🎉")
        st.rerun()

# ----------------------------
# Outputs + Redo + Copy
# ----------------------------
blocks = st.session_state.blocks

if blocks:

    with st.expander("🔍 View extracted content blocks"):
        st.json(blocks)

    # Twitter
    if "Twitter / X" in platforms:
        st.subheader("🐦 Twitter / X Thread")
        if st.session_state.twitter is None:
            st.session_state.twitter = gen_twitter(blocks, tone)
        st.code(st.session_state.twitter)
        if st.button("🔄 Redo Twitter"):
            redo_guard()
            st.session_state.twitter = gen_twitter(blocks, tone)
            st.rerun()

    # Instagram
    if "Instagram Carousel" in platforms:
        st.subheader("📸 Instagram Carousel")
        if st.session_state.instagram is None:
            st.session_state.instagram = gen_instagram_carousel(blocks, tone)
        st.code(st.session_state.instagram)
        if st.button("🔄 Redo Instagram"):
            redo_guard()
            st.session_state.instagram = gen_instagram_carousel(blocks, tone)
            st.rerun()

    # LinkedIn
    if "LinkedIn Post" in platforms:
        st.subheader("💼 LinkedIn Post")
        if st.session_state.linkedin is None:
            st.session_state.linkedin = gen_linkedin(blocks, tone)
        st.code(st.session_state.linkedin)
        if st.button("🔄 Redo LinkedIn"):
            redo_guard()
            st.session_state.linkedin = gen_linkedin(blocks, tone)
            st.rerun()

    # Email (paid only)
    if "Email Newsletter" in platforms:
        if not st.session_state.paid:
            st.warning("Email newsletters are available on the Pro plan.")
        else:
            st.subheader("✉️ Email Newsletter")
            if st.session_state.email is None:
                st.session_state.email = gen_email(blocks, tone)
            st.code(st.session_state.email)
            if st.button("🔄 Redo Email"):
                redo_guard()
                st.session_state.email = gen_email(blocks, tone)
                st.rerun()
