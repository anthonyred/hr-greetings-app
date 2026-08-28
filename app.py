import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import os
from google import genai

# Setup Gemini Client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

st.set_page_config(page_title="Employee Greeting Hub", page_icon="🎉", layout="centered")

st.title("🎉 Automated Employee Greeting Hub")
st.write("Generate personalized birthday cards and messages with one click.")

# 1. Input Section
with st.container():
    st.subheader("1. Employee Details")
    col1, col2 = st.columns(2)
    with col1:
        emp_name = st.text_input("Employee Name", value="Alex Morgan")
        emp_role = st.text_input("Role / Department", value="UI/UX Designer")
    with col2:
        emp_email = st.text_input("Employee Email", value="test@example.com")
        emp_hobbies = st.text_input("Interests / Hobbies", value="Coffee enthusiast, marathon runner")
    
    photo_url = st.text_input("Employee Photo URL", value="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=400")

# 2. Image Customizer Function (Zero-cost dynamic card)
def generate_custom_card(image_url, name):
    # Download base photo
    response = requests.get(image_url)
    user_img = Image.open(BytesIO(response.content)).convert("RGB")
    user_img = user_img.resize((300, 300))
    
    # Create a blank festive card background (500x550)
    card = Image.new("RGB", (500, 550), color="#1E293B")
    draw = ImageDraw.Draw(card)
    
    # Paste employee photo onto the card
    card.paste(user_img, (100, 120))
    
    # Add Text Overlays
    draw.text((120, 40), "HAPPY BIRTHDAY!", fill="#FBBF24")
    draw.text((150, 450), f"Celebrating {name}!", fill="#FFFFFF")
    
    # Save to buffer
    buf = BytesIO()
    card.save(buf, format="PNG")
    buf.seek(0)
    return buf

# 3. AI Drafting
if st.button("Generate Greeting & Preview"):
    with st.spinner("Generating personalized message and card..."):
        prompt = f"Write a warm, concise, 2-sentence professional birthday message for {emp_name}, a {emp_role} who loves {emp_hobbies}."
        try:
    ai_resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    st.session_state["draft_msg"] = ai_resp.text.strip()
except Exception as e:
    st.error(f"API Error Details: {e}")
    # Fallback text so your demo doesn't crash
    st.session_state["draft_msg"] = f"Wishing you a fantastic birthday, {name}! Thank you for all your hard work as our {role}."
        
        st.session_state["draft_text"] = ai_resp.text.strip()
        st.session_state["card_buffer"] = generate_custom_card(photo_url, emp_name)

# 4. Review & Approval Section
if "draft_text" in st.session_state:
    st.divider()
    st.subheader("2. Review & Approval")
    
    # Allow HR to manually tweak the draft if needed
    final_message = st.text_area("Greeting Message (Editable)", value=st.session_state["draft_text"], height=100)
    st.image(st.session_state["card_buffer"], caption="Generated Customized Card", width=350)
    
    # 5. Send Action
    if st.button("🚀 Approve & Send Email"):
        # Configure SMTP (Set in secrets/environment)
        sender_email = os.environ.get("SENDER_EMAIL")
        sender_pass = os.environ.get("SENDER_APP_PASSWORD")
        
        msg = MIMEMultipart("related")
        msg["Subject"] = f"🎉 Happy Birthday, {emp_name}!"
        msg["From"] = sender_email
        msg["To"] = emp_email
        
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #333;">
            <h2>Happy Birthday, {emp_name}! 🎂</h2>
            <p style="font-size: 16px; line-height: 1.5;">{final_message}</p>
            <br/>
            <img src="cid:card_img" style="border-radius: 8px;" />
            <p style="color: #777; font-size: 12px; margin-top: 20px;">Warm wishes,<br>People Operations</p>
          </body>
        </html>
        """
        msg.attach(MIMEText(html_body, "html"))
        
        # Attach image inline
        st.session_state["card_buffer"].seek(0)
        img_part = MIMEImage(st.session_state["card_buffer"].read())
        img_part.add_header("Content-ID", "<card_img>")
        msg.attach(img_part)
        
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, sender_pass)
                server.send_message(msg)
            st.success(f"Greeting successfully sent to {emp_email}!")
        except Exception as e:
            st.error(f"Failed to send email: {e}")
