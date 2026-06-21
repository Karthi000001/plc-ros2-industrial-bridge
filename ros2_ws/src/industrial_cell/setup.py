from setuptools import setup
from glob import glob

package_name = "industrial_cell"

setup(
    name=package_name,
    version="1.0.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages",
         [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/launch", glob("launch/*.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Karthikeyan Raja",
    maintainer_email="your@email.com",
    description="PLC-ROS2 industrial cell bridge with ML anomaly detection",
    license="MIT",
    entry_points={
        "console_scripts": [
            "modbus_bridge   = industrial_cell.modbus_bridge:main",
            "cell_supervisor = industrial_cell.cell_supervisor:main",
        ],
    },
)
