__author__ = "Jose David Escribano Orts"
__subsystem__ = "tools"
__module__ = "actualizar_libmpv.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

"""Actualiza vendor/libmpv-2.dll desde una release de shinchiro/mpv-winbuild-cmake y regenera sus avisos.

Descarga el paquete mpv-dev x86_64 de la release, comprueba que la DLL carga y
reproduce con python-mpv, reconstruye la versión de cada biblioteca que lleva
dentro y genera la sección de libmpv de THIRD-PARTY-NOTICES.txt y el paso 4 del
README.md. Sin --apply solo deja el resultado en la carpeta de trabajo.

Uso, desde la raíz del repositorio y con el intérprete de biblio_anime_env:

    python tools/actualizar_libmpv.py                       última release, en seco
    python tools/actualizar_libmpv.py --tag 20260923        una release concreta, en seco
    python tools/actualizar_libmpv.py --tag 20260923 --apply

Por qué hace falta reconstruir: la receta de shinchiro clona cada biblioteca en
la versión que tenga su rama al compilar y no la anota en ningún sitio. Aquí se
toma el último commit de esa rama anterior al arranque de la compilación; mpv y
FFmpeg se comprueban contra el hash que lleva el nombre del paquete.
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import textwrap
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import requests

ROOT = Path(__file__).resolve().parent.parent
VENDOR_DLL = ROOT / "vendor" / "libmpv-2.dll"
NOTICES = ROOT / "THIRD-PARTY-NOTICES.txt"
README = ROOT / "README.md"

RECIPE = "shinchiro/mpv-winbuild-cmake"
API = f"https://api.github.com/repos/{RECIPE}"
RAW = f"https://raw.githubusercontent.com/{RECIPE}"
DEV_ASSET_RE = re.compile(r"^mpv-dev-x86_64-(\d{8})-git-([0-9a-f]+)\.7z$")
FFMPEG_ASSET_RE = re.compile(r"^ffmpeg-x86_64-git-([0-9a-f]+)\.7z$")
RUN_URL_RE = re.compile(r"https://github\.com/[^/]+/[^/]+/actions/runs/(\d+)")

#: Variables de la compilación de la que sale el paquete x86_64 básico (no el -v3).
BUILD_VARS = {
    "TARGET_ARCH": "x86_64-w64-mingw32",
    "TARGET_CPU": "x86_64",
    "COMPILER_TOOLCHAIN": "clang",
    "CLANG_PACKAGES_LTO": "ON",
}

NOTICES_BEGIN = "#### INICIO libmpv · generado por tools/actualizar_libmpv.py, no editar a mano ####"
NOTICES_END = "#### FIN libmpv ####"
README_BEGIN = "<!-- libmpv:inicio · generado por tools/actualizar_libmpv.py -->"
README_END = "<!-- libmpv:fin -->"

LICENSE_NAME_RE = re.compile(r"^(licen[cs]e|copying|copyright|notice|unlicense)([._-][\w.+-]*)?"
                             r"(?<!\.cfg)(?<!\.py)(?<!\.sh)(?<!\.json)(?<!\.toml)(?<!\.yml)(?<!\.yaml)"
                             r"(?<!\.in)(?<!\.cmake)(?<!\.c)(?<!\.h)(?<!\.html)$", re.I)
LICENSE_DIR_RE = re.compile(r"^licen[cs]es$", re.I)
#: Licencias fuera de la raíz de algunos repositorios.
EXTRA_LICENSE_FILES = {
    "mingw-w64": ["mingw-w64-libraries/winpthreads/COPYING"],
}
#: Repositorios cuya licencia va en el comentario inicial de sus cabeceras.
HEADER_LICENSE_FILES = {
    "nvcodec-headers": ["include/ffnvcodec/nvEncodeAPI.h", "include/ffnvcodec/dynlink_loader.h"],
    "avisynth-headers": ["avs_core/include/avisynth_c.h"],
}
#: Lo que hay que saber de un paquete para leer bien su entrada.
SOURCE_NOTES = {
    "opus-dnn": "datos del modelo neuronal de Opus, con la licencia de opus (ver su entrada)",
    "avisynth-headers": "solo sus cabeceras C: FFmpeg carga AviSynth.dll si está instalado",
    "nvcodec-headers": "solo cabeceras; la licencia va en cada fichero",
}
#: Pausa entre peticiones HTTP, para no martillear a nadie.
HTTP_PAUSE_S = 0.3
#: Historia que se baja de cada repositorio: de sobra para encontrar el commit de la fecha.
SHALLOW_DAYS = 400

_session = requests.Session()
_session.headers["User-Agent"] = "BibliotecaAnime-actualizar-libmpv"


def log(message: str) -> None:
    print(message, flush=True)


# ---- Red y git ----
def http_get(url: str, api: bool = False, stream: bool = False) -> requests.Response:
    """GET con pausa previa y error si no es 2xx. :param api: si va a la API de GitHub."""
    time.sleep(HTTP_PAUSE_S)
    headers = {}
    if api:
        headers["Accept"] = "application/vnd.github+json"
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
    response = _session.get(url, headers=headers, timeout=120, stream=stream)
    response.raise_for_status()
    return response


def download(url: str, dest: Path, size: Optional[int] = None) -> Path:
    """Descarga a disco, reutilizando lo ya bajado si coincide el tamaño."""
    if dest.exists() and (size is None or dest.stat().st_size == size):
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_name(dest.name + ".part")
    with http_get(url, stream=True) as response, open(partial, "wb") as handle:
        for chunk in response.iter_content(1 << 20):
            handle.write(chunk)
    partial.replace(dest)
    return dest


def git(*args: str, cwd: Optional[Path] = None, check: bool = True) -> str:
    """Ejecuta git sin pedir credenciales. :return: la salida estándar."""
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env)
    if check and proc.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {proc.stderr.strip()[-400:]}")
    return proc.stdout


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def system_tar() -> str:
    """El tar de Windows (bsdtar), que abre .7z; el de Git for Windows no."""
    candidate = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "tar.exe"
    return str(candidate) if candidate.exists() else "tar"


# ---- Release ----
@dataclass
class Release:
    tag: str
    dev_asset: str
    dev_url: str
    dev_size: int
    mpv_hash: str
    ffmpeg_hash: Optional[str]
    recipe_commit: str
    cutoff: dt.datetime
    cutoff_source: str


def fetch_release(tag: str) -> Release:
    """Lee la release, su paquete mpv-dev x86_64, el commit de la receta y la hora de la compilación."""
    url = f"{API}/releases/latest" if tag == "latest" else f"{API}/releases/tags/{tag}"
    data = http_get(url, api=True).json()
    dev = next((a for a in data["assets"] if DEV_ASSET_RE.match(a["name"])), None)
    if dev is None:
        raise SystemExit(f"La release {data['tag_name']} no trae el paquete mpv-dev-x86_64")
    ffmpeg = next((FFMPEG_ASSET_RE.match(a["name"]) for a in data["assets"]
                   if FFMPEG_ASSET_RE.match(a["name"])), None)

    ref = http_get(f"{API}/git/ref/tags/{data['tag_name']}", api=True).json()["object"]
    if ref["type"] == "tag":
        ref = http_get(f"{API}/git/tags/{ref['sha']}", api=True).json()["object"]

    cutoff_text, cutoff_source = data["created_at"], "creación de la release"
    run = RUN_URL_RE.search(data.get("body") or "")
    if run:
        run_data = http_get(f"{API}/actions/runs/{run.group(1)}", api=True).json()
        cutoff_text = run_data.get("run_started_at") or run_data["created_at"]
        cutoff_source = f"arranque de la compilación ({run.group(0)})"
    return Release(
        tag=data["tag_name"],
        dev_asset=dev["name"],
        dev_url=dev["browser_download_url"],
        dev_size=dev["size"],
        mpv_hash=DEV_ASSET_RE.match(dev["name"]).group(2),
        ffmpeg_hash=ffmpeg.group(1) if ffmpeg else None,
        recipe_commit=ref["sha"],
        cutoff=dt.datetime.fromisoformat(cutoff_text.replace("Z", "+00:00")),
        cutoff_source=cutoff_source,
    )


def extract_dll(archive: Path, out_dir: Path) -> Path:
    """Saca libmpv-2.dll del .7z con el tar de Windows."""
    out_dir.mkdir(parents=True, exist_ok=True)
    tar = system_tar()
    names = subprocess.run([tar, "-tf", str(archive)], capture_output=True, text=True, check=True).stdout.split()
    member = next((n for n in names if n.split("/")[-1] == "libmpv-2.dll"), None)
    if member is None:
        raise SystemExit(f"{archive.name} no contiene libmpv-2.dll")
    subprocess.run([tar, "-xf", str(archive), "-C", str(out_dir), member], check=True)
    extracted = out_dir / member
    final = out_dir / "libmpv-2.dll"
    if extracted != final:
        shutil.move(str(extracted), final)
    return final


SMOKE_TEST = r'''
import json, os, sys, time
dll_dir = sys.argv[1]
os.environ["PATH"] = dll_dir + os.pathsep + os.environ["PATH"]
os.add_dll_directory(dll_dir)
import mpv
result = {}
player = mpv.MPV(vo="null", ao="null", ytdl=False, keep_open="yes")
result["mpv_version"] = player._get_property("mpv-version")
result["ffmpeg_version"] = player._get_property("ffmpeg-version")
for name, url in (("video", "av://lavfi:testsrc2=duration=30:size=320x240:rate=24"),
                  ("audio", "av://lavfi:sine=frequency=440:duration=30")):
    player.play(url)
    deadline = time.monotonic() + 15
    position = None
    while time.monotonic() < deadline:
        position = player.time_pos
        if position is not None and position > 1.0:
            break
        time.sleep(0.1)
    result[name] = position is not None and position > 1.0
player.terminate()
print(json.dumps(result))
'''


def smoke_test(dll: Path) -> dict:
    """Carga la DLL con python-mpv en otro proceso y reproduce un vídeo y un audio sintéticos."""
    proc = subprocess.run([sys.executable, "-c", SMOKE_TEST, str(dll.parent)],
                          capture_output=True, text=True, timeout=120)
    lines = [line for line in proc.stdout.splitlines() if line.startswith("{")]
    if proc.returncode or not lines:
        raise SystemExit(f"La DLL no pasa la prueba de humo:\n{proc.stdout}\n{proc.stderr}")
    return json.loads(lines[-1])


# ---- Receta (CMake) ----
@dataclass
class Target:
    name: str
    depends: List[str]
    git_repository: Optional[str] = None
    git_tag: Optional[str] = None
    url: Optional[str] = None
    url_hash: Optional[str] = None
    git_submodules: Optional[str] = None


def strip_comments(text: str) -> str:
    out = []
    for line in text.splitlines():
        in_quotes = False
        for i, char in enumerate(line):
            if char == '"' and (i == 0 or line[i - 1] != "\\"):
                in_quotes = not in_quotes
            elif char == "#" and not in_quotes:
                line = line[:i]
                break
        out.append(line)
    return "\n".join(out)


def cmake_commands(text: str) -> List[Tuple[str, List[str]]]:
    """Trocea un fichero CMake en (comando, argumentos), respetando comillas y paréntesis."""
    text = strip_comments(text)
    commands, i = [], 0
    pattern = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(")
    while True:
        match = pattern.search(text, i)
        if not match:
            return commands
        depth, j, in_quotes, start = 1, match.end(), False, match.end()
        while j < len(text) and depth:
            char = text[j]
            if char == '"' and text[j - 1] != "\\":
                in_quotes = not in_quotes
            elif not in_quotes and char == "(":
                depth += 1
            elif not in_quotes and char == ")":
                depth -= 1
            j += 1
        body = text[start:j - 1]
        commands.append((match.group(1).lower(), re.findall(r'"(?:[^"\\]|\\.)*"|[^\s"]+', body)))
        i = j


class CMakeState:
    """Lo justo de CMake para seguir los if() y set() que eligen dependencias según la arquitectura."""

    TRUE = {"1", "ON", "YES", "TRUE", "Y"}
    FALSE = {"", "0", "OFF", "NO", "FALSE", "N", "IGNORE", "NOTFOUND"}

    def __init__(self, variables: Dict[str, str]):
        self.vars = dict(variables)
        self.stack: List[List[bool]] = []  # [activo_el_padre, ya_se_tomó_una_rama, activo]

    def active(self) -> bool:
        return all(frame[2] for frame in self.stack)

    def subst(self, text: str) -> str:
        for _ in range(5):
            new = re.sub(r"\$\{(\w+)\}", lambda m: self.vars.get(m.group(1), ""), text)
            if new == text:
                break
            text = new
        return text

    def __value(self, token: str) -> str:
        if token.startswith('"'):
            return self.subst(token[1:-1])
        text = self.subst(token)
        return self.vars.get(text, text) if re.fullmatch(r"[A-Za-z_]\w*", text) else text

    def __truthy(self, token: str) -> bool:
        text = self.subst(token.strip('"'))
        if text.upper() in self.TRUE:
            return True
        if text.upper() in self.FALSE or text.upper().endswith("-NOTFOUND"):
            return False
        if re.fullmatch(r"[A-Za-z_]\w*", text):
            return self.__truthy(self.vars.get(text, "")) if text in self.vars else False
        return False

    def condition(self, tokens: List[str]) -> bool:
        tokens = list(tokens)

        def parse_or():
            value = parse_and()
            while tokens and tokens[0] == "OR":
                tokens.pop(0)
                value = parse_and() or value
            return value

        def parse_and():
            value = parse_not()
            while tokens and tokens[0] == "AND":
                tokens.pop(0)
                value = parse_not() and value
            return value

        def parse_not():
            if tokens and tokens[0] == "NOT":
                tokens.pop(0)
                return not parse_not()
            return parse_primary()

        def parse_primary():
            if not tokens:
                return False
            head = tokens.pop(0)
            if head == "(":
                value = parse_or()
                if tokens and tokens[0] == ")":
                    tokens.pop(0)
                return value
            if head in ("EXISTS", "POLICY", "TARGET", "COMMAND", "IS_DIRECTORY"):
                tokens.pop(0) if tokens else None
                return False
            if head == "DEFINED":
                return bool(tokens) and tokens.pop(0) in self.vars
            if tokens and tokens[0] in ("STREQUAL", "MATCHES", "EQUAL", "VERSION_GREATER_EQUAL",
                                        "VERSION_LESS", "VERSION_GREATER", "STRLESS", "STRGREATER"):
                op = tokens.pop(0)
                right = tokens.pop(0) if tokens else '""'
                left_value, right_value = self.__value(head), self.__value(right)
                if op == "STREQUAL" or op == "EQUAL":
                    return left_value == right_value
                if op == "MATCHES":
                    return re.search(right_value, left_value) is not None
                return False
            return self.__truthy(head)

        # Los paréntesis pueden llegar pegados a los tokens.
        expanded = []
        for token in tokens:
            if token.startswith('"'):
                expanded.append(token)
            else:
                expanded.extend(t for t in re.split(r"([()])", token) if t)
        tokens[:] = expanded
        return parse_or()

    def run(self, commands: List[Tuple[str, List[str]]], targets: Dict[str, Target]) -> None:
        for name, args in commands:
            if name == "if":
                parent = self.active()
                taken = parent and self.condition(args)
                self.stack.append([parent, taken, taken])
            elif name == "elseif" and self.stack:
                frame = self.stack[-1]
                go = frame[0] and not frame[1] and self.condition(args)
                frame[2] = go
                frame[1] = frame[1] or go
            elif name == "else" and self.stack:
                frame = self.stack[-1]
                frame[2] = frame[0] and not frame[1]
                frame[1] = True
            elif name == "endif" and self.stack:
                self.stack.pop()
            elif not self.active():
                continue
            elif name == "set" and args:
                values = args[1:]
                if "CACHE" in values:
                    values = values[:values.index("CACHE")]
                    if args[0] in self.vars:
                        continue
                self.vars[args[0]] = " ".join(self.subst(v.strip('"')) for v in values)
            elif name == "externalproject_add" and args:
                target = self.__target(args)
                targets[target.name] = target

    def __target(self, args: List[str]) -> Target:
        keyword = re.compile(r"^[A-Z][A-Z0-9_]+$")
        target = Target(name=self.subst(args[0]), depends=[])
        current = None
        for raw in args[1:]:
            if keyword.match(raw):
                current = raw
                continue
            value = self.subst(raw.strip('"'))
            if current == "DEPENDS":
                target.depends.extend(v for v in re.split(r"[;\s]+", value) if v)
            elif current == "GIT_REPOSITORY" and target.git_repository is None:
                target.git_repository = value
            elif current == "GIT_TAG" and target.git_tag is None:
                target.git_tag = value
            elif current == "URL" and target.url is None:
                target.url = value
            elif current == "URL_HASH" and target.url_hash is None:
                target.url_hash = value
            elif current == "GIT_SUBMODULES" and target.git_submodules is None:
                target.git_submodules = value
        # «GIT_SUBMODULES» sin valor también desactiva los submódulos.
        if "GIT_SUBMODULES" in args and target.git_submodules is None:
            target.git_submodules = ""
        return target


class Recipe:
    """Los ficheros de la receta en un commit, leídos de raw.githubusercontent.com."""

    def __init__(self, commit: str):
        self.commit = commit
        self.__cache: Dict[str, str] = {}

    def text(self, path: str) -> str:
        if path not in self.__cache:
            self.__cache[path] = http_get(f"{RAW}/{self.commit}/{path}").text
        return self.__cache[path]

    def targets(self) -> Tuple[Dict[str, Target], Dict[str, str]]:
        """Evalúa los paquetes en el orden de la receta. :return: objetivos y variables finales."""
        state = CMakeState(BUILD_VARS)
        targets: Dict[str, Target] = {}
        state.run(cmake_commands(self.text("cmake/packages_check.cmake")), targets)
        listing = self.text("packages/CMakeLists.txt")
        block = re.search(r"list\(APPEND ep(.*?)\)", listing, re.S).group(1)
        for package in block.split():
            log(f"  receta: {package}")
            state.run(cmake_commands(self.text(f"packages/{package}.cmake")), targets)
        mingw = {}
        state.run(cmake_commands(self.text("toolchain/mingw-w64.cmake")), mingw)
        targets.update(mingw)
        return targets, state.vars


def closure(targets: Dict[str, Target], root: str) -> List[str]:
    """Todo lo que root necesita, directa o indirectamente, en orden estable."""
    seen, order, pending = set(), [], [root]
    while pending:
        name = pending.pop(0)
        if name in seen:
            continue
        seen.add(name)
        order.append(name)
        target = targets.get(name)
        if target is None:
            log(f"  ⚠ {name}: no está en la receta")
            continue
        pending.extend(target.depends)
    return order


# ---- Fuentes y licencias ----
@dataclass
class Source:
    name: str
    kind: str
    origin: str
    ref: str
    exact: bool
    note: str = ""
    licenses: List[Tuple[str, str]] = field(default_factory=list)
    children: List["Source"] = field(default_factory=list)


def _safe(name: str) -> str:
    return re.sub(r"[^\w.+-]", "_", name)


def clone_history(url: str, dest: Path, branch: Optional[str], since: dt.datetime) -> None:
    """Clon desnudo sin árboles ni ficheros: solo los commits del último año y pico."""
    if dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    base = ["clone", "--bare", "--filter=tree:0", "--single-branch"]
    if branch:
        base += ["--branch", branch]
    try:
        git(*base, f"--shallow-since={since:%Y-%m-%d}", url, str(dest))
    except RuntimeError:
        shutil.rmtree(dest, ignore_errors=True)
        git(*base, url, str(dest))


def license_files_at(repo: Path, commit: str, package: str = "") -> List[Tuple[str, str]]:
    """Los ficheros de licencia de la raíz y de sus carpetas de licencias en un commit, bajados a demanda.

    :param package: Nombre del paquete en la receta, para sus licencias fuera de la raíz.
    """
    found = []
    for line in git("ls-tree", commit, cwd=repo).splitlines():
        meta, name = line.split("\t", 1)
        kind = meta.split()[1]
        if kind == "blob" and LICENSE_NAME_RE.match(name):
            found.append((name, git("cat-file", "-p", f"{commit}:{name}", cwd=repo)))
        elif kind == "tree" and (LICENSE_DIR_RE.match(name) or LICENSE_NAME_RE.match(name)):
            for sub in git("ls-tree", "--name-only", f"{commit}:{name}", cwd=repo).splitlines():
                found.append((f"{name}/{sub}", git("cat-file", "-p", f"{commit}:{name}/{sub}", cwd=repo)))
    for path in EXTRA_LICENSE_FILES.get(package, []):
        found.append((path, git("cat-file", "-p", f"{commit}:{path}", cwd=repo)))
    for path in HEADER_LICENSE_FILES.get(package, []):
        text = header_license(git("cat-file", "-p", f"{commit}:{path}", cwd=repo))
        if text:
            found.append((f"{path} (comentario de cabecera)", text))
    return found


def header_license(source: str) -> Optional[str]:
    """El aviso de licencia del comentario inicial de un fichero C, en /* */ o en líneas //."""
    block = re.match(r"\s*/\*(.*?)\*/", source, re.S)
    if block:
        lines = [re.sub(r"^\s?\*\s?", "", line) for line in block.group(1).strip("\n").splitlines()]
        return "\n".join(lines).strip() + "\n"
    # En líneas //: los párrafos iniciales mientras hablen de licencia o copyright.
    keywords = re.compile(r"licen[cs]e|copyright|permission|warranty|exception", re.I)
    paragraphs, current = [], []
    for line in source.splitlines():
        if line.startswith("//"):
            current.append(re.sub(r"^//\s?", "", line))
        elif not line.strip():
            if current:
                paragraphs.append(current)
                current = []
        else:
            break
    if current:
        paragraphs.append(current)
    kept = []
    for paragraph in paragraphs:
        if not keywords.search(" ".join(paragraph)):
            break
        kept.append("\n".join(paragraph).strip())
    return "\n\n".join(kept) + "\n" if kept else None


