def get_font(size, bold=False):
    """Loads guaranteed local Linux TrueType fonts without web requests."""
    font_candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "arial.ttf"  # Windows local fallback
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

def generate_poster_card(name, role, hobbies, photo_url, company_name="MiTRAA TECH"):
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
        draw_centered_text(draw, "PHOTO", photo_y + 190, font_subtitle, "#92400E", width)

    draw.rounded_rectangle([photo_x, photo_y, photo_x + photo_w, photo_y + photo_h], radius=24, outline="#D97706", width=3)

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
