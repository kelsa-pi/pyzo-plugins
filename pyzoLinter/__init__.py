# -*- coding: utf-8 -*-

# Static code analysis tool - pylint

import os
import sys

import pyzo
from pyzo.util.qt import QtCore, QtGui, QtWidgets
from pyzo import translate

tool_name = translate("pyzoLinter", "Linter")
tool_summary = "Shows the structure of your source code."

ALL = "All Issues"
CONVENTION = "Convention"
REFACTOR = "Refactor"
WARNING = "Warning"
ERROR = "Error"


class PyzoLinter(QtWidgets.QWidget):
    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)

        # Make sure there is a configuration entry for this tool
        # The pyzo tool manager makes sure that there is an entry in
        # config.tools before the tool is instantiated.

        toolId = self.__class__.__name__.lower()
        self._config = pyzo.config.tools[toolId]
        if not hasattr(self._config, "fontSize"):
            if sys.platform == "darwin":
                self._config.fontSize = 12
            else:
                self._config.fontSize = 10

        # Style
        theme = pyzo.themes[pyzo.config.settings.theme.lower()]["data"]
        background_style = theme["editor.text"].split(",")
        background = background_style[1].split(":")[1]
        textcolor_style = theme["syntax.identifier"].split(",")
        textcolor = textcolor_style[0].split(":")[1]

        # Keep track of linter output
        self.output = ""

        # Folder for linter output file
        self.output_folder = os.path.join(
            pyzo.appDataDir, "tools", "pyzoLinter"
        )

        self.process = None
        self.locale_codec = pyzo.QtCore.QTextCodec.codecForLocale()

        self.cur_dir_path = ""

        # Create button for parsing scope
        self._reload = QtWidgets.QToolButton(self)
        self._reload.setIcon(pyzo.icons.arrow_refresh)
        self._reload.setToolTip("Parse")
        # event
        self._reload.clicked.connect(self.start)

        # Create combo box Scope
        scope_list = ["Current document", "Current document directory"]
        self._scope = QtWidgets.QComboBox(self)
        self._scope.setToolTip("Get by index")
        self._scope.addItems(scope_list)

        # Create font options menu
        self._font_options = QtWidgets.QToolButton(self)
        self._font_options.setIcon(pyzo.icons.wrench)
        self._font_options.setIconSize(QtCore.QSize(16, 16))
        self._font_options.setPopupMode(self._font_options.InstantPopup)
        self._font_options.setToolButtonStyle(
            QtCore.Qt.ToolButtonTextBesideIcon
        )
        self._font_options._menu = QtWidgets.QMenu()
        self._font_options.setMenu(self._font_options._menu)
        self.onFontOptionsPress()  # create menu now
        # event
        self._font_options.pressed.connect(self.onFontOptionsPress)
        self._font_options._menu.triggered.connect(
            self.onFontOptionMenuTiggered
        )

        # Create button for opening output file in the editor
        self._open_file = QtWidgets.QToolButton(self)
        self._open_file.setIcon(pyzo.icons.page_white_text)
        self._open_file.setIconSize(QtCore.QSize(16, 16))
        self._open_file.setStyleSheet(
            "QToolButton { border: none; padding: 0px; }"
        )
        self._open_file.setToolTip("Open output file in the editor")
        # event
        self._open_file.clicked.connect(self.onOpenOutputFile)

        # Ratings label
        self._ratings = QtWidgets.QLabel(self)
        self._ratings.setText("")
        self._ratings.setAlignment(QtCore.Qt.AlignCenter)
        ss = "QLabel{color: black;background-color: #FFFFE0;font : bold;}"
        self._ratings.setStyleSheet(ss)

        # Create radio box All
        self._all = QtWidgets.QRadioButton(self)
        self._all.setText(ALL)
        self._all.setChecked(True)
        self._all.setToolTip(ALL)

        # Create radio box Convention
        self._convention = QtWidgets.QRadioButton(self)
        self._convention.setText(CONVENTION)
        self._convention.setToolTip(CONVENTION)

        # Create radio box Refactor
        self._refactor = QtWidgets.QRadioButton(self)
        self._refactor.setText(REFACTOR)
        self._refactor.setToolTip(REFACTOR)

        # Create radio box Warning
        self._warning = QtWidgets.QRadioButton(self)
        self._warning.setText(WARNING)
        self._warning.setToolTip(WARNING)

        # Create radio box Error
        self._error = QtWidgets.QRadioButton(self)
        self._error.setText(ERROR)
        self._error.setToolTip(ERROR)

        # Radio box event
        self._all.toggled.connect(
            lambda: self.onRadioChangeState(self._all)
        )
        self._convention.toggled.connect(
            lambda: self.onRadioChangeState(self._convention)
        )
        self._refactor.toggled.connect(
            lambda: self.onRadioChangeState(self._refactor)
        )
        self._warning.toggled.connect(
            lambda: self.onRadioChangeState(self._warning)
        )
        self._error.toggled.connect(
            lambda: self.onRadioChangeState(self._error)
        )

        # Create tree widget
        self._tree = QtWidgets.QTreeWidget(self)
        self._tree.setColumnCount(5)
        self._tree.setHeaderLabels(
            ["Description", "File", "Code", "Line", "Column"]
        )
        self._tree.setColumnWidth(0, 400)
        self._tree.setColumnWidth(1, 80)
        self._tree.setHeaderHidden(False)
        self._tree.setSortingEnabled(True)
        self._tree.sortItems(1, QtCore.Qt.AscendingOrder)
        self._tree.sortItems(2, QtCore.Qt.AscendingOrder)
        self._tree.setRootIsDecorated(False)
        # style
        # set widget stye
        background = self.getThemeItem(item="editor.text")
        textcolor = self.getThemeItem(item="syntax.identifier")
        styleKeys = ["background-color", "color"]
        styleValues = [background["back"], textcolor["fore"]]
        self.setWidgetStyleSheet(self._tree, styleKeys, styleValues)
        # event
        self._tree.clicked.connect(self.onItemClicked)

        # Create two sizers
        self._sizer1 = QtWidgets.QVBoxLayout(self)
        self._sizer2 = QtWidgets.QHBoxLayout()
        self._sizer4 = QtWidgets.QHBoxLayout()
        #
        self._sizer1.setSpacing(2)
        self._sizer1.setContentsMargins(0, 0, 0, 0)

        # Set layout
        self._sizer1.addLayout(self._sizer2, 0)
        self._sizer1.addLayout(self._sizer4, 0)
        self._sizer1.addWidget(self._tree, 1)
        #
        self._sizer2.addWidget(self._reload, 0)
        self._sizer2.addWidget(self._scope, 0)
        self._sizer2.addWidget(self._ratings, 0)
        self._sizer2.addWidget(self._font_options, 0)
        #
        self._sizer4.addWidget(self._all, 0)
        self._sizer4.addWidget(self._convention, 0)
        self._sizer4.addWidget(self._refactor, 0)
        self._sizer4.addWidget(self._warning, 0)
        self._sizer4.addWidget(self._error, 0)
        self._sizer4.addWidget(self._open_file, 0)
        #
        self.setLayout(self._sizer1)

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

    def onRadioChangeState(self, radiobox):
        """ Filter the tree
        """
        root = self._tree.invisibleRootItem()
        child_count = root.childCount()
        for i in range(child_count):
            item = root.child(i)
            # code number column
            code = item.text(2)

            # All
            if (
                    radiobox.text().startswith("All")
                    and radiobox.isChecked() is True
            ):
                if code[0] in ['C', 'R', 'W', 'E']:
                    self._tree.setRowHidden(i, QtCore.QModelIndex(), False)
                else:
                    self._tree.setRowHidden(i, QtCore.QModelIndex(), True)

            # Convention
            if (
                    radiobox.text().startswith("Convention")
                    and radiobox.isChecked() is True
            ):
                if code[0] == "C":
                    self._tree.setRowHidden(i, QtCore.QModelIndex(), False)
                else:
                    self._tree.setRowHidden(i, QtCore.QModelIndex(), True)

            # Refactor
            if (
                    radiobox.text().startswith("Refactor")
                    and radiobox.isChecked() is True
            ):
                if code[0] == "R":
                    self._tree.setRowHidden(i, QtCore.QModelIndex(), False)
                else:
                    self._tree.setRowHidden(i, QtCore.QModelIndex(), True)

            # Warning
            if (
                    radiobox.text().startswith("Warning")
                    and radiobox.isChecked() is True
            ):
                if code[0] == "W":
                    self._tree.setRowHidden(i, QtCore.QModelIndex(), False)
                else:
                    self._tree.setRowHidden(i, QtCore.QModelIndex(), True)

            # Error
            if (
                    radiobox.text().startswith("Error")
                    and radiobox.isChecked() is True
            ):
                if code[0] == "E":
                    self._tree.setRowHidden(i, QtCore.QModelIndex(), False)
                else:
                    self._tree.setRowHidden(i, QtCore.QModelIndex(), True)

    def reset(self):
        """ reset()
        Reset widgets
        """
        self._ratings.setText("Pylint running...")
        self._all.setChecked(True)
        self._all.setText(ALL)
        self._convention.setText(CONVENTION)
        self._refactor.setText(REFACTOR)
        self._warning.setText(WARNING)
        self._error.setText(ERROR)
        self._tree.clear()
        self.output = ""
        self.cur_dir_path = ""

    def start(self):
        """ start()
        Start code inspection
        """
        self.reset()
        self.process = pyzo.QtCore.QProcess(self)
        self.process.finished.connect(self.showOutput)
        self.process.setProcessChannelMode(
            pyzo.QtCore.QProcess.SeparateChannels
        )
        self.process.readyReadStandardOutput.connect(self.readOutput)
        self.process.readyReadStandardError.connect(
            lambda: self.read_output(error=True)
        )

        editor = pyzo.editors.getCurrentEditor()
        scope = self._scope.currentText()
        self.cur_dir_path = os.path.dirname(os.path.abspath(editor.filename))

        if scope == "Current document":
            pylint_exe = "pylint"
            params = [
                "-rn",
                "--msg-template",
                "{path}:{line}:{column}: {msg_id}: {msg} ({symbol})",
                editor.filename,
            ]
        elif scope == "Current document directory":

            pylint_exe = "pylint"
            params = [
                "-rn",
                "--msg-template",
                "{path}:{line}:{column}: {msg_id}: {msg} ({symbol})",
                self.cur_dir_path,
            ]

        self.process.start(pylint_exe, params)



    def readOutput(self):

        qba = pyzo.QtCore.QByteArray()
        while self.process.bytesAvailable():
            qba += self.process.readAllStandardOutput()
        text = self.locale_codec.toUnicode(qba.data())

        self.output += text

    def showOutput(self):
        """ showOutput()
        Fill the treee
        """

        nA = 0
        nC = 0
        nR = 0
        nW = 0
        nE = 0

        # write output in the file
        output_file = os.path.join(self.output_folder, "pylinter_output.txt")
        with open(output_file, "w") as res:
            res.write(self.output)

        for line in self.output.splitlines():
            l = line.split(":")
            try:
                editor = pyzo.editors.getCurrentEditor()
                path = os.path.join(os.path.curdir, editor.filename)
                #path = l[-5].strip()
                line = l[-4].strip()
                col = l[-3].strip()
                msg_id = l[-2].strip()
                msg = l[-1].strip()

                QtWidgets.QTreeWidgetItem(
                    self._tree, [msg, path, msg_id, line, col]
                )

                if msg_id[0] == "C":
                    nC += 1
                elif msg_id[0] == "R":
                    nR += 1
                elif msg_id[0] == "W":
                    nW += 1
                elif msg_id[0] == "E":
                    nE += 1
                nA = nC + nR + nW + nE

            except:
                if l[0].strip().startswith("Your code"):
                    res = l[0].replace("Your code has been rated at", "")
                    res = res.replace("(previous run", "")
                    try:
                        prevsplit = l[1].split(",")
                        prev = prevsplit[1].replace(")", "")
                        self._ratings.setText(res + prev)
                    except:
                        pass

        self._all.setText("{} ({})".format(ALL, str(nA)))
        self._convention.setText("{} ({})".format(CONVENTION, str(nC)))
        self._refactor.setText("{} ({})".format(REFACTOR, str(nR)))
        self._warning.setText("{} ({})".format(WARNING, str(nW)))
        self._error.setText("{} ({})".format(ERROR, str(nE)))

        self.onRadioChangeState(self._convention)

    def onItemClicked(self):
        """ onItemClicked()
        If item clicked in the tree select a line in editor
        """
        editor = pyzo.editors.getCurrentEditor()
        fname = self._tree.currentItem().text(1)
        filepath = os.path.join(self.cur_dir_path, fname)
        lineno = self._tree.currentItem().text(3)

        # load file in the editor
        pyzo.editors.loadFile(filepath)
        cursor = QtGui.QTextCursor(
            editor.document().findBlockByLineNumber(int(lineno) - 1)
        )
        cursor.select(QtGui.QTextCursor.LineUnderCursor)
        editor.setTextCursor(cursor)

    def onOpenOutputFile(self):
        """ onOpenOutputFile()
        Open output file in editor
        """
        fpath = os.path.join(self.output_folder, "pylinter_output.txt")
        pyzo.editors.loadFile(fpath)

    def onFontOptionsPress(self):
        """ Create the menu for the button, Do each time to make sure
        the checks are right. """

        # Get menu
        menu = self._font_options._menu
        menu.clear()

        # Add font size options
        currentSize = self._config.fontSize
        for i in range(8, 15):
            action = menu.addAction("font-size: %ipx" % i)
            action.setCheckable(True)
            action.setChecked(i == currentSize)

    def onFontOptionMenuTiggered(self, action):
        """  The user decides what to show in the structure. """
        # Get text
        text = action.text().lower()

        if "size" in text:
            # Get font size
            size = int(text.split(":", 1)[1][:-2])
            # Update
            self._config.fontSize = size
            # Set font size
            font = self._tree.font()
            font.setPointSize(self._config.fontSize)
            self._tree.setFont(QtGui.QFont(font))

        self._tree.updateGeometries()
