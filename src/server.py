from __future__ import annotations

import threading
from http import HTTPStatus

import flask
from flask import Flask, Response
from waitress.server import create_server as create_waitress_server
from zimply_core.zim_core import ZIMClient

from .consts import USER_FILES


class ZIMServer(threading.Thread):

    _ready = threading.Event()
    daemon = True

    def __init__(self, app: Flask, dictionary: str) -> None:
        super().__init__()
        self.app = app
        self.is_shutdown = False
        zim_path = next((USER_FILES / dictionary).glob("*.zim"), None)
        if not zim_path:
            raise Exception(f"No ZIM file was found in {str(dictionary)}")
        self.client = ZIMClient(
            str(zim_path),
            encoding="utf-8",
            auto_delete=True,
            # FIXME: enable search after fixing threading issues
            enable_search=False,
        )

    def run(self) -> None:
        try:
            self.server = create_waitress_server(
                self.app,
                host="127.0.0.1",
                # port="8000",
                port="0",
                clear_untrusted_proxy_headers=True,
                threads=1,
            )
            self._ready.set()
            self.server.run()

        except Exception:
            if not self.is_shutdown:
                raise

    # Copied from mediasrv.py in Anki
    # TODO: uncomment if actually necessary
    # def shutdown(self) -> None:
    #     self.is_shutdown = True
    #     sockets = list(self.server._map.values())  # type: ignore
    #     for socket in sockets:
    #         socket.handle_close()
    #     # https://github.com/Pylons/webtest/blob/4b8a3ebf984185ff4fefb31b4d0cf82682e1fcf7/webtest/http.py#L93-L104
    #     self.server.task_dispatcher.shutdown()

    @property
    def port(self) -> int:
        self._ready.wait()
        return int(self.server.effective_port)  # type: ignore

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}/"


def create_server(dictionary: str) -> ZIMServer:
    app = Flask(__name__)

    zim_server = ZIMServer(app, dictionary)

    @app.route("/")
    def index() -> Response:
        article = zim_server.client.main_page
        response = flask.make_response(article.data, HTTPStatus.OK)
        response.headers["Content-Type"] = article.mimetype
        return response

    @app.route("/<path:path>")
    def handle_request(path: str) -> Response:
        try:
            article = zim_server.client.get_article(path)
        except KeyError:
            *_, word = path.rsplit("/", maxsplit=1)
            results = zim_server.client.search(word, 0, -1)
            if results:
                article = zim_server.client.get_article(results[0].url)
            else:
                article = None
        if article:
            response = flask.make_response(article.data, HTTPStatus.OK)
            response.headers["Content-Type"] = article.mimetype
            return response
        return flask.make_response("Requested resource not found", HTTPStatus.NOT_FOUND)

    return zim_server


if __name__ == "__main__":
    server = create_server("wiktionary_el_all_maxi_2022-07")
    server.start()
    server.join()
