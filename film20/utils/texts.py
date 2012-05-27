# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Filmaster - a social web network and recommendation engine
# Copyright (c) 2009 Filmaster (Borys Musielak, Adam Zielinski).
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------

"""
_ASCII_REPLACEMENTS = {}
def add(codes, char, upper=True):
	#nonlocal _ASCII_REPLACEMENTS
    for i in codes:
        c = unichr(i)
        _ASCII_REPLACEMENTS[c] = char
        if upper and c.upper()<>c:
            if __name__ == "__main__":
                if c.upper().lower() != c:
                    print "%s.upper()==%s; %s.upper().lower()==%s" % (c, c.upper(), c.upper().lower())
            _ASCII_REPLACEMENTS[c.upper()] = char.upper()
            

def set(code, char, upper=True):
    #nonlocal _ASCII_REPLACEMENTS
    c = unichr(code)
    _ASCII_REPLACEMENTS[c] = char
    if upper and c.upper()<>c:
        if __name__=="__main__":
            if c.upper().lower() != c:
                print "%s.upper()==%s; %s.upper().lower()==%s" % (c, c.upper(), c.upper().lower())	
        _ASCII_REPLACEMENTS[c.upper()] = char.upper()
	

DICT = _ASCII_REPLACEMENTS
#Latin-1
#set(138, u's')
#set(140, u'OE')
#set(142, u'Z')
add(range(224, 230), u'a')
set(230, u'ae')
set(231, u'c')
add(range(232, 236), u'e')
add(range(236, 240), u'i')
set(241, u'n')
add(range(242, 247), u'o')
set(248, u'o')
add(range(249, 253), u'u')
set(255, u'y')



#Latin Extended-A
add(range(257, 262, 2), u'a')
add(range(263, 270, 2), u'c')
add([271, 273], u'd')
add(range(275, 284, 2), u'e')
add(range(285, 292, 2), u'g')
add([293, 295], u'h')
add(range(297, 304, 2), u'i')
set(304, u'I', False)
set(305, u'i', False)
set(307, u'ij')
set(309, u'j')
add([311, 312], u'k')
add(range(314, 323, 2), u'l')
add(range(324, 332, 2), u'n')
add(range(333, 338, 2), u'o')
set(338, u'oe')
add(range(341, 346, 2), u'r')
add(range(347, 354, 2), u's')
add(range(355, 360, 2), u't')
add(range(361, 372, 2), u'u')
set(373, u'w')
set(375, u'y')
set(376, u'Y')
add(range(378, 383, 2), u'z')
set(383, u's', False)




del add
del set
"""

# http://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-in-a-python-unicode-string/518232#518232
import unicodedata
def strip_accents(s): 
    return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))
    
def concatenate_words(words, separator=u' '):
    return separator.join([word for word in words if word !=None])

