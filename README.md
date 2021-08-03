# pyFileCarving
pyFileCarving is a command line script for file carving.

## Supported File Types

- PE-files
- PEM-files (certificates, private keys)
- PDFs
- Pictures (JPG, PNG)


## Installation
Clone the repo and install the package with pip

    git clone https://github.com/wahlflo/pyFileCarving
    cd pyFileCarving
    pip3 install .

## Usage
Type ```pyFileCarving --help``` to view the help.

```
usage: pyFileCarving -i INPUT -o OUTPUT

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Path to the device or file which should be scanned
  -o OUTPUT, --output OUTPUT
                        Path to the output directory
  -c, --no-corruption-checks
                        No corruption checks will be made, which faster the scan
  -f                    Flush files when the maximum file size is reached even if its not completely carved
  -p PLUGIN_LIST [PLUGIN_LIST ...], --plugin PLUGIN_LIST [PLUGIN_LIST ...]
                        List of plugins which will be used [keys, cert, pictures, binary, pdf]

```
