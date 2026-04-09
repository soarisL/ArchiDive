"""
ArchiDive — Exceções Customizadas
Define exceções específicas para melhor tratamento de erros.
"""

class ArchidiveException(Exception):
    """Exceção base para ArchiDive."""
    pass

class DXFFileError(ArchidiveException):
    """Erro ao ler arquivo DXF."""
    pass

class DXFFileNotFound(DXFFileError):
    """Arquivo DXF não encontrado."""
    pass

class DXFFileCorrupted(DXFFileError):
    """Arquivo DXF corrompido ou inválido."""
    pass

class DXFNoPolygonsFound(DXFFileError):
    """Nenhum polígono válido encontrado no arquivo DXF."""
    pass

class GeometryError(ArchidiveException):
    """Erro durante processamento geométrico."""
    pass

class ExportError(ArchidiveException):
    """Erro durante exportação."""
    pass

class OBJExportError(ExportError):
    """Erro ao exportar para OBJ."""
    pass

class GLTFExportError(ExportError):
    """Erro ao exportar para glTF."""
    pass

class VisualizerError(ArchidiveException):
    """Erro no visualizador 3D."""
    pass

class OpenGLError(VisualizerError):
    """Erro relacionado a OpenGL."""
    pass