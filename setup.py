from setuptools import setup, find_packages

setup(
    name="archidive",
    version="1.0.0",
    description="Conversor profissional de plantas baixas DXF para ambientes 3D e VR",
    author="ArchiDive",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "PyQt5>=5.15.0",
        "numpy>=1.21.0",
        "ezdxf>=1.0.0",
        "pygltflib>=1.15.0",
        "PyOpenGL>=3.1.6",
    ],
    entry_points={
        "console_scripts": [
            "archidive=main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