def submodules_at(repo: Path, commit: str, parent_url: str, work: Path) -> List[Source]:
    """Los submódulos del commit, cada uno en el commit exacto que fija el padre."""
    try:
        gitmodules = git("cat-file", "-p", f"{commit}:.gitmodules", cwd=repo)
    except RuntimeError:
        return []
    children = []
    for block in re.split(r"\[submodule ", gitmodules)[1:]:
        path = re.search(r"path\s*=\s*(\S+)", block)
        url = re.search(r"url\s*=\s*(\S+)", block)
        if not path or not url:
            continue
        sub_url = url.group(1)
        if sub_url.startswith("../") or sub_url.startswith("./"):
            sub_url = requests.compat.urljoin(parent_url.rstrip("/") + "/", sub_url)
        entry = git("ls-tree", commit, "--", path.group(1), cwd=repo).split()
        if len(entry) < 3 or entry[1] != "commit":
            continue
        sha = entry[2]
        # Nombre corto: con la URL entera la ruta pasa del límite de Windows.
        sub_repo = work / "submodules" / f"{hashlib.sha1(sub_url.encode()).hexdigest()[:10]}-{sha[:12]}"
        source = Source(name=path.group(1), kind="submódulo", origin=sub_url, ref=sha, exact=True,
                        note="submódulo fijado por el padre (puede ser solo de pruebas o de compilación)")
        try:
            if not sub_repo.exists():
                git("init", "--bare", "-q", str(sub_repo))
                git("fetch", "-q", "--depth=1", "--filter=blob:none", sub_url, sha, cwd=sub_repo)
            source.licenses = license_files_at(sub_repo, sha)
        except RuntimeError as exc:
            source.note += f"; ⚠ no se pudieron leer sus licencias ({str(exc).splitlines()[0][:120]})"
        children.append(source)
    return children


