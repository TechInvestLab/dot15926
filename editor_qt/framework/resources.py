"""
 .15925 Editor
Copyright 2014 TechInvestLab.ru dot15926@gmail.com

.15925 Editor is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 3.0 of the License, or (at your option) any later version.

.15925 Editor is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with .15925 Editor.
"""




import os

from PySide.QtCore import *
from PySide.QtGui import *
import gettext
import re
from collections import defaultdict

language_codes = {'aa': 'Afar', 'ab': 'Abkhazian', 'ae': 'Avestan', 'af': 'Afrikaans', 
					'ak': 'Akan', 'am': 'Amharic', 'an': 'Aragonese', 'ar': 'Arabic', 
					'as': 'Assamese', 'av': 'Avaric', 'ay': 'Aymara', 'az': 'Azerbaijani', 
					'ba': 'Bashkir', 'be': 'Belarusian', 'bg': 'Bulgarian', 'bh': 
					'Bihari', 'bi': 'Bislama', 'bm': 'Bambara', 'bn': 'Bengali; Bangla', 
					'bo': 'Tibetan', 'br': 'Breton', 'bs': 'Bosnian', 'ca': 'Catalan', 
					'ce': 'Chechen', 'ch': 'Chamorro', 'co': 'Corsican', 'cr': 'Cree', 
					'cs': 'Czech', 'cu': 'Church Slavic', 'cv': 'Chuvash', 'cy': 'Welsh', 
					'da': 'Danish', 'de': 'German', 'dv': 'Divehi; Maldivian', 
					'dz': 'Dzongkha; Bhutani', 'ee': '\u00c9w\u00e9', 'el': 'Greek', 'en': 'English', 
					'eo': 'Esperanto', 'es': 'Spanish', 'et': 'Estonian', 'eu': 'Basque', 
					'fa': 'Persian', 'ff': 'Fulah', 'fi': 'Finnish', 'fj': 'Fijian; Fiji', 
					'fo': 'Faroese', 'fr': 'French', 'fy': 'Western Frisian', 'ga': 'Irish', 
					'gd': 'Scottish Gaelic', 'gl': 'Galician', 'gn': 'Guarani',
					'gu': 'Gujarati', 'gv': 'Manx', 'ha': 'Hausa', 'he': 'Hebrew (formerly iw)', 
					'hi': 'Hindi', 'ho': 'Hiri Motu', 'hr': 'Croatian', 
					'ht': 'Haitian; Haitian Creole', 'hu': 'Hungarian', 'hy': 'Armenian', 
					'hz': 'Herero', 'ia': 'Interlingua', 'id': 'Indonesian (formerly in)', 
					'ie': 'Interlingue; Occidental', 'ig': 'Igbo', 'ii': 'Sichuan Yi; Nuosu', 
					'ik': 'Inupiak; Inupiaq', 'io': 'Ido', 'is': 'Icelandic', 'it': 'Italian', 
					'iu': 'Inuktitut', 'ja': 'Japanese', 'jv': 'Javanese', 'ka': 'Georgian', 
					'kg': 'Kongo', 'ki': 'Kikuyu; Gikuyu', 'kj': 'Kuanyama; Kwanyama', 
					'kk': 'Kazakh', 'kl': 'Kalaallisut; Greenlandic', 'km': 'Central Khmer; Cambodian', 
					'kn': 'Kannada', 'ko': 'Korean', 'kr': 'Kanuri', 'ks': 'Kashmiri', 'ku': 'Kurdish', 
					'kv': 'Komi', 'kw': 'Cornish', 'ky': 'Kirghiz', 'la': 'Latin', 
					'lb': 'Letzeburgesch; Luxembourgish', 'lg': 'Ganda', 
					'li': 'Limburgish; Limburger; Limburgan', 'ln': 'Lingala', 'lo': 'Lao; Laotian', 
					'lt': 'Lithuanian', 'lu': 'Luba-Katanga', 'lv': 'Latvian; Lettish', 
					'mg': 'Malagasy', 'mh': 'Marshallese', 'mi': 'Maori', 'mk': 'Macedonian', 
					'ml': 'Malayalam', 'mn': 'Mongolian', 'mo': 'Moldavian', 'mr': 'Marathi', 
					'ms': 'Malay', 'mt': 'Maltese', 'my': 'Burmese', 'na': 'Nauru', 
					'nb': 'Norwegian Bokm\u00e5l', 'nd': 'Ndebele, North', 'ne': 'Nepali', 'ng': 'Ndonga', 
					'nl': 'Dutch', 'nn': 'Norwegian Nynorsk', 'no': 'Norwegian', 'nr': 'Ndebele, South', 
					'nv': 'Navajo; Navaho', 'ny': 'Chichewa; Nyanja', 'oc': 'Occitan; Proven\u00e7al', 
					'oj': 'Ojibwa', 'om': '(Afan) Oromo', 'or': 'Oriya', 'os': 'Ossetian; Ossetic', 
					'pa': 'Panjabi; Punjabi', 'pi': 'Pali', 'pl': 'Polish', 'ps': 'Pashto; Pushto', 
					'pt': 'Portuguese', 'qu': 'Quechua', 'rm': 'Romansh', 'rn': 'Rundi; Kirundi', 
					'ro': 'Romanian', 'ru': 'Russian', 'rw': 'Kinyarwanda', 'sa': 'Sanskrit', 
					'sc': 'Sardinian', 'sd': 'Sindhi', 'se': 'Northern Sami', 'sg': 'Sango; Sangro', 
					'si': 'Sinhala; Sinhalese', 'sk': 'Slovak', 'sl': 'Slovenian', 'sm': 'Samoan', 
					'sn': 'Shona', 'so': 'Somali', 'sq': 'Albanian', 'sr': 'Serbian', 
					'ss': 'Swati; Siswati', 'st': 'Sesotho; Sotho, Southern', 'su': 'Sundanese', 
					'sv': 'Swedish', 'sw': 'Swahili', 'ta': 'Tamil', 'te': 'Telugu', 'tg': 'Tajik', 
					'th': 'Thai', 'ti': 'Tigrinya', 'tk': 'Turkmen', 'tl': 'Tagalog', 
					'tn': 'Tswana; Setswana', 'to': 'Tonga', 'tr': 'Turkish', 'ts': 'Tsonga', 
					'tt': 'Tatar', 'tw': 'Twi', 'ty': 'Tahitian', 'ug': 'Uighur', 'uk': 'Ukrainian', 
					'ur': 'Urdu', 'uz': 'Uzbek', 've': 'Venda', 'vi': 'Vietnamese', 
					'vo': 'Volap\u00fck; Volapuk', 'wa': 'Walloon', 'wo': 'Wolof', 'xh': 'Xhosa', 
					'yi': 'Yiddish (formerly ji)', 'yo': 'Yoruba', 'za': 'Zhuang', 
					'zh': 'Chinese', 'zu': 'Zulu'}

