# -*- coding: UTF-8 -*-
# ClipBoardEditor- global plugin
# Editor de conteúdo da área de transferência com histórico e formatação.
# Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
# This file is covered by the GNU General Public License, version 2.
# See the file COPYING for more details.

import globalPluginHandler
from scriptHandler import script

import wx
import api
import gui
import ui
import logHandler

import json
import re


# ============================================================
# IDENTIFICAÇÃO DE FORMATOS
# ============================================================


def detectFormat(text):
	content = text.strip()

	if not content:
		return None

	# JSON: objetos e arrays.
	if (content.startswith("{") and content.endswith("}")) or (
		content.startswith("[") and content.endswith("]")
	):
		try:
			json.loads(content)
			return "json"
		except json.JSONDecodeError:
			pass

	# XML.
	if content.startswith("<?xml") or re.match(r"^<[\w:.-]+(?:\s|>)", content):
		try:
			from xml.dom import minidom

			minidom.parseString(content)
			return "xml"
		except Exception:
			pass

	# SQL.
	sql_pattern = (
		r"^(SELECT|INSERT|UPDATE|DELETE|WITH|CREATE|ALTER|"
		r"DROP|TRUNCATE|EXEC|EXECUTE|MERGE|DECLARE|SET)\b"
	)

	if re.match(sql_pattern, content, re.IGNORECASE):
		return "sql"

	return None


# ============================================================
# FORMATADOR SQL
# ============================================================


def formatSQL(text):
	keywords = [
		"SELECT",
		"FROM",
		"WHERE",
		"INNER JOIN",
		"LEFT JOIN",
		"RIGHT JOIN",
		"FULL JOIN",
		"JOIN",
		"ON",
		"AND",
		"OR",
		"GROUP BY",
		"ORDER BY",
		"HAVING",
		"UNION ALL",
		"UNION",
		"INSERT INTO",
		"VALUES",
		"UPDATE",
		"SET",
		"DELETE FROM",
		"CREATE TABLE",
		"ALTER TABLE",
		"DROP TABLE",
		"WHEN",
		"THEN",
		"ELSE",
		"END",
		"LIMIT",
		"OFFSET",
	]

	formatted = re.sub(r"\s+", " ", text.strip())

	for keyword in sorted(keywords, key=len, reverse=True):
		pattern = r"\b" + re.escape(keyword) + r"\b"

		formatted = re.sub(
			pattern,
			"\n" + keyword,
			formatted,
			flags=re.IGNORECASE,
		)

	lines = formatted.splitlines()
	result = []

	for line in lines:
		line = line.strip()

		if not line:
			continue

		upper_line = line.upper()

		if upper_line.startswith(("AND ", "OR ", "ON ")):
			result.append("    " + line)
		else:
			result.append(line)

	return "\n".join(result).strip()


# ============================================================
# DIÁLOGO DO EDITOR
# ============================================================