def resolve_git(target: Target, release: Release, work: Path, known: Optional[str]) -> Source:
    """El commit que se compiló: el exacto si se conoce, si no el último de la rama antes del corte."""
    repo = work / "repos" / f"{_safe(target.name)}.git"
    since = release.cutoff - dt.timedelta(days=SHALLOW_DAYS)
    clone_history(target.git_repository, repo, target.git_tag, since)
    is_branch = not target.git_tag or git("show-ref", f"refs/heads/{target.git_tag}", cwd=repo, check=False).strip()
    cutoff = release.cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
    line = git("log", "--first-parent", "-1", "--format=%H %cI", f"--before={cutoff}", "HEAD", cwd=repo).strip()
    if not line:
        shutil.rmtree(repo, ignore_errors=True)
        git("clone", "--bare", "--filter=tree:0", "--single-branch",
            *(["--branch", target.git_tag] if target.git_tag else []), target.git_repository, str(repo))
        line = git("log", "--first-parent", "-1", "--format=%H %cI", f"--before={cutoff}", "HEAD", cwd=repo).strip()
    reconstructed, date = line.split()
    source = Source(name=target.name, kind="git", origin=target.git_repository, ref=reconstructed, exact=False,
                    note=f"último commit de «{target.git_tag or 'rama por defecto'}» antes del corte ({date})")
    if not is_branch:
        source.ref = git("rev-parse", "HEAD^{commit}", cwd=repo).strip()
        source.exact = True
        source.note = f"etiqueta {target.git_tag}, fijada por la receta"
    elif known:
        full = git("rev-parse", f"{known}^{{commit}}", cwd=repo).strip()
        match = full == reconstructed
        source.ref, source.exact = full, True
        source.note = (f"commit exacto (consta en el nombre del paquete); la reconstrucción "
                       f"{'coincide' if match else 'NO coincide: ' + reconstructed[:12]}")
    source.licenses = license_files_at(repo, source.ref, target.name)
    if target.git_submodules is None:
        source.children = submodules_at(repo, source.ref, target.git_repository, work)
    return source


