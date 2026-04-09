"""
ArchiDive — Backend
Responsável por:
  - Leitura de arquivos DXF
  - Extração e limpeza de polígonos
  - Geração de geometria 3D (paredes, piso, teto)
  - Exportação OBJ e glTF/GLB
"""

import os
import struct
import base64
import json
import numpy as np
import ezdxf

# pygltflib é opcional; se não tiver instalado, apenas OBJ fica disponível
try:
    from pygltflib import (
        GLTF2, Scene, Node, Mesh, Primitive, Attributes,
        Buffer, BufferView, Accessor,
        FLOAT, UNSIGNED_INT, ARRAY_BUFFER, ELEMENT_ARRAY_BUFFER,
        TRIANGLE_STRIP, TRIANGLES,
    )
    GLTF_AVAILABLE = True
except ImportError:
    GLTF_AVAILABLE = False


class Backend:
    """Motor de processamento de plantas baixas DXF → 3D."""

    def __init__(self, altura_parede: float = 2.5):
        self.altura_parede = altura_parede
        self.documento_dxf = None
        self.caminho_arquivo = ""
        self.walls: list = []
        self.floors: list = []
        self.ceilings: list = []
        self.outlines: list = []
        self.polygons: list = []
        self.escala = 0.001  # DXF costuma estar em mm; converte para metros

    # ------------------------------------------------------------------
    # Leitura DXF
    # ------------------------------------------------------------------

    def abrir_arquivo(self, caminho: str):
        """Abre um arquivo DXF e retorna (ok: bool, mensagem: str)."""
        try:
            self.documento_dxf = ezdxf.readfile(caminho)
            self.caminho_arquivo = caminho
            # Detecta unidade do arquivo
            units = self.documento_dxf.units
            # ezdxf: 0=sem unidade,1=polegada,2=pé,4=mm,5=cm,6=m
            if units == 6:
                self.escala = 1.0
            elif units == 5:
                self.escala = 0.01
            elif units in (4, 0):
                self.escala = 0.001
            elif units == 1:
                self.escala = 0.0254
            elif units == 2:
                self.escala = 0.3048
            else:
                self.escala = 0.001
            return True, f"Arquivo carregado com sucesso!\nUnidade detectada: escala={self.escala}"
        except Exception as exc:
            return False, f"Erro ao carregar arquivo:\n{exc}"

    # ------------------------------------------------------------------
    # Helpers geométricos
    # ------------------------------------------------------------------

    @staticmethod
    def points_equal(p1, p2, tol: float = 0.001) -> bool:
        return abs(p1[0] - p2[0]) < tol and abs(p1[1] - p2[1]) < tol

    @staticmethod
    def cross(o, a, b) -> float:
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    def clean_polygon(self, polygon):
        clean = []
        for i, p in enumerate(polygon):
            if i == 0 or not self.points_equal(p, polygon[i - 1]):
                clean.append(p)
        if len(clean) > 2 and not self.points_equal(clean[0], clean[-1]):
            clean.append(clean[0])
        return clean

    def convex_hull(self, points):
        if len(points) < 3:
            return None
        pts = np.array([(p[0], p[1]) for p in points])
        centroid = np.mean(pts, axis=0)
        angles = np.arctan2(pts[:, 1] - centroid[1], pts[:, 0] - centroid[0])
        sorted_pts = pts[np.argsort(angles)]
        hull = []
        for point in sorted_pts:
            while len(hull) >= 2 and self.cross(hull[-2], hull[-1], point) <= 0:
                hull.pop()
            hull.append(point)
        if hull:
            hull.append(hull[0])
        return [(float(p[0]), float(p[1])) for p in hull]

    def polygon_area(self, poly) -> float:
        """Calcula área usando Shoelace."""
        n = len(poly) - 1
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += poly[i][0] * poly[j][1]
            area -= poly[j][0] * poly[i][1]
        return abs(area) / 2.0

    # ------------------------------------------------------------------
    # Extração de polígonos do DXF
    # ------------------------------------------------------------------

    def extrair_paredes(self) -> list:
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

            elif dtype == "LINE":
                # Linhas isoladas são descartadas; contam apenas polígonos
                pass

            if verts:
                clean = []
                for i, v in enumerate(verts):
                    if i == 0 or not self.points_equal(v, verts[i - 1]):
                        clean.append(v)
                if len(clean) >= 3:
                    if not self.points_equal(clean[0], clean[-1]):
                        clean.append(clean[0])
                    if len(clean) >= 4:
                        area = self.polygon_area(clean)
                        if area > 0.01:  # filtra ruídos menores que 0.01 m²
                            polygons.append(clean)

        self.polygons = polygons
        return polygons

    # ------------------------------------------------------------------
    # Geração de geometria 3D
    # ------------------------------------------------------------------

    def criar_ambiente_3d(self, polygons: list, gerar_escadas: bool = False, altura_total: float = None):
        height = self.altura_parede
        walls, outlines = [], []
        if not polygons: return [], [], [], [], []

        all_points = []
        for poly in polygons:
            clean = self.clean_polygon(poly)
            all_points.extend(clean[:-1])
        boundary = self.convex_hull(all_points)
        if not boundary: return [], [], [], [], []

        for polygon in polygons:
            clean = self.clean_polygon(polygon)
            for i in range(len(clean) - 1):
                p1, p2 = clean[i], clean[i + 1]
                wall = [[p1[0], p1[1], 0.0], [p2[0], p2[1], 0.0],
                        [p2[0], p2[1], height], [p1[0], p1[1], height]]
                walls.append(wall); outlines.append(wall)

        floor = [[p[0], p[1], 0.0] for p in boundary]
        ceiling = [[p[0], p[1], height] for p in reversed(boundary)]
        stairs_3d = []
        if gerar_escadas:
            stairs_3d = self.gerar_geometria_escadas_3d(self.detectar_escadas_hibrido(), altura_total or height)

        self.walls, self.floors, self.ceilings, self.outlines, self.stairs = walls, [floor], [ceiling], outlines, stairs_3d
        return walls, [floor], [ceiling], outlines, stairs_3d

    # ------------------------------------------------------------------
    # Estatísticas
    # ------------------------------------------------------------------

    def get_stats(self) -> dict:
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
        if self.floors:
            floor_area = self.polygon_area(self.floors[0])

        return {
            "paredes": len(self.walls),
            "poligonos": len(self.polygons),
            "area_paredes_m2": round(total_wall_area, 2),
            "area_piso_m2": round(floor_area, 2),
            "altura_parede_m": self.altura_parede,
        }

    # ------------------------------------------------------------------
    # Exportação OBJ
    # ------------------------------------------------------------------

    def export_as_obj(self, filename: str, walls, floors, ceilings) -> str:
        """Exporta a geometria para .obj + .mtl com materiais básicos."""
        mtl_filename = os.path.splitext(filename)[0] + ".mtl"

        with open(mtl_filename, "w") as mf:
            mf.write("# ArchiDive — Material Library\n")
            mf.write("newmtl wall_mat\nKa 0.8 0.8 0.8\nKd 0.9 0.9 0.9\nKs 0.1 0.1 0.1\nNs 10\n\n")
            mf.write("newmtl floor_mat\nKa 0.6 0.5 0.4\nKd 0.75 0.65 0.5\nKs 0.05 0.05 0.05\nNs 5\n\n")
            mf.write("newmtl ceiling_mat\nKa 0.95 0.95 0.95\nKd 1.0 1.0 1.0\nKs 0.0 0.0 0.0\nNs 1\n\n")

        with open(filename, "w") as f:
            f.write(f"# ArchiDive v1.0 — Exportado\n")
            f.write(f"# Arquivo DXF: {os.path.basename(self.caminho_arquivo)}\n")
            f.write(f"mtllib {os.path.basename(mtl_filename)}\n\n")

            vertex_dict: dict = {}
            vertex_counter = 1
            all_geom = [("wall_mat", walls), ("floor_mat", floors), ("ceiling_mat", ceilings)]

            # Registra todos os vértices primeiro
            for _, geom_list in all_geom:
                for face in geom_list:
                    for v in face:
                        key = tuple(round(x, 6) for x in v)
                        if key not in vertex_dict:
                            vertex_dict[key] = vertex_counter
                            f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
                            vertex_counter += 1

            f.write("\n")

            # Faces por material
            for mat, geom_list in all_geom:
                f.write(f"\nusemtl {mat}\n")
                for face in geom_list:
                    indices = []
                    for v in face:
                        key = tuple(round(x, 6) for x in v)
                        indices.append(str(vertex_dict[key]))
                    f.write(f"f {' '.join(indices)}\n")

        return filename

    # ------------------------------------------------------------------
    # Exportação glTF (JSON + BIN)
    # ------------------------------------------------------------------

    def export_as_gltf(self, filename: str) -> str:
        """Exporta para glTF 2.0 (.gltf + .bin). Requer pygltflib."""
        if not GLTF_AVAILABLE:
            raise RuntimeError("pygltflib não está instalado. Execute: pip install pygltflib")

        all_verts = []
        all_indices = []

        def add_quad(quad):
            base = len(all_verts)
            for v in quad:
                all_verts.append(v)
            # Dois triângulos por quad
            all_indices.extend([base, base + 1, base + 2, base, base + 2, base + 3])

        for wall in self.walls:
            add_quad(wall)
        for floor in self.floors:
            pts = floor[:-1] if len(floor) > 3 else floor
            for i in range(1, len(pts) - 1):
                tri_verts = [pts[0], pts[i], pts[i + 1]]
                base = len(all_verts)
                all_verts.extend(tri_verts)
                all_indices.extend([base, base + 1, base + 2])
        for ceiling in self.ceilings:
            pts = ceiling[:-1] if len(ceiling) > 3 else ceiling
            for i in range(1, len(pts) - 1):
                tri_verts = [pts[0], pts[i], pts[i + 1]]
                base = len(all_verts)
                all_verts.extend(tri_verts)
                all_indices.extend([base, base + 1, base + 2])

        verts_np = np.array(all_verts, dtype=np.float32)
        idx_np = np.array(all_indices, dtype=np.uint32)

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
            Accessor(bufferView=0, componentType=FLOAT, count=len(all_verts), type="VEC3", min=vmin, max=vmax),
            Accessor(bufferView=1, componentType=UNSIGNED_INT, count=len(all_indices), type="SCALAR"),
        ]

        gltf.save(filename)
        return filename
    
    # ------------------------------------------------------------------
    # Pipeline Híbrido: Detecção de Escadas
    # ------------------------------------------------------------------
    def detectar_escadas_hibrido(self, threshold: float = 0.65) -> list:
        if not self.documento_dxf:
            return []
        msp = self.documento_dxf.modelspace()
        scale = self.escala
        stair_kw = {"escada", "stair", "degrau", "step", "circulação", "rampa", "sc", "st"}
        lines = []

        for ent in msp:
            if ent.dxftype() == "LINE":
                layer = (ent.dxf.layer or "").lower()
                sx, sy = ent.dxf.start[0]*scale, ent.dxf.start[1]*scale
                ex, ey = ent.dxf.end[0]*scale, ent.dxf.end[1]*scale
                vx, vy = ex-sx, ey-sy
                length = (vx**2 + vy**2)**0.5
                if length < 0.05: continue
                angle = np.arctan2(vy, vx)
                lines.append({
                    "s": (sx, sy), "e": (ex, ey), "angle": angle,
                    "len": length, "layer": layer, "kw": any(k in layer for k in stair_kw)
                })

        groups, used = [], set()
        for i, l1 in enumerate(lines):
            if i in used: continue
            group = [l1]; used.add(i)
            for j, l2 in enumerate(lines):
                if j in used: continue
                diff = abs(l1["angle"] - l2["angle"])
                if diff > np.pi: diff = 2*np.pi - diff
                if diff < 0.05 and abs(l1["len"] - l2["len"]) < l1["len"]*0.3:
                    group.append(l2); used.add(j)
            if len(group) >= 3:
                groups.append(group)

        stairs = []
        for g in groups:
            centers = sorted([(l["s"][0]+l["e"][0])/2 for l in g])
            dists = [centers[i+1]-centers[i] for i in range(len(centers)-1)]
            if not dists: continue
            mean_d, std_d = np.mean(dists), np.std(dists)
            regularity = max(0, 1.0 - (std_d / (mean_d + 1e-6)))
            layer_match = sum(1 for l in g if l["kw"]) / len(g)

            all_x = [p for l in g for p in (l["s"][0], l["e"][0])]
            all_y = [p for l in g for p in (l["s"][1], l["e"][1])]
            bbox_w = max(all_x) - min(all_x)
            bbox_h = max(all_y) - min(all_y)
            aspect = max(bbox_w, bbox_h) / (min(bbox_w, bbox_h) + 1e-6)

            score = (regularity * 0.4) + (layer_match * 0.3) + (min(1.0, aspect/5.0) * 0.3)
            if score >= threshold:
                stairs.append({
                    "x_min": min(all_x), "x_max": max(all_x),
                    "y_min": min(all_y), "y_max": max(all_y),
                    "n_steps": len(g), "score": score
                })
        return stairs

    def gerar_geometria_escadas_3d(self, stair_candidates, altura_total=None) -> list:
        if altura_total is None: altura_total = self.altura_parede
        stairs_3d = []
        for s in stair_candidates:
            cx, cy = (s["x_min"]+s["x_max"])/2, (s["y_min"]+s["y_max"])/2
            larg = max(s["x_max"]-s["x_min"], s["y_max"]-s["y_min"])
            prof = min(s["x_max"]-s["x_min"], s["y_max"]-s["y_min"])
            h_step = altura_total / s["n_steps"]
            d_step = prof / s["n_steps"]

            for i in range(s["n_steps"]):
                z = i * h_step
                y0 = s["y_min"] + i * d_step
                y1 = y0 + d_step
                # Gera quad por degrau (topo + frente simplificada)
                stairs_3d.append([
                    [s["x_min"], y0, z], [s["x_max"], y0, z],
                    [s["x_max"], y1, z+h_step], [s["x_min"], y1, z+h_step]
                ])
        return stairs_3d

    # ------------------------------------------------------------------
    # Carregador de OBJ para Visualização Interna
    # ------------------------------------------------------------------
    def carregar_obj(self, caminho_obj: str) -> tuple:
        verts, faces = [], []
        with open(caminho_obj, 'r') as f:
            for line in f:
                if line.startswith('v '):
                    verts.append([float(x) for x in line.split()[1:4]])
                elif line.startswith('f '):
                    idxs = [int(p.split('/')[0])-1 for p in line.split()[1:]]
                    for i in range(1, len(idxs)-1):
                        faces.append([idxs[0], idxs[i], idxs[i+1]])
        return verts, faces