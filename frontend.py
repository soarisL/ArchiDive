"""
ArchiDive — Frontend
Interface gráfica profissional com tema escuro, visualizador 3D OpenGL e painel de controle.
"""

import os
import logging
from typing import List, Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QMessageBox, QDoubleSpinBox,
    QGroupBox, QCheckBox, QOpenGLWidget, QSplitter, QFrame,
    QProgressBar, QStatusBar, QAction, QMenuBar, QToolBar,
    QSizePolicy, QGridLayout, QSpacerItem, QScrollArea,
)
from PyQt5.QtCore import Qt, QPoint, QThread, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QPixmap, QCursor

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False

from config import COLORS, APP_NAME, APP_VERSION
from exceptions import NoGeometryError
from backend import Backend

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------
# Estilos (mesmos do original, apenas ajustados para novas cores)
# -----------------------------------------------------------------------
STYLE_MAIN = f"""
QMainWindow, QWidget {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', sans-serif;
}}
QMenuBar {{
    background-color: {COLORS['bg_panel']};
    color: {COLORS['text_primary']};
    border-bottom: 1px solid {COLORS['border']};
    padding: 2px;
    font-size: 13px;
}}
QMenuBar::item:selected {{
    background-color: {COLORS['bg_card']};
    border-radius: 4px;
}}
QMenu {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    color: {COLORS['text_primary']};
}}
QMenu::item:selected {{
    background-color: {COLORS['accent_dim']};
    border-radius: 4px;
    color: white;
}}
QStatusBar {{
    background-color: {COLORS['bg_panel']};
    color: {COLORS['text_secondary']};
    border-top: 1px solid {COLORS['border']};
    font-size: 12px;
}}
QScrollBar:vertical {{
    background: {COLORS['bg_panel']};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['border']};
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLORS['accent_dim']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
"""

STYLE_PANEL = f"""
QGroupBox {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;
    color: {COLORS['text_secondary']};
    letter-spacing: 1.2px;
    text-transform: uppercase;
    padding-top: 16px;
    margin-top: 8px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 14px;
    top: -2px;
    color: {COLORS['text_secondary']};
}}
QLabel {{
    color: {COLORS['text_secondary']};
    font-size: 13px;
}}
QLabel#value_label {{
    color: {COLORS['text_primary']};
    font-size: 22px;
    font-weight: 700;
}}
QLabel#unit_label {{
    color: {COLORS['text_muted']};
    font-size: 11px;
}}
QLabel#filename_label {{
    color: {COLORS['accent']};
    font-size: 12px;
    font-weight: 500;
}}
QLabel#section_title {{
    color: {COLORS['text_primary']};
    font-size: 13px;
    font-weight: 600;
}}
QDoubleSpinBox {{
    background-color: {COLORS['bg_input']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    color: {COLORS['text_primary']};
    padding: 6px 10px;
    font-size: 13px;
}}
QDoubleSpinBox:focus {{
    border: 1px solid {COLORS['accent']};
}}
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background-color: {COLORS['bg_card']};
    border: none;
    width: 18px;
}}
QCheckBox {{
    color: {COLORS['text_secondary']};
    font-size: 13px;
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    background-color: {COLORS['bg_input']};
}}
QCheckBox::indicator:checked {{
    background-color: {COLORS['accent']};
    border-color: {COLORS['accent']};
}}
QCheckBox:hover {{
    color: {COLORS['text_primary']};
}}
QProgressBar {{
    background-color: {COLORS['bg_input']};
    border: none;
    border-radius: 4px;
    height: 6px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background-color: {COLORS['accent']};
    border-radius: 4px;
}}
"""

STYLE_BUTTON_PRIMARY = f"""
QPushButton {{
    background-color: {COLORS['accent']};
    color: #000000;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.3px;
}}
QPushButton:hover {{
    background-color: #33DDFF;
}}
QPushButton:pressed {{
    background-color: {COLORS['accent_dim']};
}}
QPushButton:disabled {{
    background-color: {COLORS['border']};
    color: {COLORS['text_muted']};
}}
"""

STYLE_BUTTON_SECONDARY = f"""
QPushButton {{
    background-color: transparent;
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton:hover {{
    border-color: {COLORS['accent']};
    color: {COLORS['accent']};
    background-color: {COLORS['accent_glow']};
}}
QPushButton:pressed {{
    background-color: {COLORS['bg_card']};
}}
QPushButton:disabled {{
    color: {COLORS['text_muted']};
    border-color: {COLORS['border']};
}}
"""

STYLE_BUTTON_DANGER = f"""
QPushButton {{
    background-color: transparent;
    color: {COLORS['danger']};
    border: 1px solid {COLORS['danger']}55;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {COLORS['danger']}22;
    border-color: {COLORS['danger']};
}}
"""