def resolve_url(target: Target, work: Path) -> Source:
    """Un paquete descargado como archivo: la versión la fija la URL."""
    name = target.url.rsplit("/", 1)[-1].split("?")[0]
    archive = download(target.url, work / "tarballs" / name)
    note = "versión fijada por la URL de la receta"
    if target.url_hash and target.url_hash.upper().startswith("SHA256="):
        expected = target.url_hash.split("=", 1)[1].lower()
        note += "; sha256 comprobado" if sha256_of(archive) == expected else "; ⚠ sha256 NO coincide"
    source = Source(name=target.name, kind="archivo", origin=target.url, ref=name, exact=True, note=note)
    source.licenses = archive_license_files(archive)
    return source


def archive_license_files(archive: Path, prefix: Optional[str] = None) -> List[Tuple[str, str]]:
    """Ficheros de licencia del primer nivel de un .tar.* o .zip."""
    found = []

    def wanted(member: str) -> bool:
        parts = member.strip("/").split("/")
        if prefix is not None and parts[0] != prefix:
            return False
        return len(parts) == 2 and bool(LICENSE_NAME_RE.match(parts[1]))

    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as handle:
            for member in handle.namelist():
                if wanted(member):
                    found.append((member.split("/", 1)[1], handle.read(member).decode("utf-8", "replace")))
    else:
        with tarfile.open(archive, "r:*") as handle:
            for member in handle.getmembers():
                if member.isfile() and wanted(member.name):
                    data = handle.extractfile(member).read()
                    found.append((member.name.split("/", 1)[1], data.decode("utf-8", "replace")))
    return found


