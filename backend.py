"""
ArchiDive — Backend
Responsável por:
  - Leitura de arquivos DXF
  - Extração e limpeza de polígonos
  - Geração de geometria 3D (paredes, piso, teto, escadas)
  - Exportação OBJ e glTF/GLB
"""

import os
import logging
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import ezdxf
from ezdxf import DXFStructureError, DXFVersionError

from config import (
    POLYGON_MIN_AREA, STAIR_DETECTION_THRESHOLD, STAIR_KEYWORDS,
    MTL_WALL_AMBIENT, MTL_WALL_DIFFUSE, MTL_WALL_SPECULAR, MTL_WALL_SHININESS,
    MTL_FLOOR_AMBIENT, MTL_FLOOR_DIFFUSE, MTL_FLOOR_SPECULAR, MTL_FLOOR_SHININESS,
    MTL_CEILING_AMBIENT, MTL_CEILING_DIFFUSE, MTL_CEILING_SPECULAR, MTL_CEILING_SHININESS,
    OBJ_DECIMAL_PLACES
)
from exceptions import DXFFileError, DXFFileNotFound, DXFFileCorrupted, DXFNoPolygonsFound, ExportError, NoGeometryError

# pygltflib é opcional; se não tiver instalado, apenas OBJ fica disponível
try:
    from pygltflib import (
        GLTF2, Scene, Node, Mesh, Primitive, Attributes,
        Buffer, BufferView, Accessor,
        FLOAT, UNSIGNED_INT, ARRAY_BUFFER, ELEMENT_ARRAY_BUFFER,
    )
    GLTF_AVAILABLE = True
except ImportError:
    GLTF_AVAILABLE = False

logger = logging.getLogger(__name__)


