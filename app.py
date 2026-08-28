import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import BytesIO
from google import genai
from PIL import Image, ImageDraw, ImageOps
import requests
import streamlit as st

st.set_page_config(page_title="HR Celebration Studio", page_icon="✨", layout="wide")

st.title("✨ Enterprise Celebration Studio")
st.caption("Generate publication-ready greeting posters with automated copy and live token analytics.")

# API Setup
api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
client = genai.Client(api_key=api_key) if api_key else None

def generate_poster_card(name, role, occasion, photo_url, company_name="MiTRAA TECH"):
    """Creates a high-res vertical celebration poster matching corporate poster aesthetics."""
    width, height = 800, 1200
    
    # 1. Warm Golden Gradient Background
    card = Image.new("RGB", (width, height), color="#FFFBEB")
    draw = ImageDraw.Draw(card)
    
    # Vertical golden glow gradient simulation
    for y in range(height):
        # Blend from warm gold at top to light ivory and back to rich gold at bottom
        ratio = y / height
        if ratio < 0.5:
            r = int(255 - (ratio * 20))
            g = int(245 - (ratio * 30))
            b = int(225 - (ratio * 60))
        else:
            r = int(245 + ((ratio - 0.5) * 15))
            g = int(230 - ((ratio - 0.5) * 50))
            b = int(195 - ((ratio - 0.5) * 100))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # 2. Ornate Outer & Inner Arch Borders
    draw.rounded_rectangle([30, 30, width - 30, height - 30], radius=40, outline="#D97706", width=3)
    draw.rounded_rectangle([45, 45, width - 45, height - 45], radius=32, outline="#FBBF24", width=1)

    # 3. Top Header / Company Branding
    draw.text((width // 2 - 120, 65), f"✦ {company_name.upper()} ✦", fill="#B45309")

    # 4. Main Event Header
    display_title = f"Happy {occasion}"
    draw.text((width // 2 - 140, 115), "CELEBRATING", fill="#D97706")
    draw.text((width // 2 - 180, 150), display_title, fill="#7C2D12")

    # 5. Rounded Main Illustration / Photo Window
    photo_w, photo_h = 600, 480
    photo_x, photo_y = (width - photo_w) // 2, 230
    
    try:
        res = requests.get(photo_url, timeout=5)
        raw_pic = Image.open(BytesIO(res.content)).convert("RGB")
        raw_pic = ImageOps.fit(raw_pic, (photo_w, photo_h), centering=(0.5, 0.5))
        
        # Rounded mask for central photo
        mask = Image.new("L", (photo_w, photo_h), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([0, 0, photo_w, photo_h], radius=28, fill=255)
        
        card.paste(raw_pic, (photo_x, photo_y), mask)
    except Exception:
        draw.rounded_rectangle([photo_x, photo_y, photo_x + photo_w, photo_y + photo_h], radius=28, fill="#FDE68A")
        draw.text((width // 2 - 40, photo_y + 220), "PHOTO", fill="#92400E")

    # Golden border around photo frame
    draw.rounded_rectangle([photo_x, photo_y, photo_x + photo_w, photo_y + photo_h], radius=28, outline="#D97706", width=3)

    # 6. Employee Details & Personal Greeting Section
    display_name = name.strip().title()
    display_role = role.strip().title()
    
    draw.text((width // 2 - 130, 740), display_name, fill="#1E293B")
    draw.text((width // 2 - 110, 785), f"Role: {display_role}", fill="#B45309")
    
    # Ornamental divider line
    draw.line([(width // 2 - 180, 830), (width // 2 + 180, 830)], fill="#F59E0B", width=2)
    draw.text((width // 2 - 10, 822), "✦", fill="#B45309")

    # 7. Bottom Blessing / Wish Badge
    badge_rect = [100, 860, width - 100, 1020]
    draw.rounded_rectangle(badge_rect, radius=20, fill="#FFFFFF", outline="#FDE68A", width=2)
    draw.text((width // 2 - 240, 890), "Wishing you joy, milestones, and shared success", fill="#475569")
    draw.text((width // 2 - 200, 930), "on this special milestone today and always!", fill="#64748B")
    
    # 8. Footer Badge
    draw.rounded_rectangle([width // 2 - 150, 1060, width // 2 + 150, 1110], radius=15, fill="#991B1B")
    draw.text((width // 2 - 90, 1075), f"From Team {company_name}", fill="#FFFFFF")

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

# Layout Columns
col_form, col_preview = st.columns([1, 1.2], gap="large")

with col_form:
    st.subheader("1. Employee & Event Details")
    with st.form("greeting_builder"):
        occasion = st.selectbox("Celebration Type", ["Birthday", "Work Anniversary", "Raksha Bandhan", "Promotion"])
        company_name = st.text_input("Company / Team Name", value="MiTRAA TECH")
        name = st.text_input("Colleague Name", value="Anthony Reddy")
        email = st.text_input("Colleague Email", value="")
        role = st.text_input("Designation / Role", value="Software Developer")
        hobbies = st.text_input("Key Highlights / Hobbies", value="AI Engineering, Calisthenics, and Team Building")
        photo_url = st.text_input(
            "Photo URL (Image / Portrait)",
            value="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=800",
        )
        submit = st.form_submit_button("⚡ Generate Studio Poster & Message")

if submit:
    prompt = f"""
    You are the Lead HR Director at {company_name}.
    Write a warm, celebratory, and genuinely uplifting 2-sentence {occasion} wish for {name}, our {role}.
    Highlight their positive impact and personal interest in {hobbies}.
    Avoid generic robotic cliches; make it thoughtful, concise, and celebratory.
    """

    prompt_tokens = 0
    candidate_tokens = 0
    total_tokens = 0

    if client:
        try:
            ai_resp = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
            )
            st.session_state["draft_msg"] = ai_resp.text.strip()
            
            # Extract Token Usage Metadata
            if hasattr(ai_resp, "usage_metadata") and ai_resp.usage_metadata:
                prompt_tokens = ai_resp.usage_metadata.prompt_token_count or 0
                candidate_tokens = ai_resp.usage_metadata.candidates_token_count or 0
                total_tokens = ai_resp.usage_metadata.total_token_count or (prompt_tokens + candidate_tokens)
        except Exception as e:
            st.error(f"AI Generation Note: {e}")
            st.session_state["draft_msg"] = (
                f"Happy {occasion}, {name}! Wishing you immense joy, continued breakthroughs as our {role}, and lots of energy for everything you love doing!"
            )
    else:
        st.session_state["draft_msg"] = (
            f"Happy {occasion}, {name}! Wishing you immense joy, continued breakthroughs as our {role}, and lots of energy for everything you love doing!"
        )

    st.session_state["tokens"] = {
        "prompt": prompt_tokens,
        "candidate": candidate_tokens,
        "total": total_tokens
    }
    st.session_state["card"] = generate_poster_card(name, role, occasion, photo_url, company_name)
    st.session_state["ready"] = True
    st.session_state["name"] = name
    st.session_state["email"] = email
    st.session_state["occasion"] = occasion

with col_preview:
    if st.session_state.get("ready"):
        st.subheader("2. Live Token Analytics")
        t_col1, t_col2, t_col3 = st.columns(3)
        tokens = st.session_state.get("tokens", {})
        t_col1.metric("Prompt Tokens", tokens.get("prompt", 0))
        t_col2.metric("Output Tokens", tokens.get("candidate", 0))
        t_col3.metric("Total Tokens Consumed", tokens.get("total", 0), help="Tracked from Gemini API response metadata")

        st.divider()
        st.subheader("3. Poster Preview & Review")
        st.image(st.session_state["card"], caption="Generated High-Resolution Celebration Poster", use_container_width=True)

        edited_message = st.text_area(
            "Draft Message Copy (Editable):", 
            value=st.session_state.get("draft_msg", ""),
            height=100
        )

        if st.button("🚀 Approve & Dispatch to Colleague"):
            sender_email = st.secrets.get("EMAIL_USER")
            sender_pass = st.secrets.get("EMAIL_PASS")
            target_email = st.session_state.get("email")
            occ = st.session_state.get("occasion")
            emp_name = st.session_state.get("name")

            if sender_email and sender_pass and target_email:
                try:
                    send_email(
                        target_email,
                        f"✨ Happy {occ}, {emp_name}!",
                        edited_message,
                        sender_email,
                        sender_pass,
                    )
                    st.success(f"Celebration email sent to {target_email}!")
                except Exception as e:
                    st.error(f"Delivery failed: {e}")
            else:
                st.info(f"Verification Mode: Greeting ready for {emp_name} ({target_email or 'no email entered'}). Add SMTP secrets to dispatch live.")
