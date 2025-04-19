from setuptools import setup, find_packages

setup(
    name="dual_gpu_optimizer",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "rich",
        "psutil",
        "ttkbootstrap",
        "pystray",
        "pillow",
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
) 