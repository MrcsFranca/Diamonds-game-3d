# carrega as texturas com pillow e enviadas a gpu como 2d
from pathlib import Path

from OpenGL.GL import *

TEXTURE_DIR = Path(__file__).resolve().parent / "assets" / "textures"
TEXTURE_FILES = {
    "floor": "stone_floor.png",
    "wall": "stone_wall.png",
    "wood": "wood.png",
    "background": "cave_background.png",
}

_textures: dict[str, int] = {}

def _configure_texture(texture_id: int) -> None:
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)


def _fallback_texture(colors: tuple[tuple[int, int, int], ...]) -> int:
    texture_id = int(glGenTextures(1))
    _configure_texture(texture_id)
    pixels = bytes(component for color in colors for component in color)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    glTexImage2D(
        GL_TEXTURE_2D,
        0,
        GL_RGB,
        2,
        2,
        0,
        GL_RGB,
        GL_UNSIGNED_BYTE,
        pixels,
    )
    glBindTexture(GL_TEXTURE_2D, 0)
    return texture_id

# carrega a imagem e cria a textura no OpenGL
def _load_image_texture(path: Path) -> int:
    from PIL import Image

    with Image.open(path) as source:
        image = source.convert("RGB").transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        width, height = image.size
        pixels = image.tobytes()

    texture_id = int(glGenTextures(1))
    _configure_texture(texture_id)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    glTexImage2D(
        GL_TEXTURE_2D,
        0,
        GL_RGB,
        width,
        height,
        0,
        GL_RGB,
        GL_UNSIGNED_BYTE,
        pixels,
    )
    glBindTexture(GL_TEXTURE_2D, 0)
    return texture_id

#carrega as texturas da mina; chamada após criar a janela GLUT
def load_textures(texture_dir: str | Path | None = None) -> dict[str, int]:
    global _textures

    directory = Path(texture_dir) if texture_dir is not None else TEXTURE_DIR
    fallback_colors = {
        "floor": ((82, 77, 67), (105, 99, 86), (91, 85, 74), (115, 107, 93)),
        "wall": ((65, 61, 56), (83, 77, 68), (73, 68, 61), (94, 87, 76)),
        "wood": ((83, 48, 24), (111, 68, 35), (95, 57, 29), (126, 78, 39)),
        "background": ((20, 17, 19), (36, 27, 25), (48, 31, 20), (25, 21, 24)),
    }

    loaded: dict[str, int] = {}
    for name, filename in TEXTURE_FILES.items():
        path = directory / filename
        try:
            if path.is_file():
                loaded[name] = _load_image_texture(path)
                print(f"Textura carregada: {path.name}")
            else:
                print(f"Aviso: {path.name} não encontrada; usando textura simples.")
                loaded[name] = _fallback_texture(fallback_colors[name])
        except Exception as error:
            print(f"Aviso: falha ao carregar {path.name}: {error}")
            loaded[name] = _fallback_texture(fallback_colors[name])

    _textures = loaded
    return dict(_textures)

#identificador do OpenGL da textura carregada
def get_texture(name: str) -> int | None:
    return _textures.get(name)

#descarrega as texturas
def unload_textures() -> None:
    global _textures
    if _textures:
        glDeleteTextures(list(_textures.values()))
        _textures = {}
