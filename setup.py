import setuptools

with open('README.md', mode='r', encoding='utf-8') as readme_file:
    long_description = readme_file.read()


setuptools.setup(
    name="pyFileCarving",
    version="1.0.0",
    author="Florian Wahl",
    author_email="florian.wahl.developer@gmail.com",
    description="A python cli script for simple file carving",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wahlflo/pyFileCarving",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'bitarray>=1.2.2',
        'pefile>=2019.4.18',
        'Pillow>=7.1.2',
        'pyparted>=3.11.6',
        'cli-formatter>=1.2.0',
        'PyPDF2>=1.26.0'
    ],
    entry_points={
        "console_scripts": [
            "pyFileCarving=py_file_carving.cli_script:main"
        ],
    }
)