# -*- coding: utf-8 -*-
import ast
import os
import pathlib

from os.path import abspath, dirname, join
from inspect import getsourcefile
from json import load, loads, dump

import pyzo
from pyzo.util.qt import QtCore, QtGui, QtWidgets
from pyzo import translate

tool_name = translate("ExternalCommands", "External Commands")
tool_summary = (
    "Execute an external command that is not included in the Pyzo IDE."
)

DIALOG_INPUT = []
PATH = abspath(getsourcefile(lambda: 0))
DIR = dirname(PATH)
RESULTFILE = "commands.txt"


def saveCommands(commands, dir, filename):
    file_path = join(dir, filename)
    with open(file_path, "w", encoding="utf-8") as outfile:
        dump(commands, outfile, indent=4)


def loadCommands(dir, filename):
    file_path = join(dir, filename)
    with open(file_path, "r", encoding="utf-8") as data_file:
        data = loads(data_file.read())
        return data


def commandList(commands=[]):
    l = DIALOG_INPUT
    if commands:
        l.extend(commands)
    else:
        del l[:]
    return l


class PyzoExternalCommands(QtWidgets.QWidget):
    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)

        # Make sure there is a configuration entry for this tool
        # The pyzo tool manager makes sure that there is an entry in
        # config.tools before the tool is instantiated.
        toolId = self.__class__.__name__.lower()  # coding=utf-8

        # self._config = pyzo.config.tools[toolId]
        # if not hasattr(self._config, 'showTypes'):
        #     self._config.showTypes = ['class', 'def', 'cell', 'todo']
        # if not hasattr(self._config, 'level'):
        #     self._config.level = 2

        data = {"Firefox search": {"command": "firefox -search %s"}}

        self.commands_file = os.path.join(DIR, RESULTFILE)
        if not os.path.exists(self.commands_file):
            saveCommands(data, DIR, RESULTFILE)
        # Load commands
        self.commands_all = loadCommands(DIR, RESULTFILE)
        # variable
        self.file_browser = None
        self.logger = pyzo.toolManager.getTool("pyzologger")
        self.process = None
        self.qba = pyzo.QtCore.QByteArray()
        self.locale_codec = pyzo.QtCore.QTextCodec.codecForLocale()

        self.name = ""  # nraw name string
        self.command = ""  # raw command string
        self.command_process = ""  # command in QProcess
        self.process_output = ""  #

        # Create button for add external command
        self._add = QtWidgets.QToolButton(self)
        self._add.setIcon(pyzo.icons.add)
        self._add.setToolTip("Add External Command")
        # event
        self._add.clicked.connect(self.addCommand)

        # Create button for edit external command
        self._edit = QtWidgets.QToolButton(self)
        self._edit.setIcon(pyzo.icons.application_edit)
        self._edit.setToolTip("Edit External Command")
        # event
        self._edit.clicked.connect(self.editCommand)

        # Create button for remove external command
        self._remove = QtWidgets.QToolButton(self)
        self._remove.setIcon(pyzo.icons.delete)
        self._remove.setToolTip("Remove External Command")
        # event
        self._remove.clicked.connect(self.removeCommand)

        # Create button to kill process
        self._terminate = QtWidgets.QToolButton(self)
        self._terminate.setIcon(pyzo.icons.cross)
        self._terminate.setToolTip("Terminate")
        self._terminate.setEnabled(False)
        # event
        self._terminate.clicked.connect(self.terminateCommand)

        # Create button for execute command
        self._run = QtWidgets.QToolButton(self)
        self._run.setIcon(pyzo.icons.application_go)
        self._run.setToolTip("Execute command")
        # event
        self._run.clicked.connect(self.start)

        # Create tree
        self._tree = QtWidgets.QTreeWidget(self)
        self._tree.setColumnCount(1)
        self._tree.setHeaderLabels(["Name"])
        self._tree.setColumnWidth(0, 200)
        self._tree.setHeaderHidden(False)
        self._tree.setSortingEnabled(True)
        self._tree.sortItems(1, QtCore.Qt.AscendingOrder)
        self._tree.setRootIsDecorated(False)
        # set widget stye
        background = self.getThemeItem(item="editor.text")
        textcolor = self.getThemeItem(item="syntax.identifier")
        styleKeys = ["background-color", "color"]
        styleValues = [background["back"], textcolor["fore"]]
        self.setWidgetStyleSheet(self._tree, styleKeys, styleValues)

        # self.setWidgetStyleSheet(self._tree)
        # event
        self._tree.itemDoubleClicked.connect(self.start)

        # Output message
        self._output = QtWidgets.QTextBrowser(self)
        initText = ""
        self._output.setText(initText)
        # style
        self.setWidgetStyleSheet(self._output, styleKeys, styleValues)

        # Empty label
        self._empty = QtWidgets.QLabel(self)

        # Create two sizers
        self._sizer1 = QtWidgets.QVBoxLayout(self)
        self._sizer2 = QtWidgets.QHBoxLayout()
        #
        self._sizer1.setSpacing(2)
        self._sizer1.setContentsMargins(0, 0, 0, 0)

        # Set layout
        self._sizer1.addLayout(self._sizer2, 0)
        self._sizer1.addWidget(self._tree, 1)
        self._sizer1.addWidget(self._output, 1)
        #
        self._sizer2.addWidget(self._add, 0)
        self._sizer2.addWidget(self._edit, 0)
        self._sizer2.addWidget(self._remove, 0)
        self._sizer2.addWidget(self._terminate, 0)

        self._sizer2.addWidget(self._empty, 1)
        self._sizer2.addWidget(self._run, 0)
        #
        self.setLayout(self._sizer1)

        self.fillTree(self.commands_all)

    # Style
    def getThemeItem(self, item="editor.text"):
        theme = pyzo.themes[pyzo.config.settings.theme.lower()]["data"]
        for k, v in theme.items():
            key = k
            val_dict = {}
            if key == item:
                for x in v.split(","):
                    item = x.split(":")
                    item_key = item[0].strip()
                    item_value = item[1].strip()
                    val_dict[item_key] = item_value
                break
        return val_dict

    def setWidgetStyleSheet(self, widget, keys, values):
        wdg = str(type(widget))
        wdg = wdg.replace("<class 'PyQt5.QtWidgets.", "").replace("'>", "")
        t = ""
        for n in range(len(keys)):
            t = t + keys[n] + ":" + values[n] + ";"
        ss = wdg + "{" + t + "}"
        widget.setStyleSheet(ss)
        widget.setAutoFillBackground(True)

    def setWidgetTextStyle(self, widget):
        theme = pyzo.themes[pyzo.config.settings.theme.lower()]["data"]
        background = self.getThemeItem(item="editor.text")["back"]
        textcolor = self.getThemeItem(item="editor.text")["fore"]
        wdg = str(type(widget))
        wdg = wdg.replace("<class 'PyQt5.QtWidgets.", "").replace("'>", "")
        ss = wdg + "{background-color:%s; color:%s;}" % (background, textcolor)
        widget.setStyleSheet(ss)
        widget.setAutoFillBackground(True)

    # ---------

    def terminateCommand(self):
        print("TERMINATE: ")
        self.process.terminate()

    def fillTree(self, data):
        self._tree.clear()
        for key in sorted(data.keys()):
            QtWidgets.QTreeWidgetItem(self._tree, [key])

    def addCommand(self):
        commandList()
        dialog = InputDialog(self)
        dialog.setWindowTitle(translate("menu dialog", "Add command"))
        if dialog.exec_():
            if dialog._name.text() == "":
                pass
            else:
                data = loadCommands(DIR, RESULTFILE)
                data[dialog._name.text()] = {}
                data[dialog._name.text()]["command"] = dialog._command.text()
                saveCommands(data, DIR, RESULTFILE)
                self.fillTree(data)
            dialog.close()

    def editCommand(self):

        data = loadCommands(DIR, RESULTFILE)
        name = self._tree.currentItem().text(0)
        p = data[name]["command"]

        dialog = InputDialog(self)
        dialog.setWindowTitle(translate("menu dialog", "Edit command"))
        dialog._name.setText(name)
        dialog._command.setText(p)

        if dialog.exec_():
            if dialog._name.text() == "":
                pass
            else:
                data.pop(name)
                data[dialog._name.text()] = {}
                data[dialog._name.text()]["command"] = dialog._command.text()
                saveCommands(data, DIR, RESULTFILE)
                self.fillTree(data)
            dialog.close()
        loadCommands(DIR, RESULTFILE)

    def removeCommand(self):
        data = loadCommands(DIR, RESULTFILE)
        name = self._tree.currentItem().text(0)

        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Question)
        msg.setWindowTitle("Remove command")
        msg.setText("Do you really want to delete: '{}' command?".format(name))
        # msg.setInformativeText("This is additional information")
        msg.setStandardButtons(
            QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel
        )

        returnValue = msg.exec()
        if returnValue == QtWidgets.QMessageBox.Ok:
            data.pop(name)
            saveCommands(data, DIR, RESULTFILE)
            self.fillTree(data)
        else:
            pass
            print("No clicked.")

    def replacePlaceholder(self, text=""):
        self.editor = pyzo.editors.getCurrentEditor()
        self.cursor = self.editor.textCursor()
        error = ""

        path = pathlib.PurePath(self.editor.filename)
        selection = self.cursor.selectedText()

        for placeholder in ["%f", "%d", "%e", "%n", "%s", "%b"]:

            # Gets replaced by the local filepath to the active document
            if placeholder == "%f":
                text = text.replace("%f", str(path))

            # Gets replaced by the path to the directory of the active document
            if placeholder == "%d":
                text = text.replace("%d", str(path.parent))

            # Gets replaced by the name of the active document, including its extension
            if placeholder == "%e":
                text = text.replace("%e", path.name)

            # Gets replaced by the name of the active document without its extension
            if placeholder == "%n":
                a = path.name.replace(path.suffix, "")
                text = text.replace("%n", a)

            # Gets replaced by the selected text in the active document
            if placeholder == "%s":
                if selection:
                    text = text.replace("%s", selection)
                # else:
                #     error = "No selected text in the active document"
                #     break
            # Gets replaced by the selected text in the File Browser
            self.file_browser = pyzo.toolManager.getTool("pyzofilebrowser")
            if placeholder == "%b":
                if self.file_browser:
                    browser = self.file_browser.children()[0]
                    browser_tree = browser.children()[2]
                    path = None
                    try:
                        path = browser_tree.selectedItems()[0].path()
                        if path:
                            text = text.replace("%b", path)
                    except Exception as e:
                        error = "No selected file or dir in the File Browser"
                        break
                else:
                    error = "File Browser is not open"
                    break
        return text, error

    def start(self):
        """ start()
        Start command
        """
        self.name = ""
        self.command = ""
        self.terminal = ""
        self.command_process = ""
        self.process_output = ""
        self._output.setText("")
        self.error = ""
        self.commands_all = loadCommands(DIR, RESULTFILE)

        self.name = self._tree.currentItem().text(0)
        self.command = self.commands_all[self.name]["command"]
        self.command_process, self.error = self.replacePlaceholder(self.command)

        if self.error:

            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setWindowTitle("Error Message")
            msg.setText(
                "There is an error in the command: {}".format(self.name)
            )
            msg.setInformativeText(self.error)
            msg.setStandardButtons(QtWidgets.QMessageBox.Ok)

            returnValue = msg.exec()
            if returnValue == QtWidgets.QMessageBox.Ok:
                return 0

        self.process = pyzo.QtCore.QProcess(self)
        self.process.readyReadStandardOutput.connect(self.stdoutReady)
        self.process.readyReadStandardError.connect(self.stderrReady)
        self.process.started.connect(self.started)
        self.process.finished.connect(self.finished)

        self.process.start(self.command_process)
        self._terminate.setEnabled(True)

    def appendText(self, text):
        cursor = self._output.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(text)

    def started(self):
        output_text = "Command: {}\nRuner: {}\n----------\n".format(
            self.command, self.command_process
        )
        self.appendText(output_text)

    def finished(self):
        output_text = "\n*** Exit Status: {} ***".format(
            self.process.exitStatus()
        )
        self.appendText(output_text)
        self._terminate.setEnabled(False)

    def stdoutReady(self):
        self.qba = self.process.readAllStandardOutput()
        output_text = self.locale_codec.toUnicode(self.qba.data())
        self.appendText(output_text)

    def stderrReady(self):
        self.qba = self.process.readAllStandardError()
        output_text = self.locale_codec.toUnicode(self.qba.data())
        self.appendText(output_text)


