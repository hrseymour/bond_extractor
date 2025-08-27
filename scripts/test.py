import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import html_to_structured_text_bs4
from src.extractor import LLMBondExtractor

from config import config

file_path = "/home/harlan/repos/bond_extractor/output/AES/d905393d8k.htm"
with open(file_path, 'r') as f:
    text = f.read()

text = html_to_structured_text_bs4(text)
# print(text)

bondex = LLMBondExtractor(config['gemini']['api_key'], config['gemini']['model'])
bonds = bondex.extract_bonds_from_text(text, '8-K')
print('done!')