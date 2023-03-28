from setuptools import Extension, find_packages, setup
from Cython.Build import cythonize

setup(
    packages = find_packages(),
    ext_modules = cythonize([
        Extension(
           "epunfold.homsearch.homsearch_interface",
           sources=["epunfold/homsearch/homsearch_interface.pyx", "epunfold/homsearch/homsearch_lib.cpp"],
           language="c++",
           extra_compile_args=['-std=c++11'],
        )
    ])
)
