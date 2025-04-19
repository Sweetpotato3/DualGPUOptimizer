from setuptools import setup, find_packages

setup(
    name="dual_gpu_optimizer",
    version="0.2.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pynvml",
        "rich",
        "psutil",
        "ttkbootstrap",
        "pystray",
        "pillow",
        "tomli-w",
    ],
    extras_require={
        "full": [
            "torch",
            "prometheus_client",
        ],
    },
    entry_points={
        "console_scripts": [
            "dualgpuopt=dualgpuopt.__main__:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
) 