class InputDialog(QtWidgets.QDialog):
    """Advanced settings
    The Advanced settings dialog contains configuration settings for Pyzo and plugins.
    Click on an item, to edit settings.
    """

    def __init__(self, *args):

        QtWidgets.QDialog.__init__(self, *args)

        self.input = DIALOG_INPUT

        self.placeholders = """
        Placeholders:\n
        %b \n                Gets replaced by the selected text in the File Browser
        %d \n                Gets replaced by the path to the directory of the active document
        %e \n                Gets replaced by the name of the active document, including its extension
        %f \n                Gets replaced by the local filepath to the active document
        %n \n                Gets replaced by the name of the active document without its extension
        %s \n                Gets replaced by the selected text in the active document
        """
        # Set size
        size = 650, 190
        offset = 0
        size2 = size[0], size[1] + offset
        self.resize(*size2)
        self.setMaximumSize(*size2)
        self.setMinimumSize(*size2)
        self.item = ""

        note = "NOTE: It is your responsibility to prevent running hazardous commands"
        self._note_label = QtWidgets.QLabel(self)
        self._note_label.setText(note)

        layout_1 = QtWidgets.QHBoxLayout()
        layout_1.addWidget(self._note_label, 0)
        # Name
        self._name_label = QtWidgets.QLabel(self)
        self._name_label.setText("Name")
        self._name = QtWidgets.QLineEdit(self)
        self._name.setReadOnly(False)
        # Command
        self._command_label = QtWidgets.QLabel(self)
        self._command_label.setText("Command")
        self._command = QtWidgets.QLineEdit(self)
        self._command.setReadOnly(False)
        self._command.setToolTip(str(self.placeholders))
        # Grid
        self.horizontalGroupBox = QtWidgets.QGroupBox()
        layout_grid = QtWidgets.QGridLayout()
        layout_grid.setColumnStretch(1, 2)
        layout_grid.addWidget(self._name_label, 0, 0)
        layout_grid.addWidget(self._name, 0, 1)
        layout_grid.addWidget(self._command_label, 1, 0)
        layout_grid.addWidget(self._command, 1, 1)
        self.horizontalGroupBox.setLayout(layout_grid)

        self.button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout_2 = QtWidgets.QHBoxLayout()
        layout_2.addWidget(self.button_box, 0)
        # Layouts
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.addLayout(layout_1, 0)
        mainLayout.addWidget(self.horizontalGroupBox)
        mainLayout.addLayout(layout_2, 0)
        self.setLayout(mainLayout)
