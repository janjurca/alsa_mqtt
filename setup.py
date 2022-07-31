from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="alsa_mqtt",
    version="v0.1",
    description="Tool that expose an alsa device controll via mqtt.",
    long_description=long_description,
    url="https://github.com/janjurca/alsa_mqtt",
    keywords=[],
    include_package_data=True,
    packages=find_packages(),
    classifiers=[
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
    ],
    install_requires=[
        "paho-mqtt",
        "pyalsaaudio"
    ],
    entry_points={
        'console_scripts': [
            'alsa-mqtt = alsa_mqtt.__main__:main',
        ]
    }
)
