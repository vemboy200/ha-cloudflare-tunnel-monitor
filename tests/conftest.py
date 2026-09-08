import sys
from pathlib import Path

# The project root (not custom_components/ itself) must be on sys.path, so
# that imports match the same module identity Home Assistant's own loader
# uses when scanning for custom integrations (`import custom_components`,
# then reading its __path__).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