# -----------------------------------------------------------------------
# Worker thread para processamento (com mensagens de progresso)
# -----------------------------------------------------------------------
class ProcessWorker(QThread):
    finished = pyqtSignal(list, list, list, list, list, str)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, str)  # (percentual, mensagem)

    def __init__(self, backend, gerar_escadas=False):
        super().__init__()
        self.backend = backend
        self.gerar_escadas = gerar_escadas

    def run(self):
        try:
            self.progress.emit(10, "Lendo DXF...")
            polygons = self.backend.extrair_paredes()
            self.progress.emit(40, f"Extraídos {len(polygons)} polígonos")
            if not polygons:
                self.error.emit("Nenhum polígono fechado encontrado no arquivo DXF.\n\nVerifique se o arquivo contém LWPOLYLINE ou POLYLINE fechadas.")
                return
            self.progress.emit(60, "Gerando geometria 3D...")
            walls, floors, ceilings, outlines, stairs = self.backend.criar_ambiente_3d(
                polygons, self.gerar_escadas
            )
            self.progress.emit(100, "Concluído!")
            self.finished.emit(walls, floors, ceilings, outlines, stairs, f"{len(polygons)} polígonos processados")
        except Exception as exc:
            logger.exception("Erro no worker de processamento")
            self.error.emit(str(exc))


