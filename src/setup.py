from distutils.core import setup

from comref_converter import __author__, __version__

setup(
    name="comref_converter",
    version=__version__,
    description="COMREF Conversion utilities",
    author=__author__,
    author_email="ptorras@cvc.uab.cat",
    packages=["comref_converter"],
    install_requires=["tqdm", "apted", "sortedcontainers", "pydot"],
)
