import os
from io import BytesIO

import requests
import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps


# ----------------------------------------------------------------------------
# Poster generation logic
# ----------------------------------------------------------------------------

def get_font(size, bold=False):
    """Loads guaranteed local Linux TrueType fonts without web requests."""
    font_candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "arial.ttf",  # Windows local fallback
    ]
    for path in font_candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def draw_centered_text(draw, text, y, font, fill, canvas_width=800):
    """Calculates true center positioning using the font bounding box."""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (canvas_width - text_width) // 2
    draw.text((x, y), text, font=font, fill=fill)


def generate_poster_card(name, role, hobbies, photo_url=None, photo_image=None, company_name="MiTRAA TECH"):
    """
    Builds the birthday poster.
    Provide EITHER photo_url (a link Claude/requests can fetch) OR
    photo_image (a PIL.Image already loaded, e.g. from a file upload).
    """
    width, height = 800, 1200
    card = Image.new("RGB", (width, height), color="#FFFDF7")
    draw = ImageDraw.Draw(card)

    # 1. Guaranteed Large Scaled Fonts
    font_brand = get_font(26, bold=True)
    font_subtitle = get_font(24, bold=True)
    font_title = get_font(52, bold=True)
    font_name = get_font(44, bold=True)
    font_role = get_font(28, bold=False)
    font_wish_bold = get_font(24, bold=True)
    font_wish_body = get_font(20, bold=False)
    font_footer = get_font(24, bold=True)

    # 2. Rich Golden & Warm Gradient Backdrop
    for y in range(height):
        ratio = y / height
        r = int(255 - (ratio * 15))
        g = int(248 - (ratio * 25))
        b = int(225 - (ratio * 50))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # 3. Outer Decorative Frames
    draw.rounded_rectangle([25, 25, width - 25, height - 25], radius=32, outline="#B45309", width=4)
    draw.rounded_rectangle([36, 36, width - 36, height - 36], radius=24, outline="#F59E0B", width=2)

    # 4. Top Branding & Large Headers (Clean ASCII)
    draw_centered_text(draw, f"-- {company_name.upper()} --", 55, font_brand, "#9A3412", width)
    draw_centered_text(draw, "WISHING A VERY", 105, font_subtitle, "#D97706", width)
    draw_centered_text(draw, "HAPPY BIRTHDAY", 145, font_title, "#78350F", width)

    # 5. Colleague Portrait Frame
    photo_w, photo_h = 580, 430
    photo_x = (width - photo_w) // 2
    photo_y = 230

    # Soft Shadow
    draw.rounded_rectangle(
        [photo_x + 6, photo_y + 6, photo_x + photo_w + 6, photo_y + photo_h + 6],
        radius=24, fill="#E2E8F0",
    )

    try:
        if photo_image is not None:
            raw_pic = photo_image.convert("RGB")
        elif photo_url:
            res = requests.get(photo_url, timeout=5)
            raw_pic = Image.open(BytesIO(res.content)).convert("RGB")
        else:
            raise ValueError("No photo provided")

        fitted_pic = ImageOps.fit(raw_pic, (photo_w, photo_h), centering=(0.5, 0.5))

        mask = Image.new("L", (photo_w, photo_h), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([0, 0, photo_w, photo_h], radius=24, fill=255)
        card.paste(fitted_pic, (photo_x, photo_y), mask)
    except Exception:
        draw.rounded_rectangle(
            [photo_x, photo_y, photo_x + photo_w, photo_y + photo_h],
            radius=24, fill="#FEF3C7",
        )
        draw_centered_text(draw, "PHOTO", photo_y + 190, font_subtitle, "#92400E", width)

    draw.rounded_rectangle(
        [photo_x, photo_y, photo_x + photo_w, photo_y + photo_h],
        radius=24, outline="#D97706", width=3,
    )

    # 6. Colleague Name & Role
    display_name = name.strip().title()
    display_role = role.strip().title()
    draw_centered_text(draw, display_name, 690, font_name, "#1E293B", width)
    draw_centered_text(draw, f"Role: {display_role}", 750, font_role, "#B45309", width)

    # Golden Divider Line
    draw.line([(width // 2 - 160, 800), (width // 2 + 160, 800)], fill="#F59E0B", width=2)

    # 7. Wish Card Container Box
    box_rect = [60, 825, width - 60, 1010]
    draw.rounded_rectangle(box_rect, radius=20, fill="#FFFFFF", outline="#FCD34D", width=2)

    draw_centered_text(draw, "May your special day bring joy, health & success!", 860, font_wish_bold, "#0F172A", width)
    draw_centered_text(draw, f"Celebrating your work, passion for {hobbies},", 905, font_wish_body, "#475569", width)
    draw_centered_text(draw, "and all the great energy you share with our team!", 940, font_wish_body, "#475569", width)

    # 8. Bottom Corporate Pill
    draw.rounded_rectangle([width // 2 - 180, 1045, width // 2 + 180, 1105], radius=18, fill="#991B1B")
    draw_centered_text(draw, f"From Team {company_name}", 1060, font_footer, "#FFFFFF", width)

    return card


# ----------------------------------------------------------------------------
# Streamlit UI
# ----------------------------------------------------------------------------

st.set_page_config(page_title="HR Birthday Greetings", page_icon="🎂", layout="centered")

st.title("🎂 HR Birthday Poster Generator")
st.write("Fill in your colleague's details below and generate a personalized birthday poster.")

with st.form("poster_form"):
    company_name = st.text_input("Company name", value="MiTRAA TECH")
    name = st.text_input("Colleague's name", placeholder="e.g. Priya Sharma")
    role = st.text_input("Role / Designation", placeholder="e.g. Software Engineer")
    hobbies = st.text_input("Hobbies / Interests", placeholder="e.g. photography and travel")

    photo_source = st.radio("Photo source", ["Upload a photo", "Use an image URL"], horizontal=True)

    uploaded_file = None
    photo_url = None
    if photo_source == "Upload a photo":
        uploaded_file = st.file_uploader("Upload colleague's photo", type=["png", "jpg", "jpeg"])
    else:
        photo_url = st.text_input("Photo URL", placeholder="https://...")

    submitted = st.form_submit_button("Generate Poster")

if submitted:
    if not name or not role or not hobbies:
        st.error("Please fill in name, role, and hobbies before generating the poster.")
    else:
        with st.spinner("Generating poster..."):
            photo_image = None
            if uploaded_file is not None:
                photo_image = Image.open(uploaded_file)

            poster = generate_poster_card(
                name=name,
                role=role,
                hobbies=hobbies,
                photo_url=photo_url,
                photo_image=photo_image,
                company_name=company_name or "MiTRAA TECH",
            )

        st.success("Poster generated!")
        st.image(poster, caption=f"Happy Birthday, {name.strip().title()}!", use_container_width=True)

        buf = BytesIO()
        poster.save(buf, format="PNG")
        st.download_button(
            label="Download Poster",
            data=buf.getvalue(),
            file_name=f"birthday_{name.strip().replace(' ', '_').lower()}.png",
            mime="image/png",
        )
