"""Pictures the owner sends (a reference he likes, a screenshot he marked) travel with his words to the builders.

Telegram saves each picture on this machine and passes it on as "<his words> [photo: <path>]". Builders work only in
their own copy of the code, so before a build, a fix round or a mid-build instruction, each picture is copied into
that code (.hive/refs/) and his words name it there: "(his picture: .hive/refs/ref_1.jpg; open it and match it)"."""
import os, re, shutil, subprocess

PHOTO = re.compile(r'\[photo: ([^\]]+)\]')

def has(text):
    return bool(PHOTO.search(text or ''))

def words(text):
    """His words without the picture markers."""
    return ' '.join(PHOTO.sub('', text or '').split())

def attach(text, code_dir, commit=False):
    """Copy every picture named in text into code_dir/.hive/refs and point his words at the copies (optionally commit
    them). Returns the text the builders will read."""
    if not has(text):
        return text
    folder = os.path.join(code_dir, '.hive', 'refs'); os.makedirs(folder, exist_ok=True)
    done = []
    def put(m):
        src = m.group(1).strip()
        if not os.path.exists(src):
            return '(he sent a picture, but it could not be found)'
        n = len(os.listdir(folder)) + 1
        name = f'ref_{n}{os.path.splitext(src)[1] or ".jpg"}'
        shutil.copy(src, os.path.join(folder, name)); done.append(name)
        return f'(his picture: .hive/refs/{name}; open it and match what it shows)'
    out = PHOTO.sub(put, text)
    if commit and done:
        g = lambda *a: subprocess.run(['git', '-C', code_dir, *a], capture_output=True, text=True)
        g('add', '-f', '.hive/refs')
        g('-c', 'user.name=hive', '-c', 'user.email=hive@local', 'commit', '-q', '-m', "hive: the owner's reference pictures")
    return out
