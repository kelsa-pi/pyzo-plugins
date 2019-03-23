# -*- coding: utf-8 -*-

import pyzo
from pyzo.util.qt import QtCore, QtGui, QtWidgets
from pyzo import translate
from pyzo.core.menu import RunMenu
from pyzo.core.menu import AdvancedSettings
from pyzo.core.assistant import PyzoAssistant

tool_name = translate("pyzoToolbar", "Toolbar")
tool_summary = "Show the toolbar."


def addItem(target, text, icon=None, callback=None, value=None):
    """
    Add an item to the toolbar. If callback is given and not None,
    connect triggered signal to the callback. If value is None or not
    given, callback is called without parameteres, otherwise it is called
    with value as parameter
    """

    # Add action
    a = target.addAction(icon, text)

    # Connect the menu item to its callback
    if callback:
        if value is not None:
            a.triggered.connect(lambda b=None, v=value: callback(v))
        else:
            a.triggered.connect(lambda b=None: callback())

    return a


def printify():
    """ Insert selected or clipboard text variable as print('VARIABLE: ' + str(varible)).

    Note:
    Print function are a very convenient way to debug your python code as it executes, BUT
    should be used sparingly for debugging! Use logging module instead.
    """
    import pyzo

    # Get editor
    editor = pyzo.editors.getCurrentEditor()
    # Get cursor
    cursor = editor.textCursor()
    # Get selected text
    selection = cursor.selectedText()
    if selection == "":
        # Get clipboard text
        selection = pyzo.MyApp.instance().clipboard().text()
    # Update the selection
    newText = "print('{}: ' + str({}))".format(selection.upper(), selection)
    cursor.insertText(newText)


class PyzoToolbar(QtWidgets.QWidget):
    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)
        # Make sure there is a configuration entry for this tool
        # The pyzo tool manager makes sure that there is an entry in
        # config.tools before the tool is instantiated.
        toolId = self.__class__.__name__.lower()
        self._config = pyzo.config.tools[toolId]

        # Add config options
        if not hasattr(self._config, "toolbarSize"):
            self._config.toolbarSize = 35
        # if not hasattr(self._config, 'bgNames'):
        #     self._config.bgNames = ['Default', 'Alice Blue', 'Antique White', 'Light Yellow', 'Snow', 'White Smoke']
        # if not hasattr(self._config, 'bgColors'):
        #     self._config.bgColors = ['#fff', '#F0F8FF', '#FAEBD7', '#FFFFE0', '#FFFAFA', '#F5F5F5']
        # if not hasattr(self._config, 'defaultBgColor'):
        #     self._config.defaultBgColor = 'Default'

        # Create toolbar
        self.createToolbar()

    def createToolbar(self):
        self.toolbar = MainToolbar()
        pyzo.main.addToolBar(self.toolbar)
        self.toolbar.toggleViewAction().setChecked(True)
        self.toolbar.setVisible(True)


class MainToolbar(QtWidgets.QToolBar):
    """Main Toolbar"""

    def __init__(self):
        QtWidgets.QToolBar.__init__(self, "MainToolBar", parent=None)

        self.setObjectName("MainToolBar")
        self.setMovable(True)
        self.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)

        TOOLBARSIZE = pyzo.config.tools.pyzotoolbar.toolbarSize
        self.setMinimumSize(TOOLBARSIZE, TOOLBARSIZE)
        self.setIconSize(QtCore.QSize(TOOLBARSIZE, TOOLBARSIZE))

        # ---------- Toolbars sections ----------

        # File menu
        addItem(self, "New", pyzo.icons.page_add, pyzo.editors.newFile, None)

        addItem(
            self, "Open", pyzo.icons.folder_page, pyzo.editors.openFile, None
        )

        addItem(self, "Save", pyzo.icons.disk, pyzo.editors.saveFile, None)

        addItem(
            self,
            "Save all",
            pyzo.icons.disk_multiple,
            pyzo.editors.saveAllFiles,
            None,
        )

        # Edit menu
        addItem(
            self, "Undo", pyzo.icons.arrow_undo, self.itemActionCallback, "undo"
        )

        addItem(
            self, "Redo", pyzo.icons.arrow_redo, self.itemActionCallback, "redo"
        )

        self.addSeparator()

        addItem(self, "Cut", pyzo.icons.cut, self.itemActionCallback, "cut")

        addItem(
            self,
            "Copy",
            pyzo.icons.page_white_copy,
            self.itemActionCallback,
            "copy",
        )

        addItem(
            self,
            "Paste",
            pyzo.icons.paste_plain,
            self.itemActionCallback,
            "paste",
        )

        self.addSeparator()

        addItem(
            self,
            "Indent",
            pyzo.icons.text_indent,
            self.itemActionCallback,
            "indentSelection",
        )

        addItem(
            self,
            "Dedent",
            pyzo.icons.text_indent_remove,
            self.itemActionCallback,
            "dedentSelection",
        )

        self.addSeparator()

        addItem(
            self,
            "Comment",
            pyzo.icons.comment_add,
            self.itemActionCallback,
            "commentCode",
        )

        addItem(
            self,
            "Uncomment",
            pyzo.icons.comment_delete,
            self.itemActionCallback,
            "uncommentCode",
        )

        self.addSeparator()

        addItem(
            self,
            "Find or replace",
            pyzo.icons.find,
            pyzo.editors._findReplace.startFind,
            None,
        )

        self.addSeparator()

        # Run menu
        addItem(
            self,
            "Run file as script",
            pyzo.icons.run_file_script,
            RunMenu(name="Run")._runFile,
            (True, False),
        )

        addItem(
            self,
            "Run main file as script",
            pyzo.icons.run_mainfile_script,
            RunMenu(name="Run")._runFile,
            (True, False),
        )

        self.addSeparator()

        # Debug
        addItem(
            self,
            "Insert selected or clipboard text as print('TEXT: ' + text)",
            pyzo.icons.bug,
            printify,
            None,
        )

        self.addSeparator()

        addItem(
            self,
            "Advanced settings",
            pyzo.icons.cog,
            lambda: AdvancedSettings().exec_(),
            None,
        )

        addItem(
            self,
            "Edit shell configurations",
            pyzo.icons.application_wrench,
            self.editShellConfig,
            None,
        )

        addItem(
            self,
            "Local documentation",
            pyzo.icons.help,
            PyzoAssistant().show,
            None,
        )

        # Close toolbar
        self.addSeparator()
        self.addSeparator()
        # TODO:  Tools menu action on closing don't work,
        addItem(
            self,
            "Close toolbar",
            pyzo.icons.cross,
            lambda: self.closeToolbar(),
            None,
        )

        self.addSeparator()
        self.addSeparator()

    def itemActionCallback(self, action):
        widget = QtWidgets.qApp.focusWidget()
        if hasattr(widget, action):
            getattr(widget, action)()

    def editShellConfig(self):
        """ Edit, add and remove configurations for the shells. """
        from pyzo.core.shellInfoDialog import ShellInfoDialog

        d = ShellInfoDialog()
        d.exec_()

    def closeToolbar(self):
        pyzo.main.removeToolBar(self)
        self.toggleViewAction().setChecked(False)
        self.setVisible(False)
        pyzo.main.update()
        pyzo.toolManager.closeTool("pyzotoolbar")
        pyzo.toolManager.onToolClose("pyzotoolbar")
