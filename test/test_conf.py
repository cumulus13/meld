import importlib.machinery
import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONF_TEMPLATE = ROOT / "meld" / "conf.py.in"


def _load(path: Path):
    # Same approach as bin/meld uses to import conf.py.in from a checkout
    loader = importlib.machinery.SourceFileLoader("meld_conf_under_test", str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def _minor(version: str) -> int:
    # What bin/meld does at startup to decide whether this is a stable release
    return int(version.split(".")[1])


def test_template_version_usable_when_unconfigured():
    # Regression test: running from a source checkout uses conf.py.in as-is.
    # A literal "@version@" has no dots, so bin/meld crashed at startup with
    # "IndexError: list index out of range".
    version = _load(CONF_TEMPLATE).__version__
    assert not version.startswith("@")
    _minor(version)


def test_template_version_is_substituted_when_configured(tmp_path):
    configured = tmp_path / "conf.py"
    configured.write_text(CONF_TEMPLATE.read_text().replace("@version@", "3.99.12"))
    assert _load(configured).__version__ == "3.99.12"


def test_meson_supplies_version_to_conf():
    # Regression test: conf.py.in asks for @version@ but meson did not provide
    # it, so installed builds (e.g. the Windows installer) shipped a literal
    # "@version@" and refused to start.
    meson_build = (ROOT / "meld" / "meson.build").read_text()
    assert "@version@" in CONF_TEMPLATE.read_text()
    configurations = re.findall(r"app_config\s*=\s*\{(.*?)\}", meson_build, re.DOTALL)
    assert configurations
    for configuration in configurations:
        assert "'version': meson.project_version()" in configuration


def test_launcher_survives_unparseable_version():
    launcher = (ROOT / "bin" / "meld").read_text()
    assert "except (IndexError, ValueError):" in launcher