class Backend:
    """Motor de processamento de plantas baixas DXF → 3D."""

    def __init__(self, altura_parede: float = 2.5):
        self.altura_parede = altura_parede
        self.documento_dxf = None
        self.caminho_arquivo = ""
        self.escala = 0.001
        # Geometrias geradas
        self.polygons: List[List[Tuple[float, float]]] = []  # polígonos 2D limpos
        self.walls: List[List[List[float]]] = []
        self.floors: List[List[List[float]]] = []
        self.ceilings: List[List[List[float]]] = []
        self.outlines: List[List[List[float]]] = []
        self.stairs: List[List[List[float]]] = []  # escadas (quads)
        # Centro dos polígonos (para translação)
        self._polygons_center = (0.0, 0.0)

    # ------------------------------------------------------------------
    # Leitura DXF
    # ------------------------------------------------------------------
    def abrir_arquivo(self, caminho: str) -> Tuple[bool, str]:
        """Abre um arquivo DXF e retorna (ok: bool, mensagem: str)."""
        try:
            self.documento_dxf = ezdxf.readfile(caminho)
            self.caminho_arquivo = caminho
            # Detecta unidade do arquivo
            units = self.documento_dxf.units
            # ezdxf: 0=sem unidade,1=polegada,2=pé,4=mm,5=cm,6=m
            scale_map = {
                0: 0.001, 1: 0.0254, 2: 0.3048, 4: 0.001, 5: 0.01, 6: 1.0
            }
            self.escala = scale_map.get(units, 0.001)
            logger.info(f"Arquivo carregado: {caminho}, escala={self.escala}")
            return True, f"Arquivo carregado com sucesso!\nUnidade detectada: escala={self.escala}"
        except FileNotFoundError:
            logger.error(f"Arquivo não encontrado: {caminho}")
            return False, f"Arquivo não encontrado:\n{caminho}"
        except (DXFStructureError, DXFVersionError) as exc:
            logger.error(f"Erro de estrutura DXF: {exc}")
            return False, f"Arquivo DXF corrompido ou versão incompatível:\n{exc}"
        except Exception as exc:
            logger.error(f"Erro inesperado ao abrir DXF: {exc}")
            return False, f"Erro ao carregar arquivo:\n{exc}"

    # ------------------------------------------------------------------
    # Helpers geométricos
    # ------------------------------------------------------------------
    @staticmethod
    def points_equal(p1: Tuple[float, float], p2: Tuple[float, float], tol: float = 0.001) -> bool:
        return abs(p1[0] - p2[0]) < tol and abs(p1[1] - p2[1]) < tol

    @staticmethod
    def cross(o: Tuple[float, float], a: Tuple[float, float], b: Tuple[float, float]) -> float:
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    def clean_polygon(self, polygon: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Remove pontos duplicados consecutivos e fecha o polígono."""
        if not polygon:
            return []
        clean = []
        for i, p in enumerate(polygon):
            if i == 0 or not self.points_equal(p, polygon[i - 1]):
                clean.append(p)
        if len(clean) > 2 and not self.points_equal(clean[0], clean[-1]):
            clean.append(clean[0])
        return clean

    def convex_hull(self, points: List[Tuple[float, float]]) -> Optional[List[Tuple[float, float]]]:
        """Calcula o fecho convexo usando monotone chain."""
        if len(points) < 3:
            return None
        pts = sorted(set(points))  # Ordena e remove duplicados
        if len(pts) < 2:
            return None
        lower = []
        for p in pts:
            while len(lower) >= 2 and self.cross(lower[-2], lower[-1], p) <= 0:
                lower.pop()
            lower.append(p)
        upper = []
        for p in reversed(pts):
            while len(upper) >= 2 and self.cross(upper[-2], upper[-1], p) <= 0:
                upper.pop()
            upper.append(p)
        hull = lower[:-1] + upper[:-1]
        if hull:
            hull.append(hull[0])  # Fecha o polígono
        return hull

    def polygon_area(self, poly: List[Tuple[float, float]]) -> float:
        """Calcula área usando fórmula de Shoelace."""
        n = len(poly) - 1  # último ponto é repetição do primeiro
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += poly[i][0] * poly[j][1]
            area -= poly[j][0] * poly[i][1]
        return abs(area) / 2.0

    # ------------------------------------------------------------------
    # Extração de polígonos do DXF
    # ------------------------------------------------------------------
    def _get_polygons_center(self, polygons: List[List[Tuple[float, float]]]) -> Tuple[float, float]:
        """Calcula o centro (médio) de todos os polígonos."""
        all_x = []
        all_y = []
        for poly in polygons:
            for p in poly:
                all_x.append(p[0])
                all_y.append(p[1])
        if not all_x:
            return (0.0, 0.0)
        return (sum(all_x) / len(all_x), sum(all_y) / len(all_y))

    def extrair_paredes(self) -> List[List[Tuple[float, float]]]:
        """Extrai polígonos fechados do espaço modelo do DXF."""
        if not self.documento_dxf:
            return []
        msp = self.documento_dxf.modelspace()
        polygons = []
        scale = self.escala

        for entity in msp:
            dtype = entity.dxftype()
            verts = None
            if dtype in ("LWPOLYLINE", "POLYLINE"):
                try:
                    raw = [(v.dxf.x * scale, v.dxf.y * scale) for v in entity.vertices()]
                except AttributeError:
                    raw = [(v[0] * scale, v[1] * scale) for v in entity.vertices()]
                if len(raw) >= 3:
                    verts = raw
            # Ignorar LINEs propositalmente

            if verts:
                cleaned = self.clean_polygon(verts)
                if len(cleaned) >= 4:  # pelo menos 3 vértices + fechamento
                    area = self.polygon_area(cleaned)
                    if area > POLYGON_MIN_AREA:
                        polygons.append(cleaned)

        self.polygons = polygons
        # Calcula o centro dos polígonos (para translação posterior)
        self._polygons_center = self._get_polygons_center(polygons)
        logger.info(f"Extraídos {len(polygons)} polígonos do DXF, centro em ({self._polygons_center[0]:.2f}, {self._polygons_center[1]:.2f})")
        return polygons

    # ------------------------------------------------------------------
    # Geração de geometria 3D (refatorada e com translação)
    # ------------------------------------------------------------------
    def _generate_walls_and_outlines(self, polygons: List[List[Tuple[float, float]]], height: float) -> Tuple[List, List]:
        """Gera paredes (quads) e outlines (arestas) a partir dos polígonos."""
        walls = []
        outlines = []
        for polygon in polygons:
            clean = self.clean_polygon(polygon)
            for i in range(len(clean) - 1):
                p1, p2 = clean[i], clean[i + 1]
                wall = [
                    [p1[0], p1[1], 0.0],
                    [p2[0], p2[1], 0.0],
                    [p2[0], p2[1], height],
                    [p1[0], p1[1], height]
                ]
                walls.append(wall)
                outlines.append(wall)  # outlines são as mesmas faces
        return walls, outlines

    def _generate_floor_and_ceiling(self, hull: List[Tuple[float, float]], height: float) -> Tuple[List, List]:
        """Gera piso e teto a partir do fecho convexo."""
        floor = [[p[0], p[1], 0.0] for p in hull]
        ceiling = [[p[0], p[1], height] for p in reversed(hull)]
        return [floor], [ceiling]

    def _compute_convex_hull_from_polygons(self, polygons: List[List[Tuple[float, float]]]) -> Optional[List[Tuple[float, float]]]:
        """Calcula o fecho convexo de todos os pontos dos polígonos."""
        all_points = []
        for poly in polygons:
            all_points.extend(poly[:-1])  # exclui ponto de fechamento
        if not all_points:
            return None
        hull = self.convex_hull(all_points)
        if not hull:
            return None
        return hull

    def criar_ambiente_3d(self, polygons: List[List[Tuple[float, float]]],
                          gerar_escadas: bool = False,
                          altura_total: Optional[float] = None) -> Tuple[List, List, List, List, List]:
        """
        Gera geometria 3D completa, transladando os polígonos para que o centro fique na origem.
        Retorna: walls, floors, ceilings, outlines, stairs
        """
        height = self.altura_parede
        if not polygons:
            return [], [], [], [], []

        # Translada todos os polígonos para que o centro fique na origem
        cx, cy = self._polygons_center
        translated_polygons = []
        for poly in polygons:
            new_poly = [(p[0] - cx, p[1] - cy) for p in poly]
            translated_polygons.append(new_poly)

        # Fecho convexo a partir dos polígonos transladados
        hull = self._compute_convex_hull_from_polygons(translated_polygons)
        if not hull:
            logger.warning("Não foi possível calcular fecho convexo; geometria pode estar incompleta")
            return [], [], [], [], []

        # Gera paredes e outlines usando os polígonos transladados
        walls, outlines = self._generate_walls_and_outlines(translated_polygons, height)

        # Gera piso e teto a partir do hull transladado
        floors, ceilings = self._generate_floor_and_ceiling(hull, height)

        # Escadas: também precisam ser transladadas
        stairs_3d = []
        if gerar_escadas:
            stair_candidates = self.detectar_escadas_hibrido()
            if stair_candidates:
                # Translada os candidatos a escada
                for s in stair_candidates:
                    s["x_min"] -= cx
                    s["x_max"] -= cx
                    s["y_min"] -= cy
                    s["y_max"] -= cy
                stairs_3d = self.gerar_geometria_escadas_3d(stair_candidates, altura_total or height)

        # Armazena as geometrias transladadas
        self.walls = walls
        self.floors = floors
        self.ceilings = ceilings
        self.outlines = outlines
        self.stairs = stairs_3d

        return walls, floors, ceilings, outlines, stairs_3d

    # ------------------------------------------------------------------
    # Estatísticas
    # ------------------------------------------------------------------
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da geometria atual."""
        total_wall_area = 0.0
        for wall in self.walls:
            if len(wall) == 4:
                v0 = np.array(wall[0])
                v1 = np.array(wall[1])
                v3 = np.array(wall[3])
                width = float(np.linalg.norm(v1 - v0))
                height = float(np.linalg.norm(v3 - v0))
                total_wall_area += width * height

        floor_area = 0.0
        if self.floors and self.floors[0]:
            floor_area = self.polygon_area([(p[0], p[1]) for p in self.floors[0]])

        return {
            "paredes": len(self.walls),
            "poligonos": len(self.polygons),
            "area_paredes_m2": round(total_wall_area, 2),
            "area_piso_m2": round(floor_area, 2),
            "altura_parede_m": self.altura_parede,
        }

    # ------------------------------------------------------------------
    # Detecção de escadas (híbrido)
    # ------------------------------------------------------------------
    def detectar_escadas_hibrido(self, threshold: float = STAIR_DETECTION_THRESHOLD) -> List[Dict]:
        """Detecta candidatos a escada baseado em linhas paralelas regulares."""
        if not self.documento_dxf:
            return []
        msp = self.documento_dxf.modelspace()
        scale = self.escala
        lines = []

        for ent in msp:
            if ent.dxftype() == "LINE":
                layer = (ent.dxf.layer or "").lower()
                sx, sy = ent.dxf.start[0] * scale, ent.dxf.start[1] * scale
                ex, ey = ent.dxf.end[0] * scale, ent.dxf.end[1] * scale
                vx, vy = ex - sx, ey - sy
                length = (vx**2 + vy**2) ** 0.5
                if length < 0.05:
                    continue
                angle = np.arctan2(vy, vx)
                lines.append({
                    "s": (sx, sy),
                    "e": (ex, ey),
                    "angle": angle,
                    "len": length,
                    "layer": layer,
                    "kw": any(k in layer for k in STAIR_KEYWORDS)
                })

        groups, used = [], set()
        for i, l1 in enumerate(lines):
            if i in used:
                continue
            group = [l1]
            used.add(i)
            for j, l2 in enumerate(lines):
                if j in used:
                    continue
                diff = abs(l1["angle"] - l2["angle"])
                if diff > np.pi:
                    diff = 2 * np.pi - diff
                if diff < 0.05 and abs(l1["len"] - l2["len"]) < l1["len"] * 0.3:
                    group.append(l2)
                    used.add(j)
            if len(group) >= 3:
                groups.append(group)

        stairs = []
        for g in groups:
            centers = sorted([(l["s"][0] + l["e"][0]) / 2 for l in g])
            dists = [centers[i+1] - centers[i] for i in range(len(centers)-1)]
            if not dists:
                continue
            mean_d, std_d = np.mean(dists), np.std(dists)
            regularity = max(0, 1.0 - (std_d / (mean_d + 1e-6)))
            layer_match = sum(1 for l in g if l["kw"]) / len(g)

            all_x = [p for l in g for p in (l["s"][0], l["e"][0])]
            all_y = [p for l in g for p in (l["s"][1], l["e"][1])]
            bbox_w = max(all_x) - min(all_x)
            bbox_h = max(all_y) - min(all_y)
            aspect = max(bbox_w, bbox_h) / (min(bbox_w, bbox_h) + 1e-6)

            score = (regularity * 0.4) + (layer_match * 0.3) + (min(1.0, aspect / 5.0) * 0.3)
            if score >= threshold:
                stairs.append({
                    "x_min": min(all_x),
                    "x_max": max(all_x),
                    "y_min": min(all_y),
                    "y_max": max(all_y),
                    "n_steps": len(g),
                    "score": score
                })
        return stairs

    def gerar_geometria_escadas_3d(self, stair_candidates: List[Dict], altura_total: float) -> List[List[List[float]]]:
        """Gera quads representando degraus de escada."""
        stairs_3d = []
        for s in stair_candidates:
            larg = max(s["x_max"] - s["x_min"], s["y_max"] - s["y_min"])
            prof = min(s["x_max"] - s["x_min"], s["y_max"] - s["y_min"])
            h_step = altura_total / s["n_steps"]
            d_step = prof / s["n_steps"]

            for i in range(s["n_steps"]):
                z = i * h_step
                y0 = s["y_min"] + i * d_step
                y1 = y0 + d_step
                stairs_3d.append([
                    [s["x_min"], y0, z],
                    [s["x_max"], y0, z],
                    [s["x_max"], y1, z + h_step],
                    [s["x_min"], y1, z + h_step]
                ])
        return stairs_3d

    # ------------------------------------------------------------------
    # Bounding box para ajuste de câmera
    # ------------------------------------------------------------------
    def get_bounding_box(self) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        """
        Retorna o bounding box da geometria atual (paredes, piso, teto, escadas).
        Retorno: (min_x, min_y, min_z), (max_x, max_y, max_z)
        """
        all_points = []
        for wall in self.walls:
            all_points.extend(wall)
        for floor in self.floors:
            all_points.extend(floor)
        for ceiling in self.ceilings:
            all_points.extend(ceiling)
        for stair in self.stairs:
            all_points.extend(stair)
        if not all_points:
            # Retorna um box padrão visível (2x2x2 centralizado na origem)
            return (-1.0, -1.0, 0.0), (1.0, 1.0, 2.0)
        xs = [p[0] for p in all_points]
        ys = [p[1] for p in all_points]
        zs = [p[2] for p in all_points]
        min_pt = (min(xs), min(ys), min(zs))
        max_pt = (max(xs), max(ys), max(zs))
        logger.info(f"Bounding Box: min={min_pt}, max={max_pt}")
        return min_pt, max_pt

    # ------------------------------------------------------------------
    # Métodos unificados de extração de malha para exportação
    # ------------------------------------------------------------------
    def _get_all_geometry(self) -> Tuple[List[List[float]], List[int], List[Tuple[str, int, int]]]:
        """
        Retorna (vértices, índices, materiais_info) para toda a geometria (paredes, piso, teto, escadas).
        materiais_info: lista de (nome_material, inicio_indice, fim_indice)
        """
        all_verts = []
        all_indices = []
        material_ranges = []  # (material_name, start_idx, end_idx)

        def add_quad(quad, material_name):
            nonlocal all_verts, all_indices
            base = len(all_verts)
            for v in quad:
                all_verts.append(v)
            # Triangulação do quad: dois triângulos (0,1,2) e (0,2,3)
            all_indices.extend([base, base+1, base+2, base, base+2, base+3])
            return base, base+3  # índice inicial e final dos vértices adicionados

        # Paredes
        for wall in self.walls:
            add_quad(wall, "wall_mat")
        # Piso (triangulação como fan)
        if self.floors:
            floor_verts = self.floors[0]
            base = len(all_verts)
            all_verts.extend(floor_verts)
            # Triangulação simples: primeiro vértice com os demais em triângulos
            for i in range(1, len(floor_verts)-1):
                all_indices.extend([base, base+i, base+i+1])
        # Teto
        if self.ceilings:
            ceil_verts = self.ceilings[0]
            base = len(all_verts)
            all_verts.extend(ceil_verts)
            for i in range(1, len(ceil_verts)-1):
                all_indices.extend([base, base+i, base+i+1])
        # Escadas
        for stair in self.stairs:
            add_quad(stair, "stair_mat")

        return all_verts, all_indices, material_ranges

    # ------------------------------------------------------------------
    # Exportação OBJ (inclui escadas)
    # ------------------------------------------------------------------
    def export_as_obj(self, filename: str) -> str:
        """Exporta a geometria (paredes, piso, teto, escadas) para .obj + .mtl."""
        if not self.walls and not self.floors and not self.stairs:
            raise NoGeometryError("Nenhuma geometria para exportar. Gere o ambiente 3D primeiro.")

        mtl_filename = os.path.splitext(filename)[0] + ".mtl"

        # Escreve arquivo .mtl
        with open(mtl_filename, "w") as mf:
            mf.write("# ArchiDive — Material Library\n")
            mf.write("newmtl wall_mat\n")
            mf.write(f"Ka {MTL_WALL_AMBIENT[0]:.3f} {MTL_WALL_AMBIENT[1]:.3f} {MTL_WALL_AMBIENT[2]:.3f}\n")
            mf.write(f"Kd {MTL_WALL_DIFFUSE[0]:.3f} {MTL_WALL_DIFFUSE[1]:.3f} {MTL_WALL_DIFFUSE[2]:.3f}\n")
            mf.write(f"Ks {MTL_WALL_SPECULAR[0]:.3f} {MTL_WALL_SPECULAR[1]:.3f} {MTL_WALL_SPECULAR[2]:.3f}\n")
            mf.write(f"Ns {MTL_WALL_SHININESS}\n\n")
            mf.write("newmtl floor_mat\n")
            mf.write(f"Ka {MTL_FLOOR_AMBIENT[0]:.3f} {MTL_FLOOR_AMBIENT[1]:.3f} {MTL_FLOOR_AMBIENT[2]:.3f}\n")
            mf.write(f"Kd {MTL_FLOOR_DIFFUSE[0]:.3f} {MTL_FLOOR_DIFFUSE[1]:.3f} {MTL_FLOOR_DIFFUSE[2]:.3f}\n")
            mf.write(f"Ks {MTL_FLOOR_SPECULAR[0]:.3f} {MTL_FLOOR_SPECULAR[1]:.3f} {MTL_FLOOR_SPECULAR[2]:.3f}\n")
            mf.write(f"Ns {MTL_FLOOR_SHININESS}\n\n")
            mf.write("newmtl ceiling_mat\n")
            mf.write(f"Ka {MTL_CEILING_AMBIENT[0]:.3f} {MTL_CEILING_AMBIENT[1]:.3f} {MTL_CEILING_AMBIENT[2]:.3f}\n")
            mf.write(f"Kd {MTL_CEILING_DIFFUSE[0]:.3f} {MTL_CEILING_DIFFUSE[1]:.3f} {MTL_CEILING_DIFFUSE[2]:.3f}\n")
            mf.write(f"Ks {MTL_CEILING_SPECULAR[0]:.3f} {MTL_CEILING_SPECULAR[1]:.3f} {MTL_CEILING_SPECULAR[2]:.3f}\n")
            mf.write(f"Ns {MTL_CEILING_SHININESS}\n\n")
            mf.write("newmtl stair_mat\n")
            mf.write("Ka 0.0 0.5 0.6\nKd 0.0 0.8 0.9\nKs 0.2 0.2 0.2\nNs 20\n")

        # Escreve arquivo .obj
        with open(filename, "w") as f:
            f.write(f"# ArchiDive v1.0 — Exportado\n")
            f.write(f"# Arquivo DXF: {os.path.basename(self.caminho_arquivo)}\n")
            f.write(f"mtllib {os.path.basename(mtl_filename)}\n\n")

            vertex_dict = {}
            vertex_counter = 1

            # Função auxiliar para adicionar vértice e retornar índice
            def add_vertex(v):
                nonlocal vertex_counter
                key = tuple(round(x, OBJ_DECIMAL_PLACES) for x in v)
                if key not in vertex_dict:
                    vertex_dict[key] = vertex_counter
                    f.write(f"v {v[0]:.{OBJ_DECIMAL_PLACES}f} {v[1]:.{OBJ_DECIMAL_PLACES}f} {v[2]:.{OBJ_DECIMAL_PLACES}f}\n")
                    vertex_counter += 1
                return vertex_dict[key]

            # Escreve faces agrupadas por material
            # Paredes
            if self.walls:
                f.write(f"\nusemtl wall_mat\n")
                for wall in self.walls:
                    idxs = [add_vertex(v) for v in wall]
                    f.write(f"f {idxs[0]} {idxs[1]} {idxs[2]} {idxs[3]}\n")
            # Piso
            if self.floors:
                f.write(f"\nusemtl floor_mat\n")
                floor_verts = self.floors[0]
                idxs_floor = [add_vertex(v) for v in floor_verts]
                for i in range(1, len(idxs_floor)-1):
                    f.write(f"f {idxs_floor[0]} {idxs_floor[i]} {idxs_floor[i+1]}\n")
            # Teto
            if self.ceilings:
                f.write(f"\nusemtl ceiling_mat\n")
                ceil_verts = self.ceilings[0]
                idxs_ceil = [add_vertex(v) for v in ceil_verts]
                for i in range(1, len(idxs_ceil)-1):
                    f.write(f"f {idxs_ceil[0]} {idxs_ceil[i]} {idxs_ceil[i+1]}\n")
            # Escadas
            if self.stairs:
                f.write(f"\nusemtl stair_mat\n")
                for stair in self.stairs:
                    idxs = [add_vertex(v) for v in stair]
                    f.write(f"f {idxs[0]} {idxs[1]} {idxs[2]} {idxs[3]}\n")

        logger.info(f"OBJ exportado: {filename}")
        return filename

    # ------------------------------------------------------------------
    # Exportação glTF (inclui escadas)
    # ------------------------------------------------------------------
    def export_as_gltf(self, filename: str) -> str:
        """Exporta para glTF 2.0 (.gltf + .bin). Requer pygltflib."""
        if not GLTF_AVAILABLE:
            raise RuntimeError("pygltflib não está instalado. Execute: pip install pygltflib")
        if not self.walls and not self.floors and not self.stairs:
            raise NoGeometryError("Nenhuma geometria para exportar. Gere o ambiente 3D primeiro.")

        verts, indices, _ = self._get_all_geometry()
        if not verts or not indices:
            raise NoGeometryError("Geometria vazia após processamento.")

        verts_np = np.array(verts, dtype=np.float32)
        idx_np = np.array(indices, dtype=np.uint32)

        vert_bytes = verts_np.tobytes()
        idx_bytes = idx_np.tobytes()
        bin_data = vert_bytes + idx_bytes

        bin_filename = os.path.splitext(filename)[0] + ".bin"
        with open(bin_filename, "wb") as bf:
            bf.write(bin_data)

        gltf = GLTF2()
        gltf.scene = 0
        gltf.scenes = [Scene(nodes=[0])]
        gltf.nodes = [Node(mesh=0)]
        gltf.meshes = [
            Mesh(primitives=[
                Primitive(
                    attributes=Attributes(POSITION=0),
                    indices=1,
                )
            ])
        ]
        gltf.buffers = [Buffer(uri=os.path.basename(bin_filename), byteLength=len(bin_data))]
        gltf.bufferViews = [
            BufferView(buffer=0, byteOffset=0, byteLength=len(vert_bytes), target=ARRAY_BUFFER),
            BufferView(buffer=0, byteOffset=len(vert_bytes), byteLength=len(idx_bytes), target=ELEMENT_ARRAY_BUFFER),
        ]

        vmin = verts_np.min(axis=0).tolist()
        vmax = verts_np.max(axis=0).tolist()
        gltf.accessors = [
            Accessor(bufferView=0, componentType=FLOAT, count=len(verts), type="VEC3", min=vmin, max=vmax),
            Accessor(bufferView=1, componentType=UNSIGNED_INT, count=len(indices), type="SCALAR"),
        ]

        gltf.save(filename)
        logger.info(f"glTF exportado: {filename}")
        return filename

    # ------------------------------------------------------------------
    # Carregador de OBJ para visualização (melhorado)
    # ------------------------------------------------------------------
    @staticmethod
    def carregar_obj(caminho_obj: str) -> Tuple[List[List[float]], List[List[int]]]:
        """
        Carrega arquivo OBJ e triangula faces (suporta quads e polígonos convexos).
        Retorna (vértices, faces trianguladas).
        """
        verts = []
        faces_poly = []  # faces como lista de índices (sem triangulação)
        with open(caminho_obj, 'r') as f:
            for line in f:
                if line.startswith('v '):
                    parts = line.split()
                    verts.append([float(parts[1]), float(parts[2]), float(parts[3])])
                elif line.startswith('f '):
                    parts = line.split()[1:]
                    idxs = []
                    for p in parts:
                        # Formato: v/vt/vn ou v/vt ou v
                        idx = int(p.split('/')[0]) - 1
                        idxs.append(idx)
                    faces_poly.append(idxs)

        # Triangulação simples: fan a partir do primeiro vértice (funciona para convexos)
        faces_tri = []
        for poly in faces_poly:
            if len(poly) < 3:
                continue
            if len(poly) == 3:
                faces_tri.append(poly)
            else:
                for i in range(1, len(poly)-1):
                    faces_tri.append([poly[0], poly[i], poly[i+1]])
        return verts, faces_tri