class Translator(QTranslator):

	def __init__(self, parent = None):
		QTranslator.__init__(self, parent)
		self.data = defaultdict(dict)

	def AddTranslation(self, context, sourceText, translation, comment = ''):
		self.data[context][sourceText] = translation

	def isEmpty(self):
		return False

	def translate(self, context, sourceText, comment = ''):
		ctx_data = self.data.get(context)
		if ctx_data:
			return ctx_data.get(sourceText, sourceText)
		return sourceText

expr = re.compile(r'\s*([^"\s]+)\s+"((?:\\"|[^"])+)"', re.MULTILINE)
expr_contexts = re.compile(r'\s*([^"\s]+)\s*\[(.*)\]', re.MULTILINE | re.DOTALL)
expr_keys = re.compile(r'\s*"((?:\\"|[^"])+)"', re.MULTILINE)

class DummyTextModule():

	def __init__(self, name):
		self.name = name

	def __getattr__(self, key):
		return '"%s.%s" undefined'%(self.name, key)

class _fallback():
	def gettext(self, text):
		return None

class TextModule():

	def __init__(self, path, tranlsator):
		self._path = path
		self._name = os.path.splitext(os.path.basename(self._path))[0]

		with open(self._path, 'r') as f:
			content = f.read()
			result = re.findall(expr, content)
			result = [(k, v.decode('string-escape')) for k, v in result]
			try:
				translation = gettext.translation('dot15926_%s'%self._name, os.path.join(appdata.resources_dir, 'locale'), languages=[appconfig.get('language', 'en')])
				result = [(k, translation.gettext(v)) for k, v in result]
				translation.add_fallback(_fallback())
				for ctx, keys in re.findall(expr_contexts, content):
					for k in re.findall(expr_keys, keys):
						value = k.decode('string-escape')
						res = translation.gettext("%s\x04%s"%(ctx,value))
						if res:
							tranlsator.AddTranslation(ctx, value, res)
			except:
				pass
			self._data = dict(result)

	def _haskey(self, key):
		return key in self._data

	def __getattr__(self, key):
		result = self._data.get(key)
		if result is None:
			return '"%s.%s" undefined'%(self._name, key)
		return result

	def __repr__(self):
		return repr(self._data)

	def _xgettext(self):
		result = '\n'.join(['msgid ""', 'msgstr ""',
			      			'"Content-Type: text/plain; charset=UTF-8\\n"',
			      			'"Generated-By: dot15926\\n"',''])

		with open(self._path, 'r') as f:
			content = f.read()

			result += '\n'.join(['msgid "%s"\nmsgstr ""'%v for v in set([v[1] for v in re.findall(expr, content)])])
			for ctx, keys in re.findall(expr_contexts, content):
				result += '\n'.join(['msgctxt "%s"\nmsgid "%s"\nmsgstr ""'%(ctx, v) for v in set(re.findall(expr_keys, keys))])	

		return result

	def _dump_xgettext(self):
		with open('dot15926_%s.pot'%self._name, 'w') as f:
			f.write(self._xgettext())

