# -*- coding: utf-8 -*-

# Static code analysis tool - pylint

import os

import pyzo
from pyzo.util.qt import QtCore, QtGui, QtWidgets
from pyzo import translate

tool_name = translate('pyzoLinter', 'Linter')
tool_summary = "Shows the structure of your source code."

CONVENTION = 'Convention'
REFACTOR = 'Refactor'
WARNING = 'Warning'
ERROR = 'Error'


class PyzoLinter(QtWidgets.QWidget):
    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)

        # Make sure there is a configuration entry for this tool
        # The pyzo tool manager makes sure that there is an entry in
        # config.tools before the tool is instantiated.

        # toolId = self.__class__.__name__.lower()
        # self._config = pyzo.config.tools[toolId]
        # if not hasattr(self._config, 'showTypes'):
        #     self._config.showTypes = ['class', 'def', 'cell', 'todo']
        # if not hasattr(self._config, 'level'):
        #     self._config.level = 2

        # Keep track of linter output
        self.output = ''

        # Folder for linter output file
        self.output_folder = os.path.join(pyzo.appDataDir, 'tools', 'pyzoLinter')

        self.process = None
        self.locale_codec = pyzo.QtCore.QTextCodec.codecForLocale()

        # Create button for reload current file name
        self._reload = QtWidgets.QToolButton(self)
        self._reload.setIcon(pyzo.icons.arrow_refresh)
        self._reload.setToolTip("Select file")
        # event
        self._reload.clicked.connect(self.getCurrentFileName)

        # Create file path line edit
        self._file_line = QtWidgets.QLineEdit(self)
        self._file_line.setReadOnly(False)
        self._file_line.setToolTip('File for linting')

        # Create button for select file for analise
        self._select_file = QtWidgets.QToolButton(self)
        self._select_file.setIcon(pyzo.icons.folder_page)
        self._select_file.setToolTip("Select file")
        # event
        self._select_file.clicked.connect(self.onSelectFile)

        # Create button for select file for analise
        self._run = QtWidgets.QToolButton(self)
        self._run.setIcon(pyzo.icons.arrow_right)
        self._run.setToolTip("Start")
        # event
        self._run.clicked.connect(self.start)

        # Create button for opening output file in the editor
        self._open_file = QtWidgets.QToolButton(self)
        self._open_file.setIcon(pyzo.icons.page_white_text)
        self._open_file.setIconSize(QtCore.QSize(16, 16))
        self._open_file.setStyleSheet("QToolButton { border: none; padding: 0px; }")
        self._open_file.setToolTip("Open output file in the editor")
        # event
        self._open_file.clicked.connect(self.onOpenOutputFile)

        # Empty label
        self._empty = QtWidgets.QLabel(self)

        # Create options button
        # self._options = QtWidgets.QToolButton(self)
        # self._options.setIcon(pyzo.icons.filter)
        # self._options.setIconSize(QtCore.QSize(16, 16))
        # self._options.setPopupMode(self._options.InstantPopup)
        # self._options.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)

        # Create options menu
        # self._options._menu = QtWidgets.QMenu()
        # self._options.setMenu(self._options._menu)

        # Result label
        self._result = QtWidgets.QLabel(self)
        self._result.setText("Result: ")

        # Ratings label
        self._ratings = QtWidgets.QLabel(self)
        self._ratings.setText("")
        self._ratings.setMinimumHeight(30)
        self._ratings.setMinimumWidth(200)
        self._ratings.setAlignment(QtCore.Qt.AlignCenter)
        ss = 'QLabel{color: red;background-color: #FFFFE0;border-style: outset;border-width: 1px;border-radius: 10px; \
              font: bold 18px;padding: 6px;}'
        self._ratings.setStyleSheet(ss)

        # Create radio box Convention
        self._convention = QtWidgets.QRadioButton(self)
        self._convention.setText(CONVENTION)
        self._convention.setChecked(True)
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
        self._convention.toggled.connect(lambda: self.onRadioChangeState(self._convention))
        self._refactor.toggled.connect(lambda: self.onRadioChangeState(self._refactor))
        self._warning.toggled.connect(lambda: self.onRadioChangeState(self._warning))
        self._error.toggled.connect(lambda: self.onRadioChangeState(self._error))

        # Create tree widget
        self._tree = QtWidgets.QTreeWidget(self)
        self._tree.setColumnCount(3)
        self._tree.setHeaderLabels(["Description", "Code", "Line"])
        self._tree.setColumnWidth(0, 400)
        self._tree.setColumnWidth(1, 80)
        self._tree.setHeaderHidden(False)
        self._tree.setSortingEnabled(True)
        self._tree.sortItems(1, QtCore.Qt.AscendingOrder)
        self._tree.sortItems(2, QtCore.Qt.AscendingOrder)
        # self._tree.setAlternatingRowColors(True)
        self._tree.setRootIsDecorated(False)
        # event
        self._tree.clicked.connect(self.onItemClicked)

        # Create two sizers
        self._sizer1 = QtWidgets.QVBoxLayout(self)
        self._sizer2 = QtWidgets.QHBoxLayout()
        self._sizer3 = QtWidgets.QHBoxLayout()
        self._sizer4 = QtWidgets.QHBoxLayout()
        #
        self._sizer1.setSpacing(2)
        self._sizer1.setContentsMargins(0, 0, 0, 0)

        # Set layout
        self._sizer1.addLayout(self._sizer2, 0)
        self._sizer1.addLayout(self._sizer3, 0)
        self._sizer1.addLayout(self._sizer4, 0)
        self._sizer1.addWidget(self._tree, 1)
        #
        self._sizer2.addWidget(self._reload, 1)
        self._sizer2.addWidget(self._file_line, 1)
        self._sizer2.addWidget(self._select_file, 0)
        self._sizer2.addWidget(self._run, 0)
        self._sizer2.addWidget(self._empty, 0)
        #
        self._sizer3.addWidget(self._result, 0)
        self._sizer3.addWidget(self._ratings, 0)
        self._sizer3.addStretch(1)
        self._sizer3.addWidget(self._open_file, 0)
        # self._sizer3.addWidget(self._options, 0)
        #
        self._sizer4.addWidget(self._convention, 0)
        self._sizer4.addWidget(self._refactor, 0)
        self._sizer4.addWidget(self._warning, 0)
        self._sizer4.addWidget(self._error, 0)
        #
        self.setLayout(self._sizer1)

        # Set current file name
        self.getCurrentFileName()

    def onRadioChangeState(self, radiobox):
        """ Filter the tree
        """
        root = self._tree.invisibleRootItem()
        child_count = root.childCount()
        for i in range(child_count):
            item = root.child(i)
            code = item.text(1)
            # Convention
            if radiobox.text().startswith("Convention") and radiobox.isChecked() is True:
                if code[0] == 'C':

                    self._tree.setRowHidden(i, QtCore.QModelIndex(), False)
                else:
                    self._tree.setRowHidden(i, QtCore.QModelIndex(), True)

            # Refactor
            if radiobox.text().startswith("Refactor") and radiobox.isChecked() is True:
                if code[0] == 'R':
                    self._tree.setRowHidden(i, QtCore.QModelIndex(), False)
                else:
                    self._tree.setRowHidden(i, QtCore.QModelIndex(), True)

            # Warning
            if radiobox.text().startswith("Warning") and radiobox.isChecked() is True:
                if code[0] == 'W':
                    self._tree.setRowHidden(i, QtCore.QModelIndex(), False)
                else:
                    self._tree.setRowHidden(i, QtCore.QModelIndex(), True)

            # Error
            if radiobox.text().startswith("Error") and radiobox.isChecked() is True:
                if code[0] == 'E':
                    self._tree.setRowHidden(i, QtCore.QModelIndex(), False)
                else:
                    self._tree.setRowHidden(i, QtCore.QModelIndex(), True)

    def getCurrentFileName(self):
        """ getCurrentFileName()
        Add current file name in the textbox
        """
        try:
            editor = pyzo.editors.getCurrentEditor()
            self._file_line.setText(editor.filename)
            self.reset()
        except:
            pass

    def reset(self):
        """ reset()
        Reset widgets
        """
        self._ratings.setText("")
        self._convention.setChecked(True)
        self._convention.setText(CONVENTION)
        self._refactor.setText(REFACTOR)
        self._warning.setText(WARNING)
        self._error.setText(ERROR)
        self._tree.clear()

    def start(self):
        """ start()
        Start code inspection
        """
        self.reset()
        self.output = ''
        filename = self._file_line.text()

        pylint_exe = 'pylint'
        params = ['-rn',
                  '--msg-template', '{path}:{line}:{column}: {msg_id}: {msg} ({symbol})',
                  filename
                  ]
        self.process = pyzo.QtCore.QProcess(self)
        self.process.setProcessChannelMode(pyzo.QtCore.QProcess.SeparateChannels)
        self.process.setWorkingDirectory(os.path.dirname(filename))

        self.process.readyReadStandardOutput.connect(self.readOutput)
        self.process.readyReadStandardError.connect(lambda: self.read_output(error=True))

        self.process.finished.connect(self.showOutput)
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
        nC = 0
        nR = 0
        nW = 0
        nE = 0

        # write output in the file
        output_file = os.path.join(self.output_folder, 'pylinter_output.txt')
        with open(output_file, 'w') as res:
            res.write(self.output)

        for line in self.output.splitlines():
            l = line.split(':')
            try:
                line = l[1].strip()
                # col = l[2].strip()
                msg_id = l[3].strip()
                msg = l[4].strip()
                QtWidgets.QTreeWidgetItem(self._tree, [msg, msg_id, line])
                if msg_id[0] == 'C':
                    nC += 1
                elif msg_id[0] == 'R':
                    nR += 1
                elif msg_id[0] == 'W':
                    nW += 1
                elif msg_id[0] == 'E':
                    nE += 1

            except:
                if l[0].strip().startswith('Your code'):
                    res = l[0].replace("Your code has been rated at", "")
                    res = res.replace("(previous run", "")
                    try:
                        prevsplit = l[1].split(',')
                        prev = prevsplit[1].replace(')', "")
                        self._ratings.setText(res + prev)
                    except:
                        pass

        self._convention.setText('{} ({})'.format(CONVENTION, str(nC)))
        self._refactor.setText('{} ({})'.format(REFACTOR, str(nR)))
        self._warning.setText('{} ({})'.format(WARNING, str(nW)))
        self._error.setText('{} ({})'.format(ERROR, str(nE)))

        self.onRadioChangeState(self._convention)

    def onSelectFile(self):
        """ onSelectFile()
        Select file for code inspection
        """
        self.reset()
        filename = self._file_line.text()
        start_dir = os.path.dirname(filename)
        fname = pyzo.QtWidgets.QFileDialog.getOpenFileName(self, 'Select file', start_dir)
        if fname[0]:
            self._file_line.setText(fname[0])
        else:
            self.getCurrentFileName()

    def onItemClicked(self):
        """ onItemClicked()
        If item clicked in the tree select a line in editor
        """
        editor = pyzo.editors.getCurrentEditor()
        lineno = self._tree.currentItem().text(2)
        cursor = QtGui.QTextCursor(editor.document().findBlockByLineNumber(int(lineno) - 1))
        cursor.select(QtGui.QTextCursor.LineUnderCursor)
        editor.setTextCursor(cursor)

    def onOpenOutputFile(self):
        """ onOpenOutputFile()
        Open output file in editor
        """
        fpath = os.path.join(self.output_folder, "pylinter_output.txt")
        pyzo.editors.loadFile(fpath)