# default unicode character mapping ( you may not see some chars, leave as is )
ASCII_REPLACEMENTS = {u'À': 'A', u'�?': 'A', u'Â': 'A', u'Ã': 'A', u'Ä': 'Aa', u'Å': 'A', u'Æ': 'Ae', u'Ā': 'A', u'Ą': 'A', u'Ă': 'A', u'Ç': 'C', u'Ć': 'C', u'Č': 'C', u'Ĉ': 'C', u'Ċ': 'C', u'Ď': 'D', u'�?': 'D', u'È': 'E', u'É': 'E', u'Ê': 'E', u'Ë': 'E', u'Ē': 'E', u'Ę': 'E', u'Ě': 'E', u'Ĕ': 'E', u'Ė': 'E', u'Ĝ': 'G', u'Ğ': 'G', u'Ġ': 'G', u'Ģ': 'G', u'Ĥ': 'H', u'Ħ': 'H', u'Ì': 'I', u'�?': 'I', u'Î': 'I', u'�?': 'I', u'Ī': 'I', u'Ĩ': 'I', u'Ĭ': 'I', u'Į': 'I', u'İ': 'I', u'Ĳ': 'Ij', u'Ĵ': 'J', u'Ķ': 'K', u'Ľ': 'L', u'Ĺ': 'L', u'Ļ': 'L', u'Ŀ': 'L', u'�?': 'L', u'Ñ': 'N', u'Ń': 'N', u'Ň': 'N', u'Ņ': 'N', u'Ŋ': 'N', u'Ò': 'O', u'Ó': 'O', u'Ô': 'O', u'Õ': 'O', u'Ö': 'Oe', u'Ø': 'O', u'Ō': 'O', u'�?': 'O', u'Ŏ': 'O', u'Œ': 'Oe', u'Ŕ': 'R', u'Ř': 'R', u'Ŗ': 'R', u'Ś': 'S', u'Ş': 'S', u'Ŝ': 'S', u'Ș': 'S', u'Š': 'S', u'Ť': 'T', u'Ţ': 'T', u'Ŧ': 'T', u'Ț': 'T', u'Ù': 'U', u'Ú': 'U', u'Û': 'U', u'Ü': 'Ue', u'Ū': 'U', u'Ů': 'U', u'Ű': 'U', u'Ŭ': 'U', u'Ũ': 'U', u'Ų': 'U', u'Ŵ': 'W', u'Ŷ': 'Y', u'Ÿ': 'Y', u'�?': 'Y', u'Ź': 'Z', u'Ż': 'Z', u'Ž': 'Z', u'à': 'a', u'á': 'a', u'â': 'a', u'ã': 'a', u'ä': 'aa', u'�?': 'a', u'ą': 'a', u'ă': 'a', u'å': 'a', u'æ': 'ae', u'ç': 'c', u'ć': 'c', u'�?': 'c', u'ĉ': 'c', u'ċ': 'c', u'�?': 'd', u'đ': 'd', u'è': 'e', u'é': 'e', u'ê': 'e', u'ë': 'e', u'ē': 'e', u'ę': 'e', u'ě': 'e', u'ĕ': 'e', u'ė': 'e', u'ƒ': 'f', u'�?': 'g', u'ğ': 'g', u'ġ': 'g', u'ģ': 'g', u'ĥ': 'h', u'ħ': 'h', u'ì': 'i', u'í': 'i', u'î': 'i', u'ï': 'i', u'ī': 'i', u'ĩ': 'i', u'ĭ': 'i', u'į': 'i', u'ı': 'i', u'ĳ': 'ij', u'ĵ': 'j', u'ķ': 'k', u'ĸ': 'k', u'ł': 'l', u'ľ': 'l', u'ĺ': 'l', u'ļ': 'l', u'ŀ': 'l', u'ñ': 'n', u'ń': 'n', u'ň': 'n', u'ņ': 'n', u'ŉ': 'n', u'ŋ': 'n', u'ò': 'o', u'ó': 'o', u'ô': 'o', u'õ': 'o', u'ö': 'oe', u'ø': 'o', u'�?': 'o', u'ő': 'o', u'�?': 'o', u'œ': 'oe', u'ŕ': 'r', u'ř': 'r', u'ŗ': 'r', u'ś': 's', u'š': 's', u'ť': 't', u'ù': 'u', u'ú': 'u', u'û': 'u', u'ü': 'ue', u'ū': 'u', u'ů': 'u', u'ű': 'u', u'ŭ': 'u', u'ũ': 'u', u'ų': 'u', u'ŵ': 'w', u'ÿ': 'y', u'ý': 'y', u'ŷ': 'y', u'ż': 'z', u'ź': 'z', u'ž': 'z', u'ß': 'ss', u'ſ': 'ss', u'Α': 'A', u'Ά': 'A', u'Ἀ': 'A', u'Ἁ': 'A', u'Ἂ': 'A', u'Ἃ': 'A', u'Ἄ': 'A', u'�?': 'A', u'Ἆ': 'A', u'�?': 'A', u'ᾈ': 'A', u'ᾉ': 'A', u'ᾊ': 'A', u'ᾋ': 'A', u'ᾌ': 'A', u'�?': 'A', u'ᾎ': 'A', u'�?': 'A', u'Ᾰ': 'A', u'Ᾱ': 'A', u'Ὰ': 'A', u'Ά': 'A', u'ᾼ': 'A', u'Β': 'B', u'Γ': 'G', u'Δ': 'D', u'Ε': 'E', u'Έ': 'E', u'Ἐ': 'E', u'Ἑ': 'E', u'Ἒ': 'E', u'Ἓ': 'E', u'Ἔ': 'E', u'�?': 'E', u'Έ': 'E', u'Ὲ': 'E', u'Ζ': 'Z', u'Η': 'I', u'Ή': 'I', u'Ἠ': 'I', u'Ἡ': 'I', u'Ἢ': 'I', u'Ἣ': 'I', u'Ἤ': 'I', u'Ἥ': 'I', u'Ἦ': 'I', u'Ἧ': 'I', u'ᾘ': 'I', u'ᾙ': 'I', u'ᾚ': 'I', u'ᾛ': 'I', u'ᾜ': 'I', u'�?': 'I', u'ᾞ': 'I', u'ᾟ': 'I', u'Ὴ': 'I', u'Ή': 'I', u'ῌ': 'I', u'Θ': 'TH', u'Ι': 'I', u'Ί': 'I', u'Ϊ': 'I', u'Ἰ': 'I', u'Ἱ': 'I', u'Ἲ': 'I', u'Ἳ': 'I', u'Ἴ': 'I', u'Ἵ': 'I', u'Ἶ': 'I', u'Ἷ': 'I', u'Ῐ': 'I', u'Ῑ': 'I', u'Ὶ': 'I', u'Ί': 'I', u'Κ': 'K', u'Λ': 'L', u'Μ': 'M', u'�?': 'N', u'Ξ': 'Ks', u'Ο': 'O', u'Ό': 'O', u'Ὀ': 'O', u'Ὁ': 'O', u'Ὂ': 'O', u'Ὃ': 'O', u'Ὄ': 'O', u'�?': 'O', u'Ὸ': 'O', u'Ό': 'O', u'Π': 'P', u'Ρ': 'R', u'Ῥ': 'R', u'Σ': 'S', u'Τ': 'T', u'Υ': 'Y', u'Ύ': 'Y', u'Ϋ': 'Y', u'Ὑ': 'Y', u'Ὓ': 'Y', u'�?': 'Y', u'Ὗ': 'Y', u'Ῠ': 'Y', u'Ῡ': 'Y', u'Ὺ': 'Y', u'Ύ': 'Y', u'Φ': 'F', u'Χ': 'X', u'Ψ': 'Ps', u'Ω': 'O', u'�?': 'O', u'Ὠ': 'O', u'Ὡ': 'O', u'Ὢ': 'O', u'Ὣ': 'O', u'Ὤ': 'O', u'Ὥ': 'O', u'Ὦ': 'O', u'Ὧ': 'O', u'ᾨ': 'O', u'ᾩ': 'O', u'ᾪ': 'O', u'ᾫ': 'O', u'ᾬ': 'O', u'ᾭ': 'O', u'ᾮ': 'O', u'ᾯ': 'O', u'Ὼ': 'O', u'Ώ': 'O', u'ῼ': 'O', u'α': 'a', u'ά': 'a', u'ἀ': 'a', u'�?': 'a', u'ἂ': 'a', u'ἃ': 'a', u'ἄ': 'a', u'ἅ': 'a', u'ἆ': 'a', u'ἇ': 'a', u'ᾀ': 'a', u'�?': 'a', u'ᾂ': 'a', u'ᾃ': 'a', u'ᾄ': 'a', u'ᾅ': 'a', u'ᾆ': 'a', u'ᾇ': 'a', u'ὰ': 'a', u'ά': 'a', u'ᾰ': 'a', u'ᾱ': 'a', u'ᾲ': 'a', u'ᾳ': 'a', u'ᾴ': 'a', u'ᾶ': 'a', u'ᾷ': 'a', u'β': 'b', u'γ': 'g', u'δ': 'd', u'ε': 'e', u'έ': 'e', u'�?': 'e', u'ἑ': 'e', u'ἒ': 'e', u'ἓ': 'e', u'ἔ': 'e', u'ἕ': 'e', u'ὲ': 'e', u'έ': 'e', u'ζ': 'z', u'η': 'i', u'ή': 'i', u'ἠ': 'i', u'ἡ': 'i', u'ἢ': 'i', u'ἣ': 'i', u'ἤ': 'i', u'ἥ': 'i', u'ἦ': 'i', u'ἧ': 'i', u'�?': 'i', u'ᾑ': 'i', u'ᾒ': 'i', u'ᾓ': 'i', u'ᾔ': 'i', u'ᾕ': 'i', u'ᾖ': 'i', u'ᾗ': 'i', u'ὴ': 'i', u'ή': 'i', u'ῂ': 'i', u'ῃ': 'i', u'ῄ': 'i', u'ῆ': 'i', u'ῇ': 'i', u'θ': 'th', u'ι': 'i', u'ί': 'i', u'ϊ': 'i', u'�?': 'i', u'ἰ': 'i', u'ἱ': 'i', u'ἲ': 'i', u'ἳ': 'i', u'ἴ': 'i', u'ἵ': 'i', u'ἶ': 'i', u'ἷ': 'i', u'ὶ': 'i', u'ί': 'i', u'�?': 'i', u'ῑ': 'i', u'ῒ': 'i', u'ΐ': 'i', u'ῖ': 'i', u'ῗ': 'i', u'κ': 'k', u'λ': 'l', u'μ': 'm', u'ν': 'n', u'ξ': 'ks', u'ο': 'o', u'ό': 'o', u'ὀ': 'o', u'�?': 'o', u'ὂ': 'o', u'ὃ': 'o', u'ὄ': 'o', u'ὅ': 'o', u'ὸ': 'o', u'ό': 'o', u'π': 'p', u'�?': 'r', u'ῤ': 'r', u'ῥ': 'r', u'σ': 's', u'ς': 's', u'τ': 't', u'υ': 'y', u'�?': 'y', u'ϋ': 'y', u'ΰ': 'y', u'�?': 'y', u'ὑ': 'y', u'ὒ': 'y', u'ὓ': 'y', u'ὔ': 'y', u'ὕ': 'y', u'ὖ': 'y', u'ὗ': 'y', u'ὺ': 'y', u'ύ': 'y', u'ῠ': 'y', u'ῡ': 'y', u'ῢ': 'y', u'ΰ': 'y', u'ῦ': 'y', u'ῧ': 'y', u'φ': 'f', u'χ': 'x', u'ψ': 'ps', u'ω': 'o', u'ώ': 'o', u'ὠ': 'o', u'ὡ': 'o', u'ὢ': 'o', u'ὣ': 'o', u'ὤ': 'o', u'ὥ': 'o', u'ὦ': 'o', u'ὧ': 'o', u'ᾠ': 'o', u'ᾡ': 'o', u'ᾢ': 'o', u'ᾣ': 'o', u'ᾤ': 'o', u'ᾥ': 'o', u'ᾦ': 'o', u'ᾧ': 'o', u'ὼ': 'o', u'ώ': 'o', u'ῲ': 'o', u'ῳ': 'o', u'ῴ': 'o', u'ῶ': 'o', u'ῷ': 'o', u'¨': '', u'΅': '', u'᾿': '', u'῾': '', u'�?': '', u'�?': '', u'῎': '', u'῞': '', u'�?': '', u'῟': '', u'῀': '', u'�?': '', u'΄': '', u'΅': '', u'`': '', u'῭': '', u'ͺ': '', u'᾽': '', u'�?': 'A', u'Б': 'B', u'В': 'W', u'Г': 'G', u'Д': 'D', u'Е': 'E', u'�?': 'E', u'Ж': 'Z', u'З': 'Z', u'И': 'I', u'Й': 'J', u'К': 'K', u'Л': 'L', u'М': 'M', u'�?': 'N', u'О': 'O', u'П': 'P', u'Р': 'R', u'С': 'S', u'Т': 'T', u'У': 'U', u'Ф': 'F', u'Х': 'H', u'Ц': 'C', u'Ч': 'Cz', u'Ш': 'Sz', u'Щ': 'Szcz', u'Ы': 'Y', u'Э': 'E', u'Ю': 'Ju', u'Я': 'Ja', u'а': 'a', u'б': 'b', u'в': 'w', u'г': 'g', u'д': 'd', u'е': 'e', u'ё': 'e', u'ж': 'z', u'з': 'z', u'и': 'i', u'й': 'j', u'к': 'k', u'л': 'l', u'м': 'm', u'н': 'n', u'о': 'o', u'п': 'p', u'р': 'r', u'�?': 's', u'т': 't', u'у': 'u', u'ф': 'f', u'х': 'h', u'ц': 'c', u'ч': 'cz', u'ш': 'sz', u'щ': 'szcz', u'ы': 'y', u'�?': 'e', u'ю': 'ju', u'�?': 'ja', u'Ъ': '', u'ъ': '', u'Ь': '', u'ь': '', u'ð': 'd', u'�?': 'D', u'þ': 'Th', u'Þ': 'th', 
            u'�?': 'a', u'ბ': 'b', u'გ': 'g', u'დ': 'd', u'ე': 'e', u'ვ': 'v', u'ზ': 'z', u'თ': 't', u'ი': 'i', u'კ': 'k', u'ლ': 'l', u'მ': 'm', u'ნ': 'n', u'�?': 'o', u'პ': 'p', u'ჟ': 'zh', u'რ': 'r', u'ს': 's', u'ტ': 't', u'უ': 'u', u'ფ': 'p', u'ქ': 'k', u'ღ': 'gh', u'ყ': 'q', u'შ': 'sh', u'ჩ': 'ch', u'ც': 'ts', u'ძ': 'dz', u'წ': 'ts', u'ჭ': 'ch', u'ხ': 'kh', u'ჯ': 'j', u'ჰ': 'h', u'·': '-', u'³': '3', u'½': '1/2', u'¡': '!', u'Á':'A', u'¢':'c', u'ª':'a', u'±':'+', u'°':'o', u'Ł': 'L' }