class TextManager():

	def __init__(self):
		self._translator = Translator()
		self._modules = {}
		self._languages = [('en', language_codes['en'])]
		path = os.path.join(appdata.resources_dir, 'locale')
		for n in os.listdir(path):
			item_path = os.path.join(path, n)
			if os.path.isdir(item_path) and n in language_codes and n != 'en':
				self._languages.append((n, language_codes[n]))

		path = os.path.join(appdata.resources_dir)
		for n in os.listdir(path):
			item_path = os.path.join(path, n)
			name, ext = os.path.splitext(n)
			if  ext == '.tm':
				self._modules[name] = TextModule(item_path, self._translator)

	def __getattr__(self, key):
		result = self._modules.get(key)
		if result is None:
			return DummyTextModule(key)
		return result

	def _get_languages(self):
		return self._languages

class ResourcesStorage(object):
    def __init__(self):
		self._pixmaps = {}
		self._icons = {}
		path = os.path.join(appdata.resources_dir, 'images')
		for n in os.listdir(path):
			fpath = os.path.join(path, n)
			name, ext = os.path.splitext(n)
			if  ext == '.png':
				self._pixmaps[name] = QPixmap(fpath)
			elif ext == '.ico':
				self._icons[name] = QIcon(fpath)

    def GetPixmap(self, k):
    	return self._pixmaps[k]

    def GetIcon(self, k):
    	icon = self._icons.get(k)
    	if not icon:
    		imgs = k.split(';')
    		if len(imgs) > 1:
    			px = self._pixmaps[imgs[0]].copy()
    			painter = QPainter(px)
    			for i in range(1, len(imgs)):
    				painter.drawPixmap(0, 0, self._pixmaps[imgs[i]])
    			painter.end()
    			self._pixmaps[k] = px
    		else:
    			px = self._pixmaps[imgs[0]]
    		icon = QIcon(px)
    		icon.addPixmap(px, QIcon.Selected)
    		self._icons[k] = icon
    	return icon
