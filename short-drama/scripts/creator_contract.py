"""Print canonical stage templates without overwriting an existing project."""
import argparse
import json
from pathlib import Path

def main():
    contract=json.loads((Path(__file__).resolve().parents[1]/'references/document-contract.json').read_text(encoding='utf8'))
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('document',choices=list(contract['templates']))
    args=parser.parse_args()
    print('<!-- director-document:'+str(contract['version'])+' -->')
    print(contract['templates'][args.document],end='')

if __name__=='__main__':main()
