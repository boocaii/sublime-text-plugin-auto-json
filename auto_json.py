"""
This plugin trys to JSON-format text automatically
"""

FILE_NAME_SUFFIX = ['.auto-json', '.auto.json', '.auto_json']
FILE_PREFIX = ['$ auto-json', '$ auto.json', '$ auto_json', '$ auto json']
LINE_BREAKS = ['\n', '\n\r']
EMPTY_BLOCK = ''


import json
import sublime
import sublime_plugin

class AutoJSON(sublime_plugin.ViewEventListener):
	running = False

	def on_modified(self):
		file_name = self.view.file_name()
		text = self.view.substr(sublime.Region(0, self.view.size()))
		if not determine_auto_json(file_name, text):
			return

		if self.running:
			return
		self.running = True
		self.view.run_command("auto_json")
		self.running = False


class AutoJsonCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		# print('AutoJSONCommand')
		text = self.view.substr(sublime.Region(0, self.view.size()))

		line1_ends = text.find('\n')
		if line1_ends < 0:
			return

		text_without_line1 = text[line1_ends+1:]
		if not text_without_line1:
			return
		# print('text_without_line1:\n%s' % text_without_line1)


		try:
			jsoned_text = try_json_blocks(text_without_line1)
			self.view.replace(edit, sublime.Region(line1_ends+1, self.view.size()), jsoned_text)
		except Exception as e:
			import traceback
			traceback.print_exc()
			pass


def determine_auto_json(file_name, text):
	if text and text.startswith('$'):
		for prefix in FILE_PREFIX:
			if text.startswith(prefix):
				return True

	if file_name:
		for suffix in FILE_NAME_SUFFIX:
			if file_name.endswith(suffix):
				return True

	return False


def try_json_blocks(text):
	blocks = get_blocks_with_blank_line(text)
	jsoned_blocks = json_blocks(blocks)
	return ''.join(jsoned_blocks)


def get_blocks_with_blank_line(text):
	blocks = []

	lines = text.splitlines(keepends=True)

	block = EMPTY_BLOCK
	for line in lines:
		if is_empty_line(line):
			if block != EMPTY_BLOCK:
				blocks.append(block)
				block = EMPTY_BLOCK
			blocks.append(line)
		else:
			block += line

	if block != EMPTY_BLOCK:
		blocks.append(block)

	return blocks


def json_blocks(blocks):
	jsoned_blocks = []
	for block in blocks:
		if is_empty_line(block):
			jsoned_blocks.append(block)
			continue

		jsoned_blocks.append(json_block(block))

	# print('jsoned_blocks: {}'.format(jsoned_blocks))

	return jsoned_blocks


def json_block(text):
	if text.startswith('{') or text.startswith('['):
		try:
			obj = json.loads(text)
			return json_dumps(json_json_obj(obj)) + '\n'
		except Exception as e:
			return text

	return text


def json_json_obj(obj):
	# print('obj type: {}, value: {}'.format(type(obj), obj))
	if isinstance(obj, list):
		return __json_json_list(obj)

	if isinstance(obj, dict):
		return __json_json_dict(obj)

	if isinstance(obj, str):
		return __json_loads(obj)

	return obj


def __json_loads(text):
	if isinstance(text, str) and (text.startswith('{') or text.startswith('[')):
		try:
			# print('text: {}'.format(text))
			json_obj = json.loads(text)
			return json_json_obj(json_obj)
		except Exception as e:
			raise

	return text


def __json_json_list(l):
	if not isinstance(l, list):
		return l

	return [json_json_obj(t) for t in l]


def __json_json_dict(d):
	if not isinstance(d, dict):
		return d

	return {k: json_json_obj(v) for k, v in d.items()}


def json_dumps(obj):
	return json.dumps(obj, ensure_ascii=False, indent='    ')


def is_empty_line(line):
	return not line.strip()

