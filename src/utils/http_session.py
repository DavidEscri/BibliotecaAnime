"""
Una requests.Session por hilo, para reutilizar la conexión TCP + TLS entre las
peticiones de un mismo hilo. requests no garantiza que una Session sea segura
entre hilos, así que ninguna se comparte.
"""
__author__ = "Jose David Escribano Orts"
__subsystem__ = "utils"
__module__ = "http_session.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import threading

from http.cookiejar import DefaultCookiePolicy

import requests

_local = threading.local()


def thread_session() -> requests.Session:
    """Devuelve la sesión HTTP del hilo que llama, creándola la primera vez.

    No guarda cookies: cada petición se comporta como un requests.get suelto y
    lo único que se aprovecha de la anterior es la conexión.

    :return: Sesión exclusiva del hilo actual; muere con él.
    """
    session = getattr(_local, "session", None)
    if session is None:
        session = requests.Session()
        session.cookies.set_policy(DefaultCookiePolicy(allowed_domains=[]))
        _local.session = session
    return session