def deogonkify(ustr):
    """Replaces all recognized national characters with their ascii counterparts"""
    sb = None
    for i in range(0, len(ustr)):				
        if ustr[i] in ASCII_REPLACEMENTS:
            if sb == None:
                sb = [ ustr[j] for j in range(0, len(ustr)) ]
            sb[i] = ASCII_REPLACEMENTS[ustr[i]]
    if sb == None:
        return ustr
    return u''.join(sb).encode('ascii', 'ignore')
            

REPLACED_ROMAN_NUMERALS = { 'II' : '2', 'III' : '3', 'IV' : '4', 'V' : '5', 'VI' : '6', 'VII' : '7', 'VIII' : '8', 'IX' : '9' }

def roman_to_arabic(word):
    upword = word.upper()
    if upword in REPLACED_ROMAN_NUMERALS:
        return REPLACED_ROMAN_NUMERALS[upword]
    return word

POLISH_WORD_NUMERALS = {'jeden' : '1', 'dwa' : '2', 'trzy' : '3', 'cztery' : '4', 'pięć' : '5', 
    'sześć' : '6', 'siedem' : '7', 'osiem' : '8', 'dziewięć' : '9', 'dziesięć' : '10', u'pół' : '1 2'}
ENGLISH_WORD_NUMERALS = {'one' : '1', 'two': '2',  'three' : '3', 'four' : '4', 'five' : '5', 
    'six' : '6', 'seven' : '7', 'eight' : '8', 'nine' : '9', 'ten' : '10', 'half' : '1 2' }
