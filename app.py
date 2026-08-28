import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from io import BytesIO
from google import genai
from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests
import streamlit as st

st.set_page_config(page_title="Birthday Wish Studio", page_icon="🎂", layout="wide")

st.title("🎂 Enterprise Birthday Wish Studio")
st.caption("Custom-crafted birthday greetings with high-res poster generation and real-time token metrics.")

# Setup Gemini API key
api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
client = genai.Client(api_key=api_key) if api_key else None

def get_font(size, bold=False):
    """Fetches a clean TrueType font dynamically to prevent tiny default bitmap text."""
    font_urls = {
        "bold": "https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat-Bold.ttf",
        "regular": "https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat-Medium.ttf"
    }
    url = font_urls["bold"] if bold else font_urls["regular"]
    try:
        res = requests.get(url, timeout=3)
        return ImageFont.truetype(BytesIO(res.content), size)
    except Exception:
        return ImageFont.load_default()

def draw_centered_text(draw, text, y, font, fill, canvas_width=800):
    """Draws horizontally centered text using bounding box coordinates."""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (canvas_width - text_width) // 2
    draw.text((x, y), text, font=font, fill=fill)

def generate_poster_card(name, role, hobbies, photo_url, company_name="MiTRAA TECH"):
    width, height = 800, 1150
    card = Image.new("RGB", (width, height), color="#FFFDF7")
    draw = ImageDraw.Draw(card)

    # 1. Fonts
    font_brand = get_font(22, bold=True)
    font_subtitle = get_font(20, bold=True)
    font_title = get_font(52, bold=True)
    font_name = get_font(42, bold=True)
    font_role = get_font(24, bold=False)
    font_wish_bold = get_font(22, bold=True)
    font_wish_body = get_font(18, bold=False)
    font_footer = get_font(20, bold=True)

    # 2. Rich Golden & Ruby Background Gradients
    for y in range(height):
        ratio = y / height
        r = int(255 - (ratio * 15))
        g = int(248 - (ratio * 30))
        b = int(230 - (ratio * 55))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # 3. Outer Decorative Frames
    draw.rounded_rectangle([25, 25, width - 25, height - 25], radius=32, outline="#B45309", width=4)
    draw.rounded_rectangle([36, 36, width - 36, height - 36], radius=24, outline="#F59E0B", width=2)

    # 4. Top Branding & Header
    draw_centered_text(draw, f"✦  {company_name.upper()}  ✦", 50, font_brand, "#9A3412", width)
    draw_centered_text(draw, "WISHING A VERY", 95, font_subtitle, "#D97706", width)
    draw_centered_text(draw, "HAPPY BIRTHDAY", 130, font_title, "#78350F", width)

    # 5. Colleague Portrait Frame
    photo_w, photo_h = 580, 440
    photo_x = (width - photo_w) // 2
    photo_y = 215

    # Shadow behind photo
    draw.rounded_rectangle([photo_x + 6, photo_y + 6, photo_x + photo_w + 6, photo_y + photo_h + 6], radius=24, fill="#E2E8F0")

    try:
        res = requests.get(photo_url, timeout=5)
        raw_pic = Image.open(BytesIO(res.content)).convert("RGB")
        fitted_pic = ImageOps.fit(raw_pic, (photo_w, photo_h), centering=(0.5, 0.5))
        
        mask = Image.new("L", (photo_w, photo_h), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([0, 0, photo_w, photo_h], radius=24, fill=255)
        card.paste(fitted_pic, (photo_x, photo_y), mask)
    except Exception:
        draw.rounded_rectangle([photo_x, photo_y, photo_x + photo_w, photo_y + photo_h], radius=24, fill="#FEF3C7")
        draw_centered_text(draw, "PHOTO", photo_y + 200, font_subtitle, "#92400E", width)

    # Border around portrait
    draw.rounded_rectangle([photo_x, photo_y, photo_x + photo_w, photo_y + photo_h], radius=24, outline="#D97706", width=3)

    # 6. Colleague Name & Role
    display_name = name.strip().title()
    display_role = role.strip().title()
    draw_centered_text(draw, display_name, 685, font_name, "#1E293B", width)
    draw_centered_text(draw, f"{display_role}", 745, font_role, "#B45309", width)

    # Golden Ornament Line
    draw.line([(width // 2 - 160, 790), (width // 2 + 160, 790)], fill="#F59E0B", width=2)

    # 7. Wish Card / Container Box
    box_rect = [70, 815, width - 70, 990]
    draw.rounded_rectangle(box_rect, radius=20, fill="#FFFFFF", outline="#FCD34D", width=2)
    
    draw_centered_text(draw, "May your day be filled with celebration, growth & joy!", 845, font_wish_bold, "#0F172A", width)
    draw_centered_text(draw, f"Celebrating your energy, passion for {hobbies},", 885, font_wish_body, "#475569", width)
    draw_centered_text(draw, "and all the amazing milestones you bring to the team!", 915, font_wish_body, "#475569", width)

    # 8. Bottom Corporate Signature Pill
    draw.rounded_rectangle([width // 2 - 170, 1025, width // 2 + 170, 1080], radius=18, fill="#991B1B")
    draw_centered_text(draw, f"From Team {company_name} 🎉", 1040, font_footer, "#FFFFFF", width)

    return card

def send_email_with_embedded_image(to_email, subject, message_body, image_card, sender_email, sender_password):
    """Sends HTML email with the high-res card embedded directly into the message body."""
    msg = MIMEMultipart("related")
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject

    msg_alternative = MIMEMultipart("alternative")
    msg.attach(msg_alternative)

    # HTML Body with referenced image attachment
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f8fafc; padding: 20px; text-align: center;">
        <div style="max-width: 600px; margin: auto; background-color: #ffffff; padding: 25px; border-radius: 12px; border: 1px solid #e2e8f0;">
          <h2 style="color: #991b1b; margin-bottom: 10px;">🎂 Happy Birthday!</h2>
          <p style="font-size: 16px; color: #334155; line-height: 1.6; text-align: left; margin-bottom: 20px;">
            {message_body.replace(chr(10), '<br>')}
          </p>
          <div style="margin-top: 15px;">
            <img src="cid:birthday_card" style="width: 100%; border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);" alt="Birthday Card" />
          </div>
          <p style="margin-top: 25px; font-size: 13px; color: #94a3b8;">
            Sent with warmest wishes from your team.
          </p>
        </div>
      </body>
    </html>
    """
    msg_alternative.attach(MIMEText(html_content, "html"))

    # Convert PIL Image to buffer and attach as inline CID
    img_buffer = BytesIO()
    image_card.save(img_buffer, format="JPEG", quality=95)
    img_buffer.seek(0)
    
    img_attachment = MIMEImage(img_buffer.read())
    img_attachment.add_header("Content-ID", "<birthday_card>")
    img_attachment.add_header("Content-Disposition", "inline", filename="birthday_card.jpg")
    msg.attach(img_attachment)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)

# Streamlit UI Layout
col_form, col_preview = st.columns([1, 1.2], gap="large")

with col_form:
    st.subheader("1. Birthday Colleague Profile")
    with st.form("birthday_builder"):
        company_name = st.text_input("Company / Brand Name", value="MiTRAA TECH")
        name = st.text_input("Colleague Name", value="Anthony Reddy")
        email = st.text_input("Colleague Email (Receive Greeting)", value="")
        role = st.text_input("Role / Designation", value="Software Developer")
        hobbies = st.text_input("Personal Passions / Hobbies", value="AI Engineering, Calisthenics, and Tech Innovations")
        photo_url = st.text_input(
            "Photo URL (Colleague Portrait)",
            value="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=800",
        )
        submit = st.form_submit_button("✨ Generate Birthday Card & Message")

if submit:
    prompt = f"""
    You are the HR Director at {company_name}.
    Write a warm, deeply personal, and enthusiastic 2-sentence birthday wish for {name}, our {role}.
    Subtly celebrate their work energy and their personal enthusiasm for {hobbies}.
    Keep it uplifting, authentic, and emotionally warm. Avoid robotic cliches.
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
            
            if hasattr(ai_resp, "usage_metadata") and ai_resp.usage_metadata:
                prompt_tokens = ai_resp.usage_metadata.prompt_token_count or 0
                candidate_tokens = ai_resp.usage_metadata.candidates_token_count or 0
                total_tokens = ai_resp.usage_metadata.total_token_count or (prompt_tokens + candidate_tokens)
        except Exception as e:
            st.error(f"AI Note: {e}")
            st.session_state["draft_msg"] = (
                f"Happy Birthday, {name}! Wishing you a phenomenal year packed with big milestones as our {role} and endless energy for {hobbies}. Have a wonderful celebration!"
            )
    else:
        st.session_state["draft_msg"] = (
            f"Happy Birthday, {name}! Wishing you a phenomenal year packed with big milestones as our {role} and endless energy for {hobbies}. Have a wonderful celebration!"
        )

    st.session_state["tokens"] = {
        "prompt": prompt_tokens,
        "candidate": candidate_tokens,
        "total": total_tokens
    }
    st.session_state["card"] = generate_poster_card(name, role, hobbies, photo_url, company_name)
    st.session_state["name"] = name
    st.session_state["email"] = email
    st.session_state["ready"] = True

with col_preview:
    if st.session_state.get("ready"):
        st.subheader("2. Real-Time Token Analytics")
        t_col1, t_col2, t_col3 = st.columns(3)
        tokens = st.session_state.get("tokens", {})
        t_col1.metric("Prompt Tokens", tokens.get("prompt", 0))
        t_col2.metric("Output Tokens", tokens.get("candidate", 0))
        t_col3.metric("Total Tokens", tokens.get("total", 0))

        st.divider()
        st.subheader("3. Final Poster & Email Preview")
        st.image(st.session_state["card"], caption="Generated High-Resolution Card", use_container_width=True)

        edited_message = st.text_area(
            "Draft Birthday Message Copy (Editable):", 
            value=st.session_state.get("draft_msg", ""),
            height=100
        )

        if st.button("🚀 Approve & Dispatch to Colleague"):
            sender_email = st.secrets.get("EMAIL_USER")
            sender_pass = st.secrets.get("EMAIL_PASS")
            target_email = st.session_state.get("email")
            emp_name = st.session_state.get("name")
            card_img = st.session_state.get("card")

            if sender_email and sender_pass and target_email:
                try:
                    send_email_with_embedded_image(
                        target_email,
                        f"🎉 Happy Birthday, {emp_name}!",
                        edited_message,
                        card_img,
                        sender_email,
                        sender_pass,
                    )
                    st.success(f"Birthday email and attached poster successfully delivered to {target_email}!")
                except Exception as e:
                    st.error(f"Delivery failed: {e}")
            else:
                st.info(f"Verified for {emp_name}. To dispatch directly to ({target_email or 'no email'}), ensure EMAIL_USER and EMAIL_PASS exist in Streamlit Secrets.")
