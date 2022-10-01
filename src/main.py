import sys
from typing import List

from aqt import mw
from aqt.browser.browser import Browser
from aqt.editor import Editor
from aqt.gui_hooks import browser_menus_did_init, editor_did_init_buttons
from aqt.operations import CollectionOp
from aqt.qt import *
from aqt.utils import showText, showWarning, tooltip

from . import consts

sys.path.append(str(consts.ADDON_DIR / "vendor"))


# pylint: disable=wrong-import-position
from . import popup
from .gui.importer import ImportDialog
from .gui.main import ZIMFetcherDialog
from .gui.settings import SettingsDialog

PACKAGE_NAME = mw.addonManager.addonFromModule(__name__)


def on_bulk_updated_notes(
    browser: Browser, errors: List[str], updated_count: int
) -> None:
    if updated_count:
        tooltip(f"Updated {updated_count} note(s).", period=5000, parent=browser)
    if len(errors) == 1:
        showWarning(errors[0], parent=browser, title=consts.ADDON_NAME)
    elif errors:
        msg = ""
        msg += " The following issues happened during the process:\n"
        msg += "\n".join(errors)
        showText(msg, parent=browser, title=consts.ADDON_NAME)


def on_browser_action_triggered(browser: Browser) -> None:
    notes = [browser.mw.col.get_note(nid) for nid in browser.selected_notes()]
    dialog = ZIMFetcherDialog(browser.mw, browser, notes)
    if dialog.exec():
        updated_notes = dialog.updated_notes
        errors = dialog.errors
        CollectionOp(
            parent=browser,
            op=lambda col: col.update_notes(updated_notes),
        ).success(
            lambda out: on_bulk_updated_notes(browser, errors, len(updated_notes)),
        ).run_in_background()


def on_browser_menus_did_init(browser: Browser) -> None:
    config = mw.addonManager.getConfig(__name__)
    shortcut = config["browser_shortcut"]
    action = QAction("Bulk-define from ZIM file", browser)
    action.setShortcut(shortcut)
    qconnect(action.triggered, lambda: on_browser_action_triggered(browser))
    browser.form.menuEdit.addSeparator()
    browser.form.menuEdit.addAction(action)


def on_editor_button_clicked(editor: Editor) -> None:
    dialog = ZIMFetcherDialog(editor.mw, editor.parentWindow, [editor.note])
    if dialog.exec():
        if dialog.errors:
            showWarning(
                "\n".join(dialog.errors),
                parent=editor.parentWindow,
                title=consts.ADDON_NAME,
            )
        editor.loadNoteKeepingFocus()


def on_editor_did_init_buttons(buttons: List[str], editor: Editor) -> None:
    config = mw.addonManager.getConfig(__name__)
    shortcut = QKeySequence(config["editor_shortcut"]).toString(
        QKeySequence.SequenceFormat.NativeText
    )
    button = editor.addButton(
        icon=os.path.join(consts.ICONS_DIR, "logo.svg"),
        cmd="zim",
        tip=f"{consts.ADDON_NAME} ({shortcut})" if shortcut else consts.ADDON_NAME,
        func=on_editor_button_clicked,
        keys=shortcut,
    )
    buttons.append(button)


def on_import_dictionary() -> None:
    dialog = ImportDialog(mw)
    dialog.exec()
    if dialog.errors:
        showText(
            "The following errors happened during the process:\n"
            + "\n".join(dialog.errors)
        )


def on_settings() -> None:
    dialog = SettingsDialog(mw)
    dialog.exec()


def add_menu() -> None:
    menu = QMenu(consts.ADDON_NAME, mw)
    action = QAction(menu)
    action.setText("Import a file")
    qconnect(action.triggered, on_import_dictionary)
    menu.addAction(action)

    action = QAction(menu)
    action.setText("Settings")
    qconnect(action.triggered, on_settings)
    menu.addAction(action)

    mw.form.menuTools.addMenu(menu)


browser_menus_did_init.append(on_browser_menus_did_init)
editor_did_init_buttons.append(on_editor_did_init_buttons)
add_menu()
popup.init()