def resolve_crates(repo: Path, commit: str, root_crate: str, work: Path) -> List[Source]:
    """Las crates de Rust que entran en root_crate según su Cargo.lock, con sus licencias."""
    try:
        lock = git("cat-file", "-p", f"{commit}:Cargo.lock", cwd=repo)
    except RuntimeError:
        return []
    packages = {}
    for block in lock.split("[[package]]")[1:]:
        name = re.search(r'^name = "([^"]+)"', block, re.M).group(1)
        version = re.search(r'^version = "([^"]+)"', block, re.M).group(1)
        source = re.search(r'^source = "([^"]+)"', block, re.M)
        deps_block = re.search(r"^dependencies = \[(.*?)\]", block, re.M | re.S)
        deps = re.findall(r'"([^"]+)"', deps_block.group(1)) if deps_block else []
        packages.setdefault(name, []).append({"version": version, "registry": bool(source), "deps": deps})

    def pick(spec: str):
        parts = spec.split()
        candidates = packages.get(parts[0], [])
        if len(parts) > 1:
            candidates = [c for c in candidates if c["version"] == parts[1]] or candidates
        return parts[0], candidates[0] if candidates else None

    seen: Set[Tuple[str, str]] = set()
    pending = [root_crate]
    crates = []
    while pending:
        name, entry = pick(pending.pop())
        if entry is None or (name, entry["version"]) in seen:
            continue
        seen.add((name, entry["version"]))
        pending.extend(entry["deps"])
        if not entry["registry"]:
            continue
        version = entry["version"]
        archive = download(f"https://static.crates.io/crates/{name}/{name}-{version}.crate",
                           work / "crates" / f"{name}-{version}.crate")
        source = Source(name=f"{name} {version}", kind="crate", origin=f"https://crates.io/crates/{name}/{version}",
                        ref=version, exact=True, note="fijada por Cargo.lock")
        with tarfile.open(archive, "r:gz") as handle:
            manifest = handle.extractfile(f"{name}-{version}/Cargo.toml")
            declared = re.search(r'^license\s*=\s*"([^"]+)"', manifest.read().decode("utf-8", "replace"), re.M) \
                if manifest else None
        if declared:
            source.note += f"; licencia declarada: {declared.group(1)}"
        source.licenses = archive_license_files(archive, prefix=f"{name}-{version}")
        crates.append(source)
    return sorted(crates, key=lambda s: s.name)


