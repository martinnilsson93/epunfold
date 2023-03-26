from setuptools import Extension, find_packages, setup
from Cython.Build import cythonize

setup(
    packages = find_packages(),
    ext_modules = cythonize([
        Extension(
           "homsearch.homsearch_interface",
           sources=["homsearch/homsearch_interface.pyx", "homsearch/homsearch_lib.cpp"],
           language="c++",
           extra_compile_args=['-std=c++11'],
        )
    ])
)