#CHARACTER_NUMERALS = { u'\xab' : '1 2' , u'\xac' : '1 4', u'\xf3' : '3 4'}
CHARACTER_NUMERALS = { u'\xbd' : '1 2' }
    
def numeral_to_digit(word):
    lowerword = word.lower()
    if lowerword in POLISH_WORD_NUMERALS:
        return POLISH_WORD_NUMERALS[lowerword]
    if lowerword in ENGLISH_WORD_NUMERALS:
        return ENGLISH_WORD_NUMERALS[lowerword]
    if lowerword in CHARACTER_NUMERALS:
        return CHARACTER_NUMERALS[lowerword]
    return word
      
POPULAR_WORDS = [u'the', u'les', u'die', u'das', u'der',    
    u'and', u'or', u'of', u'at',
    u'il', u'el', u'le', u'la',  u'de'    
]

PUNCTUATION = u"~`!#$%^&*(),.<>_-+={}[]\"':;|\\/?|" #'@' is not included, as it's sometimes used as 'a'
WORD_BOUNDARIES = PUNCTUATION+" \t"

def get_word_list(ustr, minlength=1, exclude_list=POPULAR_WORDS):
    res=[]
    start=0
    for i in range(start, len(ustr)):
        c = ustr[i]
        try:
            if c in WORD_BOUNDARIES:
                word = roman_to_arabic(ustr[start:i])
                word = numeral_to_digit(word)
                if word.isdigit() or (len(word)>minlength and word not in exclude_list):
                    res.append(word)
                start = i+1
        except TypeError:        
            print "TypeError! %s" % type(c)
            print "char: %s" % c
            print "string: %s" % ustr
    word = roman_to_arabic(ustr[start:])
    word = numeral_to_digit(word)
    if word.isdigit() or (len(word)>minlength and word not in exclude_list):
        res.append(word)
    return res
    