def rust_std(release: Release) -> Source:
    """La biblioteca estándar de Rust del nightly de ese día, que va enlazada con subrandr."""
    until = release.cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        commit = http_get(f"https://api.github.com/repos/rust-lang/rust/commits?until={until}&per_page=1",
                          api=True).json()[0]["sha"]
    except (requests.RequestException, IndexError, KeyError) as exc:
        return Source(name="Rust (biblioteca estándar)", kind="?", origin="https://github.com/rust-lang/rust",
                      ref="?", exact=False, note=f"⚠ no se pudo resolver: {exc}")
    source = Source(name="Rust (biblioteca estándar)", kind="cadena de herramientas",
                    origin="https://github.com/rust-lang/rust", ref=commit, exact=False,
                    note="nightly del día de la compilación; commit aproximado")
    for name in ("COPYRIGHT", "LICENSE-MIT", "LICENSE-APACHE"):
        try:
            source.licenses.append((name, http_get(f"https://raw.githubusercontent.com/rust-lang/rust/{commit}/{name}").text))
        except requests.HTTPError:
            pass
    return source


# ---- Textos de licencia ----
#: (identificador, frase de cabecera normalizada, longitud máxima del texto estándar)
CANONICAL = [
    ("GPL-3.0", "gnu general public license version 3 29 june 2007", 40000),
    ("LGPL-3.0", "gnu lesser general public license version 3 29 june 2007", 9500),
    ("GPL-2.0", "gnu general public license version 2 june 1991", 20000),
    ("LGPL-2.1", "gnu lesser general public license version 21 february 1999", 28500),
    ("LGPL-2.0", "gnu library general public license version 2 june 1991", 28000),
    ("Apache-2.0", "apache license version 20 january 2004", 12500),
    ("MPL-2.0", "mozilla public license version 20", 17500),
    ("MPL-1.1", "mozilla public license version 11", 30000),
]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", "", text.lower())).strip()


def canonical_id(text: str) -> Optional[str]:
    head = normalize(text[:1500])
    for spdx, phrase, max_len in CANONICAL:
        if phrase in head and len(text) <= max_len:
            return spdx
    return None


def guess_license(text: str) -> str:
    norm = normalize(text)
    spdx = canonical_id(text)
    if spdx:
        return spdx
    for spdx, phrase, _ in CANONICAL:
        if phrase in norm[:3000]:
            return spdx + " (con añadidos)"
    rules = [
        ("MIT", "permission is hereby granted free of charge"),
        ("BSD", "redistribution and use in source and binary forms"),
        ("ISC", "permission to use copy modify andor distribute this software for any purpose"),
        ("zlib", "this software is provided asis without any express or implied warranty"),
        ("Unicode", "unicode inc"),
        ("dominio público", "public domain"),
    ]
    found = [spdx for spdx, phrase in rules if phrase in norm]
    return ", ".join(found) if found else "otra (ver texto)"


@dataclass
class LicenseTexts:
    """Los textos únicos: los estándar, una vez; los demás, deduplicados por contenido."""
    common: Dict[str, str] = field(default_factory=dict)
    unique: Dict[str, Tuple[str, str]] = field(default_factory=dict)  # clave -> (etiqueta, texto)
    __keys: Dict[str, str] = field(default_factory=dict)

    def ref(self, owner: str, filename: str, text: str) -> str:
        spdx = canonical_id(text)
        if spdx:
            if spdx != "GPL-3.0":
                self.common.setdefault(spdx, text)
            return f"texto estándar {spdx}" + (" (fichero LICENSE)" if spdx == "GPL-3.0" else "")
        digest = hashlib.sha1(normalize(text).encode()).hexdigest()
        if digest not in self.__keys:
            key = f"T{len(self.__keys) + 1}"
            self.__keys[digest] = key
            self.unique[key] = (f"{owner} · {filename}", text)
        return self.__keys[digest]


# ---- Salida ----
RULE = "=" * 79
SUBRULE = "-" * 44


def wrap(text: str) -> str:
    # Sin partir por guiones ni palabras largas: las URL tienen que poder copiarse enteras.
    return "\n".join(textwrap.fill(p, 79, break_on_hyphens=False, break_long_words=False) if p.strip() else ""
                     for p in text.split("\n"))


