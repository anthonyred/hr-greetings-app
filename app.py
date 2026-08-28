import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import BytesIO
from google import genai
import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests
import streamlit as st

st.set_page_config(page_title="HR Greeting Studio", page_icon="🎉", layout="centered")

st.title("🎉 Employee Birthday Greeting Studio")
st.caption("Generate bespoke, beautifully styled celebration cards and warm personal greetings.")

# Setup Gemini API key
api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
client = genai.Client(api_key=api_key) if api_key else None

def create_circular_avatar(image, size=(220, 220)):
    """Crops an image into a circle with an anti-aliased border mask."""
    image = ImageOps.fit(image, size, centering=(0.5, 0.5))
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + size, fill=255)
    
    output = Image.new("RGBA", size, (0, 0, 0, 0))
    output.paste(image, (0, 0))
    output.putalpha(mask)
    return output

def create_greeting_card(name, role, photo_url):
    """Generates an aesthetic, modern 1200x630 graphic card."""
    width, height = 1000, 520
    
    # Gradient-style vibrant dark backdrop
    card = Image.new("RGB", (width, height), color="#0F172A")
    draw = ImageDraw.Draw(card)
    
    # Decorative accent blocks / backdrop glow
    draw.rounded_rectangle([30, 30, width - 30, height - 30], radius=24, outline="#334155", width=2)
    draw.rectangle([30, 30, width - 30, 45], fill="#6366F1")  # Top indigo accent strip

    # Fetch and process employee photo
    avatar_size = (260, 260)
    avatar_pos = (70, 130)
    try:
        res = requests.get(photo_url, timeout=5)
        raw_pic = Image.open(BytesIO(res.content)).convert("RGBA")
        avatar = create_circular_avatar(raw_pic, size=avatar_size)
        
        # Outer ring around photo
        draw.ellipse([avatar_pos[0]-6, avatar_pos[1]-6, avatar_pos[0]+avatar_size[0]+6, avatar_pos[1]+avatar_size[1]+6], fill="#6366F1")
        card.paste(avatar, avatar_pos, avatar)
    except Exception:
        # Fallback circle if image fetch fails
        draw.ellipse([avatar_pos[0], avatar_pos[1], avatar_pos[0]+avatar_size[0], avatar_pos[1]+avatar_size[1]], fill="#334155")
        draw.text((avatar_pos[0]+70, avatar_pos[1]+110), "PHOTO", fill="#94A3B8")

    # Typography content
    title_text = "HAPPY BIRTHDAY!"
    display_name = name.strip().title()
    subtitle_text = f"Celebrating our wonderful {role.strip().title()}"
    tagline = "Wishing you a phenomenal year filled with joy, growth, and big wins!"

    # Draw Text blocks
    draw.text((380, 130), title_text, fill="#F59E0B")
    draw.text((380, 175), display_name, fill="#FFFFFF")
    draw.text((380, 240), subtitle_text, fill="#818CF8")
    draw.text((380, 300), tagline, fill="#94A3B8")
    
    # Subtle footer
    draw.text((380, 410), "From all of us at the team ✨", fill="#64748B")

    return card

def send_email(to_email, subject, message_body, sender_email, sender_password):
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(message_body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)

# Form
with st.form("employee_form"):
    name = st.text_input("Employee Name", value="Anthony Reddy")
    email = st.text_input("Employee Email", value="")
    role = st.text_input("Role", value="Software Developer")
    hobbies = st.text_input("Hobbies / Passions", value="Building AI apps, workout routines, and tech meetups")
    photo_url = st.text_input(
        "Photo URL",
        value="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400",
    )
    submit = st.form_submit_button("🚀 Generate Personalized Greeting")

if submit:
    prompt = f"""
    You are a thoughtful, friendly HR Director. 
    Write an engaging, energetic, and genuinely warm 2-sentence birthday greeting for {name}, our {role}.
    Mention their passion for {hobbies} in a natural, celebratory tone. 
    Avoid generic robotic filler like 'thank you for your hard work'. Make it feel authentic, cheerful, and personal!
    """

    if client:
        try:
            ai_resp = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
            )
            st.session_state["draft_msg"] = ai_resp.text.strip()
        except Exception as e:
            st.error(f"API Error: {e}")
            st.session_state["draft_msg"] = (
                f"Happy Birthday, {name}! We hope your special day is packed with great energy and everything you enjoy doing most. Cheers to another year of building awesome things as our {role}!"
            )
    else:
        st.session_state["draft_msg"] = (
            f"Happy Birthday, {name}! We hope your special day is packed with great energy and everything you enjoy doing most. Cheers to another year of building awesome things as our {role}!"
        )

    st.session_state["card"] = create_greeting_card(name, role, photo_url)
    st.session_state["ready"] = True

# Review & Approval Panel
if st.session_state.get("ready"):
    st.divider()
    st.subheader("HR Review & Dispatch")

    st.image(st.session_state["card"], caption="Dynamic Celebration Card")

    final_message = st.text_area(
        "Edit / Customize Greeting Copy:", value=st.session_state["draft_msg"], height=120
    )

    if st.button("✅ Approve & Send Email"):
        sender_email = st.secrets.get("EMAIL_USER")
        sender_pass = st.secrets.get("EMAIL_PASS")

        if sender_email and sender_pass and email:
            try:
                send_email(
                    email,
                    f"🎉 Happy Birthday, {name}!",
                    final_message,
                    sender_email,
                    sender_pass,
                )
                st.success(f"Greeting successfully delivered to {email}!")
            except Exception as e:
                st.error(f"Failed to send email: {e}")
        else:
            st.info(
                f"App verified for {name} ({email})! Add EMAIL_USER and EMAIL_PASS to Streamlit Secrets to dispatch live emails."
            )