def get_normalized_word_list(ustr, minlength=1, exclude_list=POPULAR_WORDS):
    return [deogonkify(w) for w in get_word_list(ustr.lower(), minlength, exclude_list)]

def normalized_text(ustr, minlength=1, exclude_list=POPULAR_WORDS):
    return u' '.join(get_normalized_word_list(ustr, minlength, exclude_list))
    
def get_normalized_suffixes(ustr, minlength=1, exclude_list=POPULAR_WORDS):
    words = get_normalized_word_list(ustr, minlength, exclude_list)
    return [ u' '.join(words[i:]) for i in range(0, len(words)) ]
    
def get_normalized_words_roots(words):
    return [ word_root(w) for w in words ]
    
def get_words_roots(words):
    return [ word_root_normalized(w) for w in words ]
    
def get_words_letters(words):
    return [ word_letters(w) for w in words ]
    
def unprefixed_text(ustr, exclude_list=POPULAR_WORDS):
    """
    Removes articles such as 'the', and 'a' in common languages 
    if they are at the beginning of the string
    """
    prefix = ustr[0:5].lower()
    for word in exclude_list:
        if prefix.startswith(word+" "):
            return ustr[len(word)+1:]
    return ustr

def word_root_normalized(word):
    """Removes lower vowels and spaces from the string"""
    sb = []
    for i in range(0, len(word)):
        if not word[i] in "aoeiuy " :
            sb.append(word[i])
    return u''.join(sb)
	
text_root_normalized = word_root_normalized
    
		
def word_root(ustr):    
    """Normalized version of the string with vowels and punctuation removed"""
    return word_root_normalized(normalized_text(ustr))

text_root = word_root
    
def word_letters(word):
    letters = [ l for l in word ]
    letters.sort()
    return u''.join(letters)
    
def text_letters(ustr):
    return u' '.join(get_words_letters(get_word_list(ustr)))

def levenshtein(s1, s2):
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if not s1:
        return len(s2)
 
    previous_row = xrange(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
            deletions = current_row[j] + 1       # than s2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
 
    return previous_row[-1]
	
