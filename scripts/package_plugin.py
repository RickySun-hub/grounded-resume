"""Build an allowlisted skills-only ZIP; never include private inputs or caches."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]

def build():
    manifest = json.loads((ROOT / 'plugin.json').read_text(encoding='utf-8'))
    output = ROOT / 'outputs' / 'plugin-package'
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"{manifest['name']}-plugin-{manifest['version']}.zip"
    files = [ROOT/'plugin.json', ROOT/'LICENSE', ROOT/'assets/proofround-icon.png']
    skill = ROOT/'skills/grounded-resume'
    files += [skill/'SKILL.md', skill/'requirements.txt', skill/'LICENSE', skill/'.gitignore']
    for folder, pattern in [('scripts','*.py'), ('references','*.md'), ('agents','*.yaml'),
                            ('assets','*.tex'), ('examples','*.json'), ('examples','*.txt')]:
        files += sorted((skill/folder).glob(pattern))
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as bundle:
        for path in files:
            if path.is_symlink():
                raise ValueError(f'Symlink is not allowed: {path}')
            bundle.write(path, path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        assert 'plugin.json' in bundle.namelist()
        assert not any(name.endswith('mcp.json') or '.app.json' in name for name in bundle.namelist())
        inventory = {name: hashlib.sha256(bundle.read(name)).hexdigest() for name in bundle.namelist()}
    (output/'inventory.json').write_text(json.dumps(inventory, indent=2)+'\n', encoding='utf-8')
    print(archive)
    print(f'files={len(inventory)} sha256={hashlib.sha256(archive.read_bytes()).hexdigest()}')

if __name__ == '__main__':
    build()
