"""
ArchiDive — Configurações Globais
Centraliza todas as constantes e parâmetros do aplicativo.
"""

# ========== PARÂMETROS GEOMÉTRICOS ==========
POLYGON_MIN_AREA = 0.01  # Filtro de ruído mínimo em m²
POLYGON_POINTS_TOLERANCE = 0.001  # Tolerância para considerar pontos iguais em metros
STAIR_DETECTION_THRESHOLD = 0.65  # Score mínimo para detectar escadas (0-1)
DEFAULT_WALL_HEIGHT = 2.5  # Altura padrão das paredes em metros
WALL_HEIGHT_MIN = 0.5  # Altura mínima das paredes
WALL_HEIGHT_MAX = 10.0  # Altura máxima das paredes

# ========== ESCALA E CONVERSÃO ==========
DXF_DEFAULT_SCALE = 0.001  # Escala padrão para DXF (mm para metros)
DXF_UNIT_SCALES = {
    0: 0.001,      # Sem unidade (assume mm)
    1: 0.0254,     # Polegadas para metros
    2: 0.3048,     # Pés para metros
    4: 0.001,      # Milímetros para metros
    5: 0.01,       # Centímetros para metros
    6: 1.0,        # Metros (sem conversão)
}

# ========== VISUALIZAÇÃO 3D ==========
GRID_SIZE = 20  # Tamanho da grade de referência
GRID_STEP = 1  # Passo da grade
CAMERA_DEFAULT_ZOOM = -15.0
CAMERA_DEFAULT_ROT_X = 30.0
CAMERA_DEFAULT_ROT_Y = -45.0
CAMERA_TOP_ROT_X = 90.0
CAMERA_TOP_ROT_Y = 0.0
CAMERA_TOP_ZOOM = -20.0
CAMERA_FRONT_ROT_X = 0.0
CAMERA_FRONT_ROT_Y = 0.0
CAMERA_FRONT_ZOOM = -20.0

# ========== ILUMINAÇÃO ==========
LIGHT_PRIMARY_POS = [5.0, 10.0, 10.0, 1.0]  # Posição luz principal
LIGHT_PRIMARY_DIFFUSE = [0.85, 0.85, 0.90, 1.0]
LIGHT_PRIMARY_AMBIENT = [0.25, 0.25, 0.30, 1.0]
LIGHT_PRIMARY_SPECULAR = [0.3, 0.3, 0.3, 1.0]

LIGHT_SECONDARY_POS = [-5.0, -2.0, 3.0, 1.0]  # Posição luz secundária
LIGHT_SECONDARY_DIFFUSE = [0.1, 0.2, 0.35, 1.0]
LIGHT_SECONDARY_AMBIENT = [0.0, 0.0, 0.0, 1.0]

# ========== ANIMAÇÃO ==========
INTRO_ANIMATION_STEP = 0.02  # Incremento de opacidade por frame
INTRO_ANIMATION_INTERVAL = 16  # ms entre frames

# ========== INTERFACE - CORES ==========
COLORS = {
    "bg_dark":        "#0D0F14",
    "bg_panel":       "#13161C",
    "bg_card":        "#1A1E27",
    "bg_input":       "#1E2330",
    "accent":         "#00D4FF",
    "accent_dim":     "#0099BB",
    "accent_glow":    "#00D4FF44",
    "success":        "#00E5A0",
    "warning":        "#FFB800",
    "danger":         "#FF4D6A",
    "text_primary":   "#F0F4FF",
    "text_secondary": "#8892A4",
    "text_muted":     "#4A5568",
    "border":         "#252A36",
    "border_active":  "#00D4FF55",
    "wall_color":     (0.72, 0.78, 0.88),
    "floor_color":    (0.42, 0.52, 0.62),
    "ceiling_color":  (0.85, 0.87, 0.92),
    "outline_color":  (0.0, 0.83, 1.0),
    "grid_color":     (0.15, 0.18, 0.25),
    "stair_color":    (0.0, 0.83, 0.95),
    "obj_color":      (1.0, 0.6, 0.2),
}

# ========== INTERFACE - SIDEBAR ==========
SIDEBAR_WIDTH = 280
CAMERA_BAR_HEIGHT = 44
WINDOW_MIN_WIDTH = 1100
WINDOW_MIN_HEIGHT = 720
WINDOW_DEFAULT_WIDTH = 1300
WINDOW_DEFAULT_HEIGHT = 800

# ========== INTERFACE - FONTES ==========
FONT_FAMILY = "Segoe UI"
FONT_DEFAULT_SIZE = 10
FONT_MONOSPACE = "Courier New"

# ========== DETECÇÃO DE ESCADAS ==========
STAIR_KEYWORDS = {"escada", "stair", "degrau", "step", "circulação", "rampa", "sc", "st"}
STAIR_LINE_ANGLE_TOLERANCE = 0.05  # Radianos
STAIR_LINE_LENGTH_TOLERANCE = 0.3  # 30% de diferença aceitável
STAIR_MIN_LINES_PER_GROUP = 3  # Número mínimo de linhas para ser considerado escada

# ========== EXPORTAÇÃO ==========
OBJ_DECIMAL_PLACES = 6
MTL_WALL_AMBIENT = [0.8, 0.8, 0.8]
MTL_WALL_DIFFUSE = [0.9, 0.9, 0.9]
MTL_WALL_SPECULAR = [0.1, 0.1, 0.1]
MTL_WALL_SHININESS = 10

MTL_FLOOR_AMBIENT = [0.6, 0.5, 0.4]
MTL_FLOOR_DIFFUSE = [0.75, 0.65, 0.5]
MTL_FLOOR_SPECULAR = [0.05, 0.05, 0.05]
MTL_FLOOR_SHININESS = 5

MTL_CEILING_AMBIENT = [0.95, 0.95, 0.95]
MTL_CEILING_DIFFUSE = [1.0, 1.0, 1.0]
MTL_CEILING_SPECULAR = [0.0, 0.0, 0.0]
MTL_CEILING_SHININESS = 1

# ========== LOGGING ==========
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = "[%(asctime)s] %(levelname)s: %(message)s"
LOG_FILE = "archidive.log"

# ========== VERSÃO ==========
APP_VERSION = "1.0.1"
APP_NAME = "ArchiDive"
APP_ORGANIZATION = "ArchiDive"