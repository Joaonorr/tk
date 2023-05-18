from setuptools import setup, find_packages

from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name = 'testkit',
    version = '1.0.0',
    author = "David Sena Oliveira",
    author_email = "sena@ufc.br",
    packages=find_packages(),
    package_dir={'': '.'},
    description = "",
    long_description=long_description,
    url = "https://github.com/senapk/tk",
    project_urls = {
        'Código fonte': 'https://github.com/senapk/tk',
    },
    license = 'MIT'
)