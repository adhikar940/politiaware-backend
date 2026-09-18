# For generating requirements

pip install pip-tools
pip-compile --python-version=3.14 requirements.in -o p3.14requirements.txt

# For allowing support different versions of libs for different python versions 

### Python 3.13 → use psycopg2-binary
psycopg2-binary ; python_version == "3.13"

### Python 3.14 → use new psycopg[binary]
psycopg[binary] ; python_version == "3.14"