# -----------------------------------------------------------------------
# Visualizador 3D OpenGL com VBOs e ajuste automático de câmera
# -----------------------------------------------------------------------
class Visualizador3D(QOpenGLWidget):
    def __init__(self, parent=None, backend=None):
        super().__init__(parent)
        self.backend = backend
        self.reset_state()
        self.setMinimumSize(500, 400)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.show_floors = True
        self.show_ceilings = True
        self.show_outlines = True
        self.show_grid = True
        self.show_stairs = True
        self.stairs = []
        self.obj_verts = []
        self.obj_faces = []
        # VBOs
        self.vbo_walls = None
        self.vbo_floors = None
        self.vbo_ceilings = None
        self.vbo_stairs = None
        self.vbo_outlines = None
        self.vbo_obj = None
        self._geometry_dirty = True  # flag para regenerar VBOs

        self._animate_intro = True
        self._intro_alpha = 0.0
        if OPENGL_AVAILABLE:
            self._intro_timer = QTimer(self)
            self._intro_timer.timeout.connect(self._tick_intro)
            self._intro_timer.start(16)

    def reset_state(self):
        self.walls, self.floors, self.ceilings, self.outlines = [], [], [], []
        self.rotacao_x = 30.0
        self.rotacao_y = -45.0
        self.zoom = -15.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.ultima_pos = QPoint()
        self._has_geometry = False
        self._geometry_dirty = True

    def _tick_intro(self):
        if self._animate_intro:
            self._intro_alpha = min(1.0, self._intro_alpha + 0.02)
            self.update()

    def fit_to_view(self, margin_factor: float = 1.5):
        """Ajusta câmera para enquadrar toda a geometria, centralizando na grade."""
        if not self._has_geometry or self.backend is None:
            return
        min_pt, max_pt = self.backend.get_bounding_box()
        center = [(min_pt[i] + max_pt[i]) * 0.5 for i in range(3)]
        # Calcula o tamanho da geometria
        size_x = max_pt[0] - min_pt[0]
        size_y = max_pt[1] - min_pt[1]
        size_z = max_pt[2] - min_pt[2]
        size = max(size_x, size_y, size_z, 0.01)
        
        # Campo de visão vertical padrão: 45 graus
        fov_rad = 45.0 * 3.14159 / 180.0
        # Distância necessária para que o objeto caiba na tela com margem
        distance = (size * 0.5) / (0.5 * fov_rad) * margin_factor
        # Garante uma distância mínima
        distance = max(distance, 5.0)
        self.zoom = -distance
        # Centraliza o pan de modo que o centro da geometria fique na origem da câmera
        self.pan_x = -center[0]
        self.pan_y = -center[1]
        # Reseta rotação para uma vista perspectiva agradável
        self.rotacao_x = 30.0
        self.rotacao_y = -45.0
        self.update()
        logger.info(f"Câmera ajustada: zoom={self.zoom:.2f}, pan=({self.pan_x:.2f}, {self.pan_y:.2f}), centro=({center[0]:.2f}, {center[1]:.2f}, {center[2]:.2f})")

    def initializeGL(self):
        if not OPENGL_AVAILABLE:
            return
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(0.051, 0.059, 0.078, 1.0)  # #0D0F14
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glShadeModel(GL_SMOOTH)

        # Luz principal
        glLightfv(GL_LIGHT0, GL_POSITION, [5.0, 10.0, 10.0, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.85, 0.85, 0.90, 1.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.25, 0.25, 0.30, 1.0])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [0.3, 0.3, 0.3, 1.0])
        # Luz secundária
        glLightfv(GL_LIGHT1, GL_POSITION, [-5.0, -2.0, 3.0, 1.0])
        glLightfv(GL_LIGHT1, GL_DIFFUSE, [0.1, 0.2, 0.35, 1.0])
        glLightfv(GL_LIGHT1, GL_AMBIENT, [0.0, 0.0, 0.0, 1.0])

    def _generate_vbos(self):
        """Gera VBOs para geometria estática (paredes, piso, teto, escadas, outlines)."""
        if not OPENGL_AVAILABLE:
            return
        # Limpa VBOs antigos
        for vbo in [self.vbo_walls, self.vbo_floors, self.vbo_ceilings, self.vbo_stairs, self.vbo_outlines]:
            if vbo is not None:
                glDeleteBuffers(1, [vbo])
        self.vbo_walls = self.vbo_floors = self.vbo_ceilings = self.vbo_stairs = self.vbo_outlines = None

        # Paredes (quads → triângulos)
        if self.walls:
            verts = []
            for wall in self.walls:
                # Triangulação do quad: (0,1,2) e (0,2,3)
                v0, v1, v2, v3 = wall
                verts.extend(v0 + v1 + v2)
                verts.extend(v0 + v2 + v3)
            arr = (GLfloat * len(verts))(*verts)
            self.vbo_walls = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_walls)
            glBufferData(GL_ARRAY_BUFFER, len(verts) * 4, arr, GL_STATIC_DRAW)
            glBindBuffer(GL_ARRAY_BUFFER, 0)

        # Piso (triângulos)
        if self.floors and self.floors[0]:
            verts = []
            floor_pts = self.floors[0]
            for i in range(1, len(floor_pts)-1):
                verts.extend(floor_pts[0] + floor_pts[i] + floor_pts[i+1])
            arr = (GLfloat * len(verts))(*verts)
            self.vbo_floors = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_floors)
            glBufferData(GL_ARRAY_BUFFER, len(verts) * 4, arr, GL_STATIC_DRAW)
            glBindBuffer(GL_ARRAY_BUFFER, 0)

        # Teto
        if self.ceilings and self.ceilings[0]:
            verts = []
            ceil_pts = self.ceilings[0]
            for i in range(1, len(ceil_pts)-1):
                verts.extend(ceil_pts[0] + ceil_pts[i] + ceil_pts[i+1])
            arr = (GLfloat * len(verts))(*verts)
            self.vbo_ceilings = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_ceilings)
            glBufferData(GL_ARRAY_BUFFER, len(verts) * 4, arr, GL_STATIC_DRAW)
            glBindBuffer(GL_ARRAY_BUFFER, 0)

        # Escadas
        if self.stairs:
            verts = []
            for step in self.stairs:
                v0, v1, v2, v3 = step
                verts.extend(v0 + v1 + v2)
                verts.extend(v0 + v2 + v3)
            arr = (GLfloat * len(verts))(*verts)
            self.vbo_stairs = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_stairs)
            glBufferData(GL_ARRAY_BUFFER, len(verts) * 4, arr, GL_STATIC_DRAW)
            glBindBuffer(GL_ARRAY_BUFFER, 0)

        # Outlines (arestas) - line loops, não VBO por simplicidade
        # Mantém desenho imediato

        self._geometry_dirty = False

    def paintGL(self):
        if not OPENGL_AVAILABLE:
            return
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(self.pan_x, self.pan_y, self.zoom)
        glRotatef(self.rotacao_x, 1.0, 0.0, 0.0)
        glRotatef(self.rotacao_y, 0.0, 1.0, 0.0)

        if self.show_grid:
            self._draw_grid()

        if not self._has_geometry:
            self._draw_placeholder()
            return

        alpha = self._intro_alpha if self._animate_intro else 1.0

        # Regenera VBOs se necessário
        if self._geometry_dirty:
            self._generate_vbos()

        # Desenha paredes com VBO
        if self.vbo_walls is not None:
            c = COLORS['wall_color']
            glColor4f(c[0], c[1], c[2], alpha)
            glEnableClientState(GL_VERTEX_ARRAY)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_walls)
            glVertexPointer(3, GL_FLOAT, 0, None)
            # número de triângulos = (número de vértices / 3)
            num_verts = self._get_vbo_size(self.vbo_walls) // (3 * 4)  # bytes por float
            glDrawArrays(GL_TRIANGLES, 0, num_verts)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            glDisableClientState(GL_VERTEX_ARRAY)

        # Piso
        if self.show_floors and self.vbo_floors is not None:
            glDisable(GL_LIGHTING)
            c = COLORS['floor_color']
            glColor4f(c[0], c[1], c[2], alpha * 0.85)
            glEnableClientState(GL_VERTEX_ARRAY)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_floors)
            glVertexPointer(3, GL_FLOAT, 0, None)
            num_verts = self._get_vbo_size(self.vbo_floors) // (3 * 4)
            glDrawArrays(GL_TRIANGLES, 0, num_verts)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            glDisableClientState(GL_VERTEX_ARRAY)
            glEnable(GL_LIGHTING)

        # Teto
        if self.show_ceilings and self.vbo_ceilings is not None:
            c = COLORS['ceiling_color']
            glColor4f(c[0], c[1], c[2], alpha * 0.4)
            glEnableClientState(GL_VERTEX_ARRAY)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_ceilings)
            glVertexPointer(3, GL_FLOAT, 0, None)
            num_verts = self._get_vbo_size(self.vbo_ceilings) // (3 * 4)
            glDrawArrays(GL_TRIANGLES, 0, num_verts)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            glDisableClientState(GL_VERTEX_ARRAY)

        # Escadas
        if self.show_stairs and self.vbo_stairs is not None:
            c = COLORS['stair_color']
            glColor4f(c[0], c[1], c[2], alpha)
            glEnableClientState(GL_VERTEX_ARRAY)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_stairs)
            glVertexPointer(3, GL_FLOAT, 0, None)
            num_verts = self._get_vbo_size(self.vbo_stairs) // (3 * 4)
            glDrawArrays(GL_TRIANGLES, 0, num_verts)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            glDisableClientState(GL_VERTEX_ARRAY)

        # Contornos (wireframe)
        if self.show_outlines:
            glDisable(GL_LIGHTING)
            glLineWidth(1.2)
            c = COLORS['outline_color']
            glColor4f(c[0], c[1], c[2], alpha * 0.5)
            for wall in self.outlines:
                glBegin(GL_LINE_LOOP)
                for v in wall:
                    glVertex3fv(v)
                glEnd()
            glEnable(GL_LIGHTING)

        # OBJ carregado
        if self.obj_verts and self.obj_faces:
            glDisable(GL_LIGHTING)
            glColor4f(1.0, 0.6, 0.2, alpha)
            glBegin(GL_TRIANGLES)
            for face in self.obj_faces:
                for idx in face:
                    if 0 <= idx < len(self.obj_verts):
                        glVertex3fv(self.obj_verts[idx])
            glEnd()
            glEnable(GL_LIGHTING)

    def _get_vbo_size(self, vbo_id):
        """Retorna o tamanho em bytes do buffer VBO."""
        glBindBuffer(GL_ARRAY_BUFFER, vbo_id)
        size = glGetBufferParameteriv(GL_ARRAY_BUFFER, GL_BUFFER_SIZE)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        return size

    def _draw_grid(self):
        glDisable(GL_LIGHTING)
        glLineWidth(1.0)
        gc = COLORS['grid_color']
        glColor4f(gc[0], gc[1], gc[2], 0.6)
        size = 20
        step = 1
        glBegin(GL_LINES)
        for i in range(-size, size + 1, step):
            glVertex3f(i, -size, 0)
            glVertex3f(i, size, 0)
            glVertex3f(-size, i, 0)
            glVertex3f(size, i, 0)
        glEnd()
        # Eixos
        glLineWidth(2.0)
        glColor4f(1.0, 0.3, 0.3, 0.7)
        glBegin(GL_LINES); glVertex3f(0,0,0); glVertex3f(3,0,0); glEnd()
        glColor4f(0.3, 1.0, 0.3, 0.7)
        glBegin(GL_LINES); glVertex3f(0,0,0); glVertex3f(0,3,0); glEnd()
        glColor4f(0.3, 0.5, 1.0, 0.7)
        glBegin(GL_LINES); glVertex3f(0,0,0); glVertex3f(0,0,3); glEnd()
        glEnable(GL_LIGHTING)

    def _draw_placeholder(self):
        glDisable(GL_LIGHTING)
        glColor4f(0.2, 0.5, 0.7, 0.3)
        glLineWidth(1.5)
        pts = [
            (-2,-2,0),(2,-2,0),(2,2,0),(-2,2,0),
            (-2,-2,3),(2,-2,3),(2,2,3),(-2,2,3),
        ]
        edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
        glBegin(GL_LINES)
        for a, b in edges:
            glVertex3fv(pts[a]); glVertex3fv(pts[b])
        glEnd()
        glEnable(GL_LIGHTING)

    def resizeGL(self, w, h):
        if not OPENGL_AVAILABLE:
            return
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, w / float(h or 1), 0.1, 500.0)
        glMatrixMode(GL_MODELVIEW)

    def mousePressEvent(self, event):
        self.ultima_pos = event.pos()

    def mouseMoveEvent(self, event):
        dx = event.x() - self.ultima_pos.x()
        dy = event.y() - self.ultima_pos.y()
        if event.buttons() == Qt.LeftButton:
            self.rotacao_x += dy * 0.4
            self.rotacao_y += dx * 0.4
            self.update()
        elif event.buttons() == Qt.RightButton:
            self.pan_x += dx * 0.02
            self.pan_y -= dy * 0.02
            self.update()
        self.ultima_pos = event.pos()

    def wheelEvent(self, event):
        self.zoom += event.angleDelta().y() * 0.015
        self.update()

    def load_geometry(self, walls, floors, ceilings, outlines, stairs=None, obj_verts=None, obj_faces=None):
        self.reset_state()
        self.walls, self.floors, self.ceilings, self.outlines = walls, floors, ceilings, outlines
        self.stairs = stairs or []
        self.obj_verts = obj_verts or []
        self.obj_faces = obj_faces or []
        self._has_geometry = True
        self._geometry_dirty = True
        self._animate_intro = True
        self._intro_alpha = 0.0
        self.update()
        # Ajusta a câmera automaticamente para centralizar e escalar o modelo
        self.fit_to_view()

    def reset_camera(self):
        self.rotacao_x = 30.0
        self.rotacao_y = -45.0
        self.zoom = -15.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.update()

    def set_top_view(self):
        self.rotacao_x = 90.0
        self.rotacao_y = 0.0
        self.zoom = -20.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.update()

    def set_front_view(self):
        self.rotacao_x = 0.0
        self.rotacao_y = 0.0
        self.zoom = -20.0
        self.update()