class ClipboardEditorDialog(wx.Dialog):
	def __init__(self, parent, clipboard_text, history):
		super().__init__(
			parent,
			title="Editor da área de transferência",
			size=(1000, 550),
			style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
		)

		self.history = list(history)

		# ----------------------------------------------------
		# ÁREA PRINCIPAL
		# ----------------------------------------------------

		mainSizer = wx.BoxSizer(wx.VERTICAL)

		instructions = wx.StaticText(
			self,
			label=("Edite o conteúdo. Pressione ESC para salvar."),
		)

		mainSizer.Add(
			instructions,
			0,
			wx.ALL,
			10,
		)

		contentSizer = wx.BoxSizer(wx.HORIZONTAL)

		# ----------------------------------------------------
		# EDITOR DE TEXTO
		# ----------------------------------------------------

		editorSizer = wx.BoxSizer(wx.VERTICAL)

		self.textCtrl = wx.TextCtrl(
			self,
			value=clipboard_text,
			style=wx.TE_MULTILINE | wx.TE_RICH2,
		)

		self.textCtrl.SetName("Texto para edição")

		editorSizer.Add(
			self.textCtrl,
			1,
			wx.EXPAND | wx.ALL,
			5,
		)

		contentSizer.Add(
			editorSizer,
			3,
			wx.EXPAND | wx.ALL,
			5,
		)

		# ----------------------------------------------------
		# HISTÓRICO
		# ----------------------------------------------------

		historySizer = wx.BoxSizer(wx.VERTICAL)

		historyLabel = wx.StaticText(
			self,
			label="Últimos 10 textos copiados",
		)

		historySizer.Add(
			historyLabel,
			0,
			wx.ALL,
			5,
		)

		self.historyList = wx.ListBox(
			self,
			choices=[],
			style=wx.LB_SINGLE,
		)

		self.historyList.SetName(
			"Histórico dos últimos 10 textos copiados",
		)

		historySizer.Add(
			self.historyList,
			1,
			wx.EXPAND | wx.ALL,
			5,
		)

		historyInstructions = wx.StaticText(
			self,
			label="Selecione um texto e pressione ENTER para editar.",
		)

		historySizer.Add(
			historyInstructions,
			0,
			wx.ALL,
			5,
		)

		contentSizer.Add(
			historySizer,
			2,
			wx.EXPAND | wx.ALL,
			5,
		)

		mainSizer.Add(
			contentSizer,
			1,
			wx.EXPAND,
		)

		# ----------------------------------------------------
		# BOTÕES
		# ----------------------------------------------------

		buttonSizer = wx.BoxSizer(wx.HORIZONTAL)

		self.formatButton = wx.Button(
			self,
			label="Formatar JSON",
		)

		self.formatButton.Bind(
			wx.EVT_BUTTON,
			self.formatContent,
		)

		buttonSizer.Add(
			self.formatButton,
			0,
			wx.ALL,
			5,
		)

		saveButton = wx.Button(
			self,
			wx.ID_OK,
			"Salvar",
		)

		cancelButton = wx.Button(
			self,
			wx.ID_CANCEL,
			"Cancelar",
		)

		buttonSizer.Add(
			saveButton,
			0,
			wx.ALL,
			5,
		)

		buttonSizer.Add(
			cancelButton,
			0,
			wx.ALL,
			5,
		)

		mainSizer.Add(
			buttonSizer,
			0,
			wx.ALIGN_RIGHT | wx.ALL,
			5,
		)

		self.SetSizer(mainSizer)

		# ----------------------------------------------------
		# EVENTOS
		# ----------------------------------------------------

		self.Bind(
			wx.EVT_CHAR_HOOK,
			self.onKeyPress,
		)

		self.textCtrl.Bind(
			wx.EVT_CHAR_HOOK,
			self.onKeyPress,
		)

		self.historyList.Bind(
			wx.EVT_CHAR_HOOK,
			self.onKeyPress,
		)

		saveButton.Bind(
			wx.EVT_BUTTON,
			self.saveAndClose,
		)

		cancelButton.Bind(
			wx.EVT_BUTTON,
			self.cancelAndClose,
		)

		self.updateFormatButton()
		self.setHistory(history)

		self.textCtrl.SetFocus()
		self.textCtrl.SetInsertionPointEnd()

	# --------------------------------------------------------
	# ATUALIZAÇÃO DO HISTÓRICO
	# --------------------------------------------------------

	def setHistory(self, history):
		self.history = list(history)

		choices = []

		for index, text in enumerate(self.history):
			# Apresenta uma prévia do conteúdo.
			preview = re.sub(r"\s+", " ", text).strip()

			if len(preview) > 100:
				preview = preview[:100] + "..."

			choices.append(
				f"{index + 1}. {preview}",
			)

		self.historyList.Set(choices)

	# --------------------------------------------------------
	# CARREGAMENTO DE UM TEXTO DO HISTÓRICO
	# --------------------------------------------------------

	def loadHistoryItem(self):
		index = self.historyList.GetSelection()

		if index == wx.NOT_FOUND:
			ui.message("Nenhum texto selecionado.")
			return

		if index >= len(self.history):
			return

		selectedText = self.history[index]

		self.textCtrl.SetValue(selectedText)

		self.updateFormatButton()

		self.textCtrl.SetFocus()
		self.textCtrl.SetInsertionPointEnd()

		ui.message("Texto carregado para edição.")

	# --------------------------------------------------------
	# ATUALIZAÇÃO DO BOTÃO DE FORMATAÇÃO
	# --------------------------------------------------------

	def updateFormatButton(self):
		self.detectedFormat = detectFormat(
			self.textCtrl.GetValue(),
		)

		formatNames = {
			"json": "Formatar JSON",
			"xml": "Formatar XML",
			"sql": "Formatar SQL",
		}

		if self.detectedFormat:
			self.formatButton.SetLabel(
				formatNames[self.detectedFormat],
			)

			self.formatButton.Show()

		else:
			self.formatButton.Hide()

		self.Layout()

	# --------------------------------------------------------
	# FORMATAÇÃO DO CONTEÚDO
	# --------------------------------------------------------

	def formatContent(self, event=None):
		text = self.textCtrl.GetValue()

		try:
			if self.detectedFormat == "json":
				parsed = json.loads(text)

				formatted = json.dumps(
					parsed,
					indent=4,
					ensure_ascii=False,
				)

				message = "JSON formatado com sucesso!"

			elif self.detectedFormat == "xml":
				from xml.dom import minidom

				parsed = minidom.parseString(text)

				formatted = parsed.toprettyxml(
					indent="    ",
					encoding=None,
				)

				formatted = "\n".join(line for line in formatted.splitlines() if line.strip())

				message = "XML formatado com sucesso!"

			elif self.detectedFormat == "sql":
				formatted = formatSQL(text)

				message = "SQL formatado com sucesso!"

			else:
				ui.message("Formato não identificado.")
				return

			self.textCtrl.SetValue(formatted)

			self.textCtrl.SetInsertionPoint(0)
			self.textCtrl.SetFocus()

			self.updateFormatButton()

			ui.message(message)

		except json.JSONDecodeError as error:
			ui.message(
				f"JSON inválido. Linha {error.lineno}, coluna {error.colno}.",
			)

			self.textCtrl.SetFocus()

		except Exception:
			logHandler.log.error(
				"Erro ao formatar conteúdo",
				exc_info=True,
			)

			ui.message(
				"Não foi possível formatar o conteúdo.",
			)

			self.textCtrl.SetFocus()

	# --------------------------------------------------------
	# TECLADO
	# --------------------------------------------------------

	def onKeyPress(self, event):
		keyCode = event.GetKeyCode()

		# ENTER na lista carrega o texto selecionado.
		if keyCode in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER) and self.historyList.HasFocus():
			self.loadHistoryItem()
			return

		# ESC salva o conteúdo atual.
		if keyCode == wx.WXK_ESCAPE:
			event.StopPropagation()
			self.saveAndClose()
			return

		event.Skip()

	# --------------------------------------------------------
	# SALVAR
	# --------------------------------------------------------

	def saveAndClose(self, event=None):
		text = self.textCtrl.GetValue()

		if not text:
			ui.message(
				"O texto está vazio. A área de transferência não foi alterada.",
			)

			return

		try:
			api.copyToClip(text)

			self.EndModal(wx.ID_OK)

		except Exception:
			logHandler.log.error(
				"Erro ao atualizar a área de transferência",
				exc_info=True,
			)

			ui.message(
				"Não foi possível atualizar a área de transferência.",
			)

	# --------------------------------------------------------
	# CANCELAR
	# --------------------------------------------------------

	def cancelAndClose(self, event=None):
		self.EndModal(wx.ID_CANCEL)


