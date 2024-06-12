import sys, os

# Include source folders.
sys.path.insert(0, os.path.abspath('../../services/bot/src/'))
sys.path.insert(0, os.path.abspath('../../services/bot/src/pbot/'))
sys.path.insert(0, os.path.abspath('../../services/bot/src/pbot/middleware'))

sys.path.insert(0, os.path.abspath('../../services/transceiver/src/'))
sys.path.insert(0, os.path.abspath('../../services/transceiver/src/transceiver/'))



release = 0
with open('../../version', 'r') as f:
    release = f.read().strip()

html_title = f"PBot Docs<br/><small>{release}</small>"

project = 'Pbot'
copyright = '2024, Chris Cummings'
author = 'Chris Cummings'

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosummary"
]

autodoc_mock_imports = [
	'tiktoken',
	'openai',
	'pytest'
]

autodoc_default_options = {
    'members':         True,
    'member-order':    'bysource',
    'special-members': '__init__',
}

templates_path = ['_templates']


exclude_patterns = []



html_theme = 'furo'
html_static_path = ['_static']
