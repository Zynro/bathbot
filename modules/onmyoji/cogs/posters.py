from PIL import Image, ImageDraw, ImageFont

TOP_LINE = "Join BubbleTea"
BOTTOM_LINE = """Level 7
24/7 Buff
70 GQ
Semi Casual
discord.gg/DbjMKYf"""
SIZE = 500, 500
BG = (255, 0, 0, 255)
FG = (0, 0, 255, 255)


def poster_image(filename):
    """ Takes an image with filename, creates a new file with _poster appended and our
    poster appended
    """
    im = Image.open(filename + ".png")
    # Resize image
    im = im.resize(SIZE, Image.LANCZOS)

    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype('fonts/comicsans.ttf', 40)

    width, height = draw.textsize(TOP_LINE, font=font)
    draw.text(((500 - width)/2.0, 0), TOP_LINE, font=font, fill=BG)
    draw.text(((500 - width)/2.0 + 5, 0), TOP_LINE, font=font, fill=FG)

    width, height = draw.textsize(BOTTOM_LINE, font=font)
    draw.multiline_text(((500 - width)/2.0, 240), BOTTOM_LINE, font=font, fill=BG, align="center")
    draw.multiline_text(((500 - width)/2.0 + 5, 240), BOTTOM_LINE, font=font, fill=FG, align="center")
    im.save(filename + '_poster.png', "PNG")


poster_image('emoji')
