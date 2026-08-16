# Genera el icono de la aplicacion: circulo azul con la letra C centrada en blanco
# Se ejecuta una sola vez durante el empaquetado, nunca al arrancar la aplicacion

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Tamano base del icono generado, en pixeles
ICON_SIZE = 256

# Colores tomados del acento de la paleta clara del sistema de diseno del proyecto
CIRCLE_COLOR = (0, 113, 227, 255)
BACKGROUND_COLOR = (255, 255, 255, 255)
LETTER_COLOR = (255, 255, 255, 255)

# Rutas de salida relativas a este archivo
OUTPUT_DIR = Path(__file__).resolve().parent
ICO_PATH = OUTPUT_DIR / "app.ico"
PNG_PATH = OUTPUT_DIR / "app.png"

# Tamanos incluidos en el .ico multi-resolucion
ICO_SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

# Rutas candidatas de fuente TrueType del sistema, en orden de preferencia
CANDIDATE_FONT_PATHS = (
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/arial.ttf",
)


# Genera el icono y lo guarda como .ico multi-resolucion y como .png
def generate_icon() -> None:
    image = _build_icon_image()
    image.save(PNG_PATH, format="PNG")
    image.save(ICO_PATH, format="ICO", sizes=ICO_SIZES)
    print("Icono generado en:", ICO_PATH, "y", PNG_PATH)


# Dibuja el circulo azul sobre fondo blanco con la letra C centrada en blanco
def _build_icon_image() -> Image.Image:
    image = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)
    margin = ICON_SIZE // 16
    draw.ellipse((margin, margin, ICON_SIZE - margin, ICON_SIZE - margin), fill=CIRCLE_COLOR)
    font = _load_letter_font()
    _draw_centered_letter(draw, "C", font)
    return image


# Carga la primera fuente TrueType disponible del sistema, o la fuente por defecto de Pillow
def _load_letter_font():
    font_size = int(ICON_SIZE * 0.55)
    for font_path in CANDIDATE_FONT_PATHS:
        if Path(font_path).exists():
            return ImageFont.truetype(font_path, font_size)
    return ImageFont.load_default(size=font_size)


# Centra la letra dada dentro del icono usando la caja delimitadora real del texto
def _draw_centered_letter(draw: ImageDraw.ImageDraw, letter: str, font) -> None:
    bounding_box = draw.textbbox((0, 0), letter, font=font)
    text_width = bounding_box[2] - bounding_box[0]
    text_height = bounding_box[3] - bounding_box[1]
    position_x = (ICON_SIZE - text_width) / 2 - bounding_box[0]
    position_y = (ICON_SIZE - text_height) / 2 - bounding_box[1]
    draw.text((position_x, position_y), letter, font=font, fill=LETTER_COLOR)


if __name__ == "__main__":
    generate_icon()
