import os
from io import BytesIO
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from google import genai
import pandas as pd
from PIL import Image, ImageDraw
import requests
import streamlit as st

st.set_page_config(page_title="HR Greeting Assistant", page_icon="🎉", layout="centered")

st.title("🎉 Employee Birthday Greeting Assistant")
st.write("Generate, review, and approve personalized greetings with one click.")

# Setup Gemini API key from Streamlit Secrets or Environment
api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
client = genai.Client(api_key=api_key) if api_key else None


def create_greeting_card(name, photo_url):
    img = Image.new("RGB", (600, 350), color="#1E293B")
    draw = ImageDraw.Draw(img)

    try:
        res = requests.get(photo_url, timeout=5)
        emp_pic = Image.open(BytesIO(res.content)).resize((180, 180))
        img.paste(emp_pic, (40, 85))
    except Exception:
        pass

    draw.text((250, 90), "HAPPY BIRTHDAY!", fill="#F59E0B")
    draw.text((250, 130), name, fill="#FFFFFF")
    draw.text((250, 170), "Wishing you a wonderful year ahead!", fill="#94A3B8")

    return img


def send_email(to_email, subject, message_body, sender_email, sender_password):
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(message_body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)


# Input Form
with st.form("employee_form"):
    name = st.text_input("Employee Name", value="Alex")
    email = st.text_input("Employee Email", value="")
    role = st.text_input("Role", value="UI/UX Designer")
    hobbies = st.text_input("Hobbies / Interests", value="Photography & Coffee")
    photo_url = st.text_input(
        "Photo URL",
        value="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400",
    )
    submit = st.form_submit_button("Generate Draft")

if submit:
    prompt = f"Write a warm, uplifting 2-sentence birthday greeting for {name}, who is a {role} and enjoys {hobbies}."

    if client:
        try:
            ai_resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            st.session_state["draft_msg"] = ai_resp.text.strip()
        except Exception as e:
            st.error(f"API Error: {e}")
            st.session_state["draft_msg"] = (
                f"Wishing you a fantastic birthday, {name}! Thank you for all your hard work as our {role}."
            )
    else:
        st.session_state["draft_msg"] = (
            f"Wishing you a fantastic birthday, {name}! Thank you for all your hard work as our {role}."
        )

    st.session_state["card"] = create_greeting_card(name, photo_url)
    st.session_state["ready"] = True

# Review and Send Screen
if st.session_state.get("ready"):
    st.divider()
    st.subheader("HR Review & Approval")

    st.image(st.session_state["card"], caption="Generated Greeting Card")

    final_message = st.text_area(
        "Review / Edit Greeting Message:", value=st.session_state["draft_msg"]
    )

    if st.button("✅ Approve & Send Email"):
        sender_email = st.secrets.get("EMAIL_USER")
        sender_pass = st.secrets.get("EMAIL_PASS")

        if sender_email and sender_pass and email:
            try:
                send_email(
                    email,
                    f"🎉 Happy Birthday {name}!",
                    final_message,
                    sender_email,
                    sender_pass,
                )
                st.success(f"Greeting successfully sent to {email}!")
            except Exception as e:
                st.error(f"Failed to send email: {e}")
        else:
            st.info(
                f"Demo Mode: Email approved for {name} ({email})! Configure SMTP credentials in secrets to send live."
            )