def render_notices(release: Release, dll_sha: str, versions: dict, sources: List[Source]) -> str:
    """La sección de libmpv de THIRD-PARTY-NOTICES.txt, entre sus marcas."""
    texts = LicenseTexts()
    rows = []

    def describe(source: Source, indent: str = "  ") -> None:
        refs = [f"{name}: {texts.ref(source.name, name, text)}" for name, text in source.licenses]
        kinds = sorted({guess_license(text) for _, text in source.licenses})
        rows.append(f"{indent}- {source.name}  [{source.kind}]")
        rows.append(f"{indent}    origen:   {source.origin}")
        rows.append(f"{indent}    versión:  {source.ref}{'' if source.exact else ' (reconstruida)'}")
        rows.append(f"{indent}    nota:     {source.note}")
        rows.append(f"{indent}    licencia: {', '.join(kinds) if kinds else 'sin fichero de licencia en la raíz: ver su origen'}")
        for ref in refs:
            rows.append(f"{indent}              {ref}")
        for child in source.children:
            describe(child, indent + "    ")

    for source in sources:
        describe(source)

    reconstructed = sum(1 for s in sources if not s.exact)
    cutoff = release.cutoff.strftime("%Y-%m-%d %H:%M:%S UTC")
    out = [NOTICES_BEGIN, RULE,
           f"libmpv ({versions['mpv_version']})",
           "Licencia: GPL-3.0-or-later (conjunto mpv + FFmpeg)",
           "Proyecto: https://mpv.io", RULE, "",
           "Fichero: _internal/vendor/libmpv-2.dll",
           f"Versión: {versions['mpv_version']} · FFmpeg {versions['ffmpeg_version']}",
           f"Compilación: {RECIPE}, versión {release.tag}",
           f"  ({release.dev_asset})",
           f"SHA-256: {dll_sha}", ""]
    out.append(wrap(
        "mpv es Copyright (C) los desarrolladores de mpv, y se distribuye bajo la GNU General Public "
        "License, versión 2 o (a tu elección) cualquier versión posterior. Esta compilación no usa la "
        "opción que la restringe a la LGPL.\n\n"
        "La DLL lleva enlazado estáticamente FFmpeg (Copyright (C) los desarrolladores de FFmpeg), "
        "compilado con --enable-gpl y --enable-version3, sin --enable-nonfree. Por eso el conjunto se "
        "distribuye bajo la GNU General Public License, versión 3 o posterior: la misma licencia de "
        "BibliotecaAnime, cuyo texto íntegro está en el fichero LICENSE.\n\n"
        "Además de mpv y FFmpeg, la DLL incorpora las bibliotecas que se listan más abajo, cada una con "
        "su propia licencia y su propio aviso de copyright, que se reproducen al final de esta sección."))
    out += ["", "Código fuente correspondiente (§6 de la GPL)", SUBRULE]
    out.append(wrap(
        f"La receta de compilación es {RECIPE} en la etiqueta {release.tag} "
        f"(commit {release.recipe_commit}): https://github.com/{RECIPE}/tree/{release.recipe_commit}\n\n"
        "Esa receta fija las opciones de compilación, pero no la versión de cada biblioteca: las descarga "
        "en la que tenga su rama en el momento de compilar, y no la anota. Por eso, debajo de cada "
        "biblioteca se indica su origen y su versión:\n\n"
        "- exacta, cuando la fija la receta (un archivo con versión, una etiqueta, un submódulo o un "
        "Cargo.lock) o consta en el nombre del paquete (mpv y FFmpeg);\n"
        f"- reconstruida, en las demás ({reconstructed}): el último commit de la rama que usa la receta "
        f"anterior al {cutoff}, {release.cutoff_source}.\n\n"
        "El código fuente de cada versión está en su origen. Si alguno deja de estar disponible, pide el "
        "código fuente correspondiente a esta versión en https://github.com/DavidEscri/BibliotecaAnime "
        "(sección «Issues») y se te facilitará."))
    out += ["", "Bibliotecas incluidas en la DLL", SUBRULE]
    out += rows
    out += ["", "Cadena de herramientas", SUBRULE]
    out.append(wrap(
        "La DLL se compila con LLVM/Clang. Las partes de su biblioteca de ejecución que quedan dentro "
        "(libc++, libunwind, compiler-rt) están bajo Apache-2.0 WITH LLVM-exception, cuya excepción "
        "permite distribuirlas incrustadas sin reproducir su aviso. Las de mingw-w64 (CRT y "
        "winpthreads) y, si se usa, la biblioteca estándar de Rust van en la lista de arriba."))
    out += ["", "Textos de licencia propios de cada biblioteca", SUBRULE, ""]
    for key, (label, text) in texts.unique.items():
        out += [f"[{key}] {label}", "." * 79, text.rstrip(), ""]
    out += ["Textos de licencia estándar", SUBRULE]
    out.append(wrap("GPL-3.0: ver el fichero LICENSE que acompaña a este programa."))
    out.append("")
    for spdx, text in sorted(texts.common.items()):
        out += [f"[{spdx}]", "." * 79, text.rstrip(), ""]
    out.append(NOTICES_END)
    # Hay licencias que llegan con CRLF o con CR sueltos: todo a \n, y el fichero decide al escribir.
    return ("\n".join(out) + "\n").replace("\r\n", "\n").replace("\r", "\n")


def render_readme(release: Release, dll_sha: str) -> str:
    return "\n".join([
        README_BEGIN,
        f"1. Descarga `{release.dev_asset}` de",
        f"   [{RECIPE}, versión {release.tag}](https://github.com/{RECIPE}/releases/tag/{release.tag})",
        "   (el build `x86_64` básico; el `-v3` exige un procesador con AVX2).",
        "2. Extrae `libmpv-2.dll` en la carpeta `vendor/` de la raíz del proyecto (`vendor/libmpv-2.dll`).",
        "3. Comprueba que es la versión validada: su SHA-256 debe ser",
        f"   `{dll_sha}`.",
        "",
        f"O hazlo todo de una vez con `python tools/actualizar_libmpv.py --tag {release.tag} --apply`,",
        "que además la prueba y regenera sus avisos de licencia.",
        README_END,
    ])


