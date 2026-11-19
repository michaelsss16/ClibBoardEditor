import globalPluginHandler
from scriptHandler import script

import wx
import api
import gui
import ui
import logHandler

import json
import re
import xml.etree.ElementTree as ET

# ============================================================
# CONFIGURAÇÕES E CONSTANTES
# ============================================================

MAX_ANALYSIS_LENGTH = 300_000  # Limite de ~300 KB para validações de formato

RE_WHITESPACE = re.compile(r"\s+")
RE_SQL_STRINGS = re.compile(r"'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"")
RE_SQL_DETECT = re.compile(
	r"^(SELECT|INSERT|UPDATE|DELETE|WITH|CREATE|ALTER|"
	r"DROP|TRUNCATE|EXEC|EXECUTE|MERGE|DECLARE|SET)\b",
	re.IGNORECASE,
)
RE_XML_START = re.compile(r"^<[\w:.-]+(?:\s|>)", re.DOTALL)

# ============================================================
# IDENTIFICAÇÃO DE FORMATOS
# ============================================================


def detectFormat(text):
	if not text or len(text) > MAX_ANALYSIS_LENGTH:
		return None

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
	if content.startswith("<?xml") or RE_XML_START.match(content):
		try:
			ET.fromstring(content)
			return "xml"
		except Exception:
			pass

	# SQL.
	if RE_SQL_DETECT.match(content):
		return "sql"

	return None


# ============================================================
# FORMATADOR SQL
# ============================================================


def formatSQL(text):
	if len(text) > MAX_ANALYSIS_LENGTH:
		return text

	# Isola e protege strings literais para não quebrar conteúdo entre aspas
	literals = []

	def save_literal(match):
		literals.append(match.group(0))
		return f"__SQL_LITERAL_{len(literals) - 1}__"

	text_protected = RE_SQL_STRINGS.sub(save_literal, text)
	formatted = RE_WHITESPACE.sub(" ", text_protected.strip())

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

	final_sql = "\n".join(result).strip()

	# Restaura as strings literais originais
	for idx, literal in enumerate(literals):
		final_sql = final_sql.replace(f"__SQL_LITERAL_{idx}__", literal)

	return final_sql


# ============================================================
# FORMATADOR XML
# ============================================================


def formatXML(text):
	root = ET.fromstring(text)
	if hasattr(ET, "indent"):
		ET.indent(root, space="    ")
		return ET.tostring(root, encoding="unicode")
	else:
		from xml.dom import minidom

		parsed = minidom.parseString(text)
		formatted = parsed.toprettyxml(indent="    ")
		return "\n".join(line for line in formatted.splitlines() if line.strip())


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
		self.detectedFormat = None
		self._formatTimer = None

		# ----------------------------------------------------
		# ÁREA PRINCIPAL
		# ----------------------------------------------------

		mainSizer = wx.BoxSizer(wx.VERTICAL)

		instructions = wx.StaticText(
			self,
			label="Edite o conteúdo. Pressione Ctrl+Shift+S para salvar, ou ESC para cancelar.",
		)

		mainSizer.Add(
			instructions,
			0,
			wx.ALL,
			10,
		)

		contentSizer = wx.BoxSizer(wx.HORIZONTAL)

		# ----------------------------------------------------
		# EDITOR DE TEXTO (Sem quebra de linha visual)
		# ----------------------------------------------------

		editorSizer = wx.BoxSizer(wx.VERTICAL)

		self.textCtrl = wx.TextCtrl(
			self,
			value=clipboard_text,
			style=wx.TE_MULTILINE | wx.TE_DONTWRAP | wx.HSCROLL | wx.TE_RICH2,
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
			label="Formatar",
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
			"Salvar (Ctrl+Shift+S)",
		)

		cancelButton = wx.Button(
			self,
			wx.ID_CANCEL,
			"Cancelar (Esc)",
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

		self.Bind(wx.EVT_CHAR_HOOK, self.onKeyPress)

		self.textCtrl.Bind(wx.EVT_TEXT, self.onTextChanged)

		saveButton.Bind(wx.EVT_BUTTON, self.saveAndClose)
		cancelButton.Bind(wx.EVT_BUTTON, self.cancelAndClose)

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
			preview = RE_WHITESPACE.sub(" ", text).strip()
			if len(preview) > 100:
				preview = preview[:100] + "..."

			choices.append(f"{index + 1}. {preview}")

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
	# DETECÇÃO DINÂMICA DE FORMATO
	# --------------------------------------------------------

	def onTextChanged(self, event):
		# Debounce de 250ms para não sobrecarregar a digitação
		if self._formatTimer and self._formatTimer.IsRunning():
			self._formatTimer.Stop()

		self._formatTimer = wx.CallLater(250, self.updateFormatButton)
		event.Skip()

	def updateFormatButton(self):
		self.detectedFormat = detectFormat(self.textCtrl.GetValue())

		formatNames = {
			"json": "Formatar JSON",
			"xml": "Formatar XML",
			"sql": "Formatar SQL",
		}

		if self.detectedFormat:
			self.formatButton.SetLabel(formatNames[self.detectedFormat])
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
				formatted = json.dumps(parsed, indent=4, ensure_ascii=False)
				message = "JSON formatado com sucesso!"

			elif self.detectedFormat == "xml":
				formatted = formatXML(text)
				message = "XML formatado com sucesso!"

			elif self.detectedFormat == "sql":
				formatted = formatSQL(text)
				message = "SQL formatado com sucesso!"

			else:
				ui.message("Nenhum formato compatível identificado.")
				return

			self.textCtrl.SetValue(formatted)
			self.textCtrl.SetInsertionPoint(0)
			self.textCtrl.SetFocus()
			self.updateFormatButton()

			ui.message(message)

		except json.JSONDecodeError as error:
			ui.message(f"JSON inválido. Linha {error.lineno}, coluna {error.colno}.")
			self.textCtrl.SetFocus()

		except Exception:
			logHandler.log.error("Erro ao formatar conteúdo", exc_info=True)
			ui.message("Não foi possível formatar o conteúdo.")
			self.textCtrl.SetFocus()

	# --------------------------------------------------------
	# CONTROLE DE TECLADO
	# --------------------------------------------------------

	def onKeyPress(self, event):
		keyCode = event.GetKeyCode()
		modifiers = event.GetModifiers()

		# ENTER na lista carrega o texto selecionado
		if keyCode in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER) and self.historyList.HasFocus():
			self.loadHistoryItem()
			return

		# Ctrl+Shift+S salva e fecha
		if modifiers == (wx.MOD_CONTROL | wx.MOD_SHIFT) and keyCode in (ord("S"), ord("s")):
			event.StopPropagation()
			self.saveAndClose()
			return

		# Ctrl+Shift+F formata o conteúdo
		if modifiers == (wx.MOD_CONTROL | wx.MOD_SHIFT) and keyCode in (ord("F"), ord("f")):
			event.StopPropagation()
			self.formatContent()
			return

		# ESC cancela e fecha (Padrão de acessibilidade)
		if keyCode == wx.WXK_ESCAPE:
			event.StopPropagation()
			self.cancelAndClose()
			return

		event.Skip()

	# --------------------------------------------------------
	# SALVAR
	# --------------------------------------------------------

	def saveAndClose(self, event=None):
		text = self.textCtrl.GetValue()

		try:
			api.copyToClip(text)
			self.EndModal(wx.ID_OK)

		except Exception:
			logHandler.log.error(
				"Erro ao atualizar a área de transferência",
				exc_info=True,
			)
			ui.message("Não foi possível atualizar a área de transferência.")

	# --------------------------------------------------------
	# CANCELAR
	# --------------------------------------------------------

	def cancelAndClose(self, event=None):
		if self._formatTimer and self._formatTimer.IsRunning():
			self._formatTimer.Stop()
		self.EndModal(wx.ID_CANCEL)


# ============================================================
# PLUGIN GLOBAL
# ============================================================


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self):
		super().__init__()

		self.activeDialog = None
		self.clipboardHistory = []
		self.lastClipboardText = None
		self.terminated = False

		try:
			initialText = api.getClipData() or ""
		except Exception:
			initialText = ""

		self.recordClipboard(initialText)

		# Inicia o monitoramento periódico
		wx.CallAfter(self.scheduleClipboardCheck)

	# --------------------------------------------------------
	# REGISTRO DO HISTÓRICO
	# --------------------------------------------------------

	def recordClipboard(self, text):
		if not text:
			return

		if not self.clipboardHistory or self.clipboardHistory[0] != text:
			self.clipboardHistory.insert(0, text)
			self.clipboardHistory = self.clipboardHistory[:10]

			if self.activeDialog is not None:
				self.activeDialog.setHistory(self.clipboardHistory)

	# --------------------------------------------------------
	# MONITORAMENTO DA ÁREA DE TRANSFERÊNCIA
	# --------------------------------------------------------

	def scheduleClipboardCheck(self):
		if self.terminated:
			return

		# Verificação com intervalo de 1000 ms para evitar bloqueios de sistema
		self.clipboardTimer = wx.CallLater(
			1000,
			self.checkClipboard,
		)

	def checkClipboard(self):
		if self.terminated:
			return

		try:
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
		if self.activeDialog is not None:
			oldDialog = self.activeDialog

			answer = wx.MessageBox(
				"Já existe uma edição aberta.\n\nDeseja descartar a edição atual e abrir um novo texto?",
				"Editor da área de transferência",
				wx.YES_NO | wx.ICON_QUESTION | wx.NO_DEFAULT,
				oldDialog,
			)

			if answer != wx.YES:
				oldDialog.Raise()
				oldDialog.SetFocus()
				return

			self.activeDialog = None
			oldDialog.EndModal(wx.ID_CANCEL)

			wx.CallAfter(self.openEditor)
			return

		dialog = None

		try:
			try:
				clipboard_text = api.getClipData() or ""
			except Exception:
				clipboard_text = ""

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
				ui.message("Área de transferência atualizada!")
			else:
				ui.message("Edição cancelada.")

		except Exception:
			logHandler.log.error("Erro no Clipboard Editor", exc_info=True)
			ui.message("Erro ao executar o editor da área de transferência.")

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

		if hasattr(self, "clipboardTimer") and self.clipboardTimer.IsRunning():
			self.clipboardTimer.Stop()

		super().terminate()
