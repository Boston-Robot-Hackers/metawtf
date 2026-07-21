from setuptools import find_packages, setup

package_name = "metawtf"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="pitosalas",
    maintainer_email="pitosalas@gmail.com",
    description="TODO: package description.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "metawtf = metawtf.tracer_node:main",
        ],
    },
)