# ============================================================
# PLUGIN GLOBAL
# ============================================================


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self):
		super().__init__()

		self.activeDialog = None

		# Histórico em memória.
		self.clipboardHistory = []

		# Último conteúdo observado.
		self.lastClipboardText = None

		self.terminated = False

		# Captura o conteúdo que já estiver na área
		# de transferência quando o plugin iniciar.
		try:
			initialText = api.getClipData() or ""
		except Exception:
			initialText = ""

		self.recordClipboard(initialText)

		# Inicia o monitoramento.
		wx.CallAfter(self.scheduleClipboardCheck)

	# --------------------------------------------------------
	# REGISTRO DO HISTÓRICO
	# --------------------------------------------------------

	def recordClipboard(self, text):
		if not text:
			return

		# Evita duplicação consecutiva.
		if not self.clipboardHistory or self.clipboardHistory[0] != text:
			self.clipboardHistory.insert(0, text)

			self.clipboardHistory = self.clipboardHistory[:10]

			# Atualiza a lista se o editor estiver aberto.
			if self.activeDialog is not None:
				self.activeDialog.setHistory(
					self.clipboardHistory,
				)

	# --------------------------------------------------------
	# MONITORAMENTO DA ÁREA DE TRANSFERÊNCIA
	# --------------------------------------------------------

	def scheduleClipboardCheck(self):
		if self.terminated:
			return

		self.clipboardTimer = wx.CallLater(
			300,
			self.checkClipboard,
		)

	def checkClipboard(self):
		if self.terminated:
			return

		try:
			# Proteção ao ler área de transferência em background
			try:
				currentText = api.getClipData() or ""
			except Exception:
				currentText = ""

			if currentText != self.lastClipboardText:
				self.lastClipboardText = currentText

				self.recordClipboard(currentText)

		except Exception:
			logHandler.log.error(
				"Erro ao monitorar a área de transferência",
				exc_info=True,
			)

		self.scheduleClipboardCheck()

	# --------------------------------------------------------
	# ATALHO PRINCIPAL
	# --------------------------------------------------------

	@script(
		description="Abre o editor da área de transferência",
		gesture="kb:NVDA+shift+c",
	)
	def script_clipboardEditor(self, gesture):
		wx.CallAfter(self.openEditor)

	# --------------------------------------------------------
	# ABERTURA DO EDITOR
	# --------------------------------------------------------

	def openEditor(self):
		# Verifica se já existe uma janela aberta.
		if self.activeDialog is not None:
			oldDialog = self.activeDialog

			answer = wx.MessageBox(
				"Já existe uma edição aberta.\n\nDeseja descartar a edição atual e abrir um novo texto?",
				"Editor da área de transferência",
				wx.YES_NO | wx.ICON_QUESTION | wx.NO_DEFAULT,
				oldDialog,
			)

			# NÃO: mantém a janela atual.
			if answer != wx.YES:
				oldDialog.Raise()
				oldDialog.SetFocus()

				return

			# SIM: descarta a edição anterior.
			self.activeDialog = None

			oldDialog.EndModal(wx.ID_CANCEL)

			# Abre a nova janela após encerrar a anterior.
			wx.CallAfter(self.openEditor)

			return

		dialog = None

		try:
			# Proteção para quando a área de transferência estiver vazia ou for um arquivo/imagem
			try:
				clipboard_text = api.getClipData() or ""
			except Exception:
				clipboard_text = ""

			# Atualiza o histórico com o conteúdo atual.
			self.lastClipboardText = clipboard_text

			self.recordClipboard(clipboard_text)

			dialog = ClipboardEditorDialog(
				gui.mainFrame,
				clipboard_text,
				self.clipboardHistory,
			)

			self.activeDialog = dialog

			result = dialog.ShowModal()

			if result == wx.ID_OK:
				ui.message(
					"Área de transferência atualizada!",
				)

			else:
				ui.message(
					"Edição cancelada.",
				)

		except Exception:
			logHandler.log.error(
				"Erro no Clipboard Editor",
				exc_info=True,
			)

			ui.message(
				"Erro ao executar o editor da área de transferência.",
			)

		finally:
			if dialog is not None:
				if self.activeDialog is dialog:
					self.activeDialog = None

				dialog.Destroy()

	# --------------------------------------------------------
	# ENCERRAMENTO DO PLUGIN
	# --------------------------------------------------------

	def terminate(self):
		self.terminated = True

		if hasattr(self, "clipboardTimer"):
			if self.clipboardTimer.IsRunning():
				self.clipboardTimer.Stop()

		super().terminate()