# -----------------------------------------------------------------------
# Card de estatística (mesmo do original)
# -----------------------------------------------------------------------
class StatCard(QFrame):
    def __init__(self, label: str, value: str = "—", unit: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("stat_card")
        self.setStyleSheet(f"""
            QFrame#stat_card {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 4px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)

        self.value_lbl = QLabel(value)
        self.value_lbl.setObjectName("value_label")
        self.value_lbl.setAlignment(Qt.AlignLeft)

        self.unit_lbl = QLabel(unit)
        self.unit_lbl.setObjectName("unit_label")

        self.label_lbl = QLabel(label.upper())
        self.label_lbl.setObjectName("unit_label")
        self.label_lbl.setStyleSheet(f"font-size: 10px; letter-spacing: 0.8px; color: {COLORS['text_muted']};")

        layout.addWidget(self.value_lbl)
        unit_row = QHBoxLayout()
        unit_row.addWidget(self.unit_lbl)
        unit_row.addStretch()
        layout.addLayout(unit_row)
        layout.addWidget(self.label_lbl)

    def update_value(self, value: str, unit: str = ""):
        self.value_lbl.setText(value)
        self.unit_lbl.setText(unit)


# -----------------------------------------------------------------------
# Janela principal
# -----------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self._worker = None
        self._setup_window()
        self._setup_menu()
        self._setup_ui()
        self._setup_statusbar()

    def _setup_window(self):
        self.setWindowTitle(f"{APP_NAME} — Planta Baixa para 3D / VR")
        self.setMinimumSize(1100, 720)
        self.resize(1300, 800)
        self.setStyleSheet(STYLE_MAIN + STYLE_PANEL)

    def _setup_menu(self):
        menubar = self.menuBar()
        # Arquivo
        file_menu = menubar.addMenu("Arquivo")
        act_open = QAction("Abrir DXF…", self); act_open.setShortcut("Ctrl+O")
        act_open.triggered.connect(self._abrir_arquivo)
        act_export_obj = QAction("Exportar OBJ…", self); act_export_obj.setShortcut("Ctrl+E")
        act_export_obj.triggered.connect(self._exportar_obj)
        act_export_gltf = QAction("Exportar glTF…", self)
        act_export_gltf.triggered.connect(self._exportar_gltf)
        act_quit = QAction("Sair", self); act_quit.setShortcut("Ctrl+Q")
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_open)
        file_menu.addSeparator()
        file_menu.addAction(act_export_obj)
        file_menu.addAction(act_export_gltf)
        file_menu.addSeparator()
        file_menu.addAction(act_quit)

        # Visualizar
        view_menu = menubar.addMenu("Visualizar")
        act_persp = QAction("Perspectiva", self); act_persp.triggered.connect(self._view_persp)
        act_top   = QAction("Vista Superior", self); act_top.triggered.connect(self._view_top)
        act_front = QAction("Vista Frontal", self); act_front.triggered.connect(self._view_front)
        view_menu.addAction(act_persp)
        view_menu.addAction(act_top)
        view_menu.addAction(act_front)

        # Ajuda
        help_menu = menubar.addMenu("Ajuda")
        act_about = QAction("Sobre ArchiDive", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- Painel lateral esquerdo ----
        sidebar = QWidget()
        sidebar.setFixedWidth(280)
        sidebar.setStyleSheet(f"background-color: {COLORS['bg_panel']}; border-right: 1px solid {COLORS['border']};")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 20, 16, 16)
        sidebar_layout.setSpacing(16)

        # Logo
        logo_lbl = QLabel("ArchiDive")
        logo_lbl.setStyleSheet(f"""
            font-size: 22px;
            font-weight: 800;
            color: {COLORS['accent']};
            letter-spacing: -0.5px;
        """)
        tagline = QLabel("Planta Baixa → 3D / VR")
        tagline.setStyleSheet(f"font-size: 11px; color: {COLORS['text_muted']}; margin-top: -4px;")
        sidebar_layout.addWidget(logo_lbl)
        sidebar_layout.addWidget(tagline)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {COLORS['border']}; margin: 4px 0;")
        sidebar_layout.addWidget(sep)

        # --- Grupo: Arquivo ---
        grp_file = QGroupBox("Arquivo DXF")
        grp_file_layout = QVBoxLayout(grp_file)
        grp_file_layout.setSpacing(8)

        self.btn_open = QPushButton("  Abrir DXF")
        self.btn_open.setStyleSheet(STYLE_BUTTON_PRIMARY)
        self.btn_open.setFixedHeight(40)
        self.btn_open.clicked.connect(self._abrir_arquivo)

        self.lbl_filename = QLabel("Nenhum arquivo carregado")
        self.lbl_filename.setObjectName("filename_label")
        self.lbl_filename.setWordWrap(True)
        self.lbl_filename.setStyleSheet(f"font-size: 11px; color: {COLORS['text_muted']};")

        grp_file_layout.addWidget(self.btn_open)
        grp_file_layout.addWidget(self.lbl_filename)
        sidebar_layout.addWidget(grp_file)

        # --- Grupo: Parâmetros ---
        grp_params = QGroupBox("Parâmetros")
        grp_params_layout = QGridLayout(grp_params)
        grp_params_layout.setSpacing(8)

        grp_params_layout.addWidget(QLabel("Altura das paredes"), 0, 0)
        height_row = QHBoxLayout()
        self.spin_height = QDoubleSpinBox()
        self.spin_height.setRange(0.5, 10.0)
        self.spin_height.setValue(2.5)
        self.spin_height.setSingleStep(0.1)
        self.spin_height.setDecimals(2)
        self.spin_height.setFixedWidth(90)
        height_row.addWidget(self.spin_height)
        height_row.addWidget(QLabel("m"))
        height_row.addStretch()
        grp_params_layout.addLayout(height_row, 1, 0)

        sidebar_layout.addWidget(grp_params)

        # --- Grupo: Camadas ---
        grp_layers = QGroupBox("Camadas")
        grp_layers_layout = QVBoxLayout(grp_layers)
        grp_layers_layout.setSpacing(6)
        self.cb_floors = QCheckBox("Exibir Piso")
        self.cb_ceilings = QCheckBox("Exibir Teto")
        self.cb_outlines = QCheckBox("Exibir Contornos")
        self.cb_grid = QCheckBox("Exibir Grade")
        self.cb_stairs_visibility = QCheckBox("Exibir Escadas")
        self.cb_stairs_detection = QCheckBox("Detectar Escadas (Híbrido)")
        self.cb_stairs_detection.setChecked(True)
        for cb in [self.cb_floors, self.cb_ceilings, self.cb_outlines, self.cb_grid, self.cb_stairs_visibility]:
            cb.setChecked(True)
            cb.stateChanged.connect(self._update_visibility)
        grp_layers_layout.addWidget(self.cb_floors)
        grp_layers_layout.addWidget(self.cb_ceilings)
        grp_layers_layout.addWidget(self.cb_outlines)
        grp_layers_layout.addWidget(self.cb_grid)
        grp_layers_layout.addWidget(self.cb_stairs_visibility)
        grp_layers_layout.addWidget(self.cb_stairs_detection)
        sidebar_layout.addWidget(grp_layers)

        # --- Ações principais ---
        self.btn_generate = QPushButton("  Gerar Ambiente 3D")
        self.btn_generate.setStyleSheet(STYLE_BUTTON_PRIMARY)
        self.btn_generate.setFixedHeight(44)
        self.btn_generate.clicked.connect(self._gerar_3d)
        sidebar_layout.addWidget(self.btn_generate)

        # Barra de progresso
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setVisible(False)
        self.progress.setFixedHeight(6)
        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        self.progress_label.setStyleSheet(f"font-size: 10px; color: {COLORS['text_muted']};")
        sidebar_layout.addWidget(self.progress_label)
        sidebar_layout.addWidget(self.progress)

        # Exportar
        export_row = QHBoxLayout()
        self.btn_export_obj = QPushButton("OBJ")
        self.btn_export_obj.setStyleSheet(STYLE_BUTTON_SECONDARY)
        self.btn_export_obj.setFixedHeight(36)
        self.btn_export_obj.setEnabled(False)
        self.btn_export_obj.clicked.connect(self._exportar_obj)

        self.btn_export_gltf = QPushButton("glTF")
        self.btn_export_gltf.setStyleSheet(STYLE_BUTTON_SECONDARY)
        self.btn_export_gltf.setFixedHeight(36)
        self.btn_export_gltf.setEnabled(False)
        self.btn_export_gltf.clicked.connect(self._exportar_gltf)

        self.btn_load_obj = QPushButton("📂 Carregar OBJ")
        self.btn_load_obj.setStyleSheet(STYLE_BUTTON_SECONDARY)
        self.btn_load_obj.setFixedHeight(36)
        self.btn_load_obj.clicked.connect(self._carregar_obj)
        export_row.addWidget(self.btn_load_obj)
        export_row.addWidget(self.btn_export_gltf)
        sidebar_layout.addLayout(export_row)

        self.btn_reset = QPushButton("Limpar Cena")
        self.btn_reset.setStyleSheet(STYLE_BUTTON_DANGER)
        self.btn_reset.setFixedHeight(36)
        self.btn_reset.clicked.connect(self._reset_scene)
        sidebar_layout.addWidget(self.btn_reset)

        sidebar_layout.addStretch()

        # --- Estatísticas ---
        grp_stats = QGroupBox("Estatísticas")
        stats_grid = QGridLayout(grp_stats)
        stats_grid.setSpacing(8)
        self.stat_polygons  = StatCard("Polígonos",  "—")
        self.stat_walls     = StatCard("Paredes",    "—")
        self.stat_wall_area = StatCard("Área Paredes", "—", "m²")
        self.stat_floor_area= StatCard("Área Piso",  "—", "m²")
        stats_grid.addWidget(self.stat_polygons,  0, 0)
        stats_grid.addWidget(self.stat_walls,     0, 1)
        stats_grid.addWidget(self.stat_wall_area, 1, 0)
        stats_grid.addWidget(self.stat_floor_area,1, 1)
        sidebar_layout.addWidget(grp_stats)

        # ---- Área 3D (direita) ----
        right_area = QWidget()
        right_layout = QVBoxLayout(right_area)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Toolbar de câmera
        cam_bar = QWidget()
        cam_bar.setFixedHeight(44)
        cam_bar.setStyleSheet(f"background-color: {COLORS['bg_panel']}; border-bottom: 1px solid {COLORS['border']};")
        cam_layout = QHBoxLayout(cam_bar)
        cam_layout.setContentsMargins(12, 0, 12, 0)
        cam_layout.setSpacing(8)
        lbl_view = QLabel("Câmera:")
        lbl_view.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        cam_layout.addWidget(lbl_view)

        for label, slot in [("Perspectiva", self._view_persp), ("Superior", self._view_top), ("Frontal", self._view_front)]:
            btn = QPushButton(label)
            btn.setFixedHeight(28)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLORS['text_secondary']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 5px;
                    padding: 0 12px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    border-color: {COLORS['accent']};
                    color: {COLORS['accent']};
                }}
            """)
            btn.clicked.connect(slot)
            cam_layout.addWidget(btn)

        cam_layout.addStretch()
        cam_help = QLabel("LMB: Rotacionar  |  RMB: Pan  |  Scroll: Zoom")
        cam_help.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        cam_layout.addWidget(cam_help)
        right_layout.addWidget(cam_bar)

        # Visualizador 3D
        if OPENGL_AVAILABLE:
            self.visualizador = Visualizador3D(backend=self.backend)
        else:
            self.visualizador = QLabel("OpenGL não disponível.\nInstale PyOpenGL para visualização 3D.")
            self.visualizador.setAlignment(Qt.AlignCenter)
            self.visualizador.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 14px;")

        right_layout.addWidget(self.visualizador)

        # Monta splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(sidebar)
        splitter.addWidget(right_area)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet(f"QSplitter::handle {{ background: {COLORS['border']}; }}")
        root.addWidget(splitter)

    def _setup_statusbar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Pronto. Abra um arquivo DXF para começar.")

    # ------------------------------------------------------------------
    # Ações
    # ------------------------------------------------------------------
    def _abrir_arquivo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir Arquivo DXF", "",
            "Arquivos CAD DXF (*.dxf);;Todos os arquivos (*)"
        )
        if not path:
            return
        ok, msg = self.backend.abrir_arquivo(path)
        if ok:
            self.lbl_filename.setText(os.path.basename(path))
            self.lbl_filename.setStyleSheet(f"font-size: 11px; color: {COLORS['accent']};")
            self.status.showMessage(f"Arquivo carregado: {os.path.basename(path)}")
            logger.info(f"Arquivo carregado: {path}")
        else:
            QMessageBox.critical(self, "Erro ao Abrir", msg)
            self.status.showMessage("Erro ao carregar arquivo.")

    def _gerar_3d(self):
        if not self.backend.documento_dxf:
            QMessageBox.warning(self, "Arquivo não carregado", "Abra um arquivo DXF antes de gerar o ambiente 3D.")
            return

        self.backend.altura_parede = self.spin_height.value()
        self.btn_generate.setEnabled(False)
        self.progress.setVisible(True)
        self.progress_label.setVisible(True)
        self.progress.setValue(0)
        self.progress_label.setText("Iniciando...")
        self.status.showMessage("Processando geometria…")

        self._worker = ProcessWorker(self.backend, gerar_escadas=self.cb_stairs_detection.isChecked())
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_generate_done)
        self._worker.error.connect(self._on_generate_error)
        self._worker.start()

    def _on_progress(self, percent, msg):
        self.progress.setValue(percent)
        self.progress_label.setText(msg)

    def _on_generate_done(self, walls, floors, ceilings, outlines, stairs, msg):
        self.btn_generate.setEnabled(True)
        self.progress.setVisible(False)
        self.progress_label.setVisible(False)
        if OPENGL_AVAILABLE:
            self.visualizador.show_floors = self.cb_floors.isChecked()
            self.visualizador.show_ceilings = self.cb_ceilings.isChecked()
            self.visualizador.show_outlines = self.cb_outlines.isChecked()
            self.visualizador.show_grid = self.cb_grid.isChecked()
            self.visualizador.show_stairs = self.cb_stairs_visibility.isChecked()
            self.visualizador.load_geometry(walls, floors, ceilings, outlines, stairs)

        self.btn_export_obj.setEnabled(True)
        self.btn_export_gltf.setEnabled(True)

        stats = self.backend.get_stats()
        self.stat_polygons.update_value(str(stats["poligonos"]))
        self.stat_walls.update_value(str(stats["paredes"]))
        self.stat_wall_area.update_value(str(stats["area_paredes_m2"]), "m²")
        self.stat_floor_area.update_value(str(stats["area_piso_m2"]), "m²")

        self.status.showMessage(f"✓ Ambiente 3D gerado — {msg}")
        logger.info(f"Ambiente 3D gerado: {stats}")

    def _on_generate_error(self, msg):
        self.btn_generate.setEnabled(True)
        self.progress.setVisible(False)
        self.progress_label.setVisible(False)
        QMessageBox.warning(self, "Aviso de Processamento", msg)
        self.status.showMessage("Processamento finalizado com avisos.")

    def _exportar_obj(self):
        if not self.backend.walls and not self.backend.floors and not self.backend.stairs:
            QMessageBox.warning(self, "Sem geometria", "Gere o ambiente 3D antes de exportar.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar OBJ", "archidive_export.obj",
            "Wavefront OBJ (*.obj)"
        )
        if not path:
            return
        try:
            self.backend.export_as_obj(path)
            QMessageBox.information(self, "Exportação Concluída",
                f"Modelo OBJ exportado com sucesso!\n\n{path}\n\nUm arquivo .mtl com materiais foi gerado no mesmo diretório.")
            self.status.showMessage(f"OBJ exportado: {os.path.basename(path)}")
            logger.info(f"OBJ exportado: {path}")
        except NoGeometryError as e:
            QMessageBox.warning(self, "Sem geometria", str(e))
        except Exception as exc:
            logger.exception("Erro na exportação OBJ")
            QMessageBox.critical(self, "Erro de Exportação", str(exc))

    def _exportar_gltf(self):
        if not self.backend.walls and not self.backend.floors and not self.backend.stairs:
            QMessageBox.warning(self, "Sem geometria", "Gere o ambiente 3D antes de exportar.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar glTF", "archidive_export.gltf",
            "glTF 2.0 (*.gltf)"
        )
        if not path:
            return
        try:
            self.backend.export_as_gltf(path)
            QMessageBox.information(self, "Exportação Concluída",
                f"Modelo glTF exportado!\n\n{path}\n\nCompatível com motores VR (Unity, Unreal, A-Frame, Blender).")
            self.status.showMessage(f"glTF exportado: {os.path.basename(path)}")
            logger.info(f"glTF exportado: {path}")
        except NoGeometryError as e:
            QMessageBox.warning(self, "Sem geometria", str(e))
        except Exception as exc:
            logger.exception("Erro na exportação glTF")
            QMessageBox.critical(self, "Erro de Exportação", f"Erro ao exportar glTF:\n{exc}")

    def _update_visibility(self):
        if OPENGL_AVAILABLE and hasattr(self.visualizador, 'show_floors'):
            self.visualizador.show_floors = self.cb_floors.isChecked()
            self.visualizador.show_ceilings = self.cb_ceilings.isChecked()
            self.visualizador.show_outlines = self.cb_outlines.isChecked()
            self.visualizador.show_grid = self.cb_grid.isChecked()
            self.visualizador.show_stairs = self.cb_stairs_visibility.isChecked()
            self.visualizador.update()

    def _reset_scene(self):
        reply = QMessageBox.question(self, "Limpar Cena",
            "Isso removerá a geometria atual. Continuar?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if OPENGL_AVAILABLE:
                self.visualizador.reset_state()
                self.visualizador.update()
                self.visualizador.fit_to_view()   # re-centraliza (mostrará apenas grade)
            self.backend.walls = []
            self.backend.floors = []
            self.backend.ceilings = []
            self.backend.outlines = []
            self.backend.stairs = []
            self.btn_export_obj.setEnabled(False)
            self.btn_export_gltf.setEnabled(False)
            for s in [self.stat_polygons, self.stat_walls, self.stat_wall_area, self.stat_floor_area]:
                s.update_value("—")
            self.status.showMessage("Cena limpa.")
            logger.info("Cena limpa pelo usuário")

    def _view_persp(self):
        if OPENGL_AVAILABLE and hasattr(self.visualizador, 'reset_camera'):
            self.visualizador.reset_camera()

    def _view_top(self):
        if OPENGL_AVAILABLE and hasattr(self.visualizador, 'set_top_view'):
            self.visualizador.set_top_view()

    def _view_front(self):
        if OPENGL_AVAILABLE and hasattr(self.visualizador, 'set_front_view'):
            self.visualizador.set_front_view()

    def _show_about(self):
        QMessageBox.about(self, "Sobre ArchiDive",
            f"<h2 style='color:#00D4FF'>ArchiDive v{APP_VERSION}</h2>"
            "<p>Conversor profissional de plantas baixas DXF para ambientes 3D e VR.</p>"
            "<p><b>Funcionalidades:</b><br>"
            "• Leitura de arquivos .DXF (AutoCAD, LibreCAD, etc.)<br>"
            "• Geração automática de paredes, piso e teto<br>"
            "• Detecção e visualização de escadas<br>"
            "• Visualizador 3D interativo com iluminação<br>"
            "• Exportação OBJ (com materiais .mtl)<br>"
            "• Exportação glTF 2.0 (Unity, Unreal, A-Frame, Blender)</p>"
            "<p style='color:#8892A4'>Desenvolvido com Python, PyQt5 e OpenGL.</p>"
        )

    def _carregar_obj(self):
        path, _ = QFileDialog.getOpenFileName(self, "Carregar OBJ para Visualização", "", "Wavefront OBJ (*.obj)")
        if not path:
            return
        try:
            verts, faces = self.backend.carregar_obj(path)
            if not verts:
                QMessageBox.warning(self, "Arquivo Vazio", "O OBJ não contém vértices válidos.")
                return
            if OPENGL_AVAILABLE:
                self.visualizador.obj_verts = verts
                self.visualizador.obj_faces = faces
                self.visualizador.update()
            self.status.showMessage(f"OBJ carregado: {os.path.basename(path)} ({len(verts)} vértices)")
            logger.info(f"OBJ carregado: {path} com {len(verts)} vértices")
        except Exception as exc:
            logger.exception("Erro ao carregar OBJ")
            QMessageBox.critical(self, "Erro ao Carregar OBJ", str(exc))