def replace_block(path: Path, begin: str, end: str, block: str) -> None:
    """Sustituye lo que hay entre las marcas, conservando los finales de línea del fichero."""
    raw = path.read_bytes()
    crlf = b"\r\n" in raw
    text = raw.decode("utf-8").replace("\r\n", "\n")
    start, stop = text.find(begin), text.find(end)
    if start < 0 or stop < 0:
        raise SystemExit(f"{path.name} no tiene las marcas de la sección generada ({begin!r})")
    stop += len(end)
    if text[stop:stop + 1] == "\n" and block.endswith("\n"):
        stop += 1
    text = text[:start] + block + text[stop:]
    path.write_bytes((text.replace("\n", "\r\n") if crlf else text).encode("utf-8"))


# ---- Principal ----
def main() -> None:
    parser = argparse.ArgumentParser(description="Actualiza vendor/libmpv-2.dll y regenera sus avisos de licencia.")
    parser.add_argument("--tag", default="latest", help="etiqueta de la release de shinchiro (por defecto, la última)")
    parser.add_argument("--apply", action="store_true", help="instalar la DLL y escribir los avisos y el README")
    parser.add_argument("--work-dir", type=Path,
                        default=Path(os.environ.get("TEMP", ".")) / "BibliotecaAnime-libmpv",
                        help="carpeta de trabajo (descargas y clones, reutilizables)")
    args = parser.parse_args()
    work: Path = args.work_dir
    work.mkdir(parents=True, exist_ok=True)

    log(f"1/6 Release {args.tag}")
    release = fetch_release(args.tag)
    log(f"    {release.tag} · {release.dev_asset} · receta {release.recipe_commit[:12]} · corte {release.cutoff:%Y-%m-%d %H:%M} UTC")

    log("2/6 DLL")
    archive = download(release.dev_url, work / "releases" / release.dev_asset, release.dev_size)
    dll = extract_dll(archive, work / "dll" / release.tag)
    dll_sha = sha256_of(dll)
    log(f"    sha256 {dll_sha}")

    log("3/6 Prueba de humo con python-mpv")
    versions = smoke_test(dll)
    log(f"    {versions}")
    if not (versions.get("video") and versions.get("audio")):
        raise SystemExit("La DLL carga pero no reproduce: no se instala")
    if release.mpv_hash[:9] not in versions["mpv_version"]:
        raise SystemExit(f"La DLL dice {versions['mpv_version']}, y el paquete es de {release.mpv_hash}")

    log("4/6 Receta")
    recipe = Recipe(release.recipe_commit)
    targets, _ = recipe.targets()
    needed = closure(targets, "mpv")
    log(f"    mpv necesita {len(needed)} objetivos")

    log("5/6 Versiones y licencias")
    known = {"mpv": release.mpv_hash, "ffmpeg": release.ffmpeg_hash}
    sources: List[Source] = []
    for name in needed + ["mingw-w64"]:
        target = targets.get(name)
        if target is None or not (target.git_repository or target.url):
            continue
        log(f"    {name}")
        try:
            source = resolve_git(target, release, work, known.get(name)) if target.git_repository \
                else resolve_url(target, work)
        except Exception as exc:
            source = Source(name=name, kind="?", origin=target.git_repository or target.url, ref="?",
                            exact=False, note=f"⚠ no se pudo resolver: {exc}")
        if name == "mingw-w64":
            source.note += "; de él salen la CRT y winpthreads, que van enlazadas"
        if name in SOURCE_NOTES:
            source.note += f"; {SOURCE_NOTES[name]}"
        if name == "subrandr" and source.kind == "git":
            source.children += resolve_crates(work / "repos" / f"{_safe(name)}.git", source.ref, "subrandr", work)
        sources.append(source)
    if "subrandr" in needed:
        sources.append(rust_std(release))

    report = {
        "tag": release.tag, "asset": release.dev_asset, "sha256": dll_sha, "versions": versions,
        "recipe_commit": release.recipe_commit, "cutoff": release.cutoff.isoformat(),
        "sources": [{"name": s.name, "kind": s.kind, "origin": s.origin, "ref": s.ref, "exact": s.exact,
                     "note": s.note, "licenses": [n for n, _ in s.licenses],
                     "children": [c.name for c in s.children]} for s in sources],
    }
    notices_block = render_notices(release, dll_sha, versions, sources)
    readme_block = render_readme(release, dll_sha)
    out_dir = work / "salida" / release.tag
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "informe.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "libmpv-notices.txt").write_text(notices_block, encoding="utf-8")
    (out_dir / "readme-paso4.md").write_text(readme_block, encoding="utf-8")

    problems = [s for s in sources if s.kind == "?" or "NO coincide" in s.note
                or (not s.licenses and s.name not in SOURCE_NOTES)]
    problems += [c for s in sources for c in s.children if "⚠" in c.note]
    log(f"6/6 Resultado en {out_dir}")
    log(f"    {len(sources)} fuentes ({sum(1 for s in sources if not s.exact)} reconstruidas), "
        f"{sum(len(s.children) for s in sources)} submódulos o crates")
    for source in problems:
        log(f"    ⚠ revisar {source.name}: {source.note or 'sin fichero de licencia en la raíz'}")

    if not args.apply:
        log("En seco: no se ha tocado el repositorio. Repite con --apply para instalarla.")
        return
    if VENDOR_DLL.exists() and sha256_of(VENDOR_DLL) != dll_sha:
        backup = work / "backup" / f"libmpv-2.{sha256_of(VENDOR_DLL)[:12]}.dll"
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(VENDOR_DLL, backup)
        log(f"    DLL anterior guardada en {backup}")
    VENDOR_DLL.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(dll, VENDOR_DLL)
    replace_block(NOTICES, NOTICES_BEGIN, NOTICES_END, notices_block)
    replace_block(README, README_BEGIN, README_END, readme_block)
    log("Aplicado: vendor/libmpv-2.dll, THIRD-PARTY-NOTICES.txt y README.md (paso 4).")
    log("Falta: probar la app (python src/app.py), recompilar el .exe y repasar la documentación de .claude/.")


if __name__ == "__main__":
    main()
