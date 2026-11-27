"""Read and patch an existing creative entry with a source fingerprint."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from creator_document import CONTRACT, check_headings, patch_fields

def locate(root, document):
    root=Path(root).resolve()
    if (root/'.short-drama/state/project.sqlite').exists() or (root/'.short-drama/managed-source.json').exists():
        raise ValueError('这是导演台管理项目，请使用导演台 cli.py entry-read / entry-update')
    path=(root/document).resolve()
    if not path.is_relative_to(root) or path.name not in CONTRACT['documents']:
        raise ValueError('请选择项目内的五份创作文档')
    return path

def section(text, entry):
    headings=list(re.finditer(r'^##[ \t]+([^\r\n]+)',text,re.M))
    found=[]
    for i,heading in enumerate(headings):
        title=heading[1].strip()
        if title==entry or title.split(' · ',1)[0].split(' ',1)[0]==entry:
            start=heading.end()
            end=headings[i+1].start() if i+1<len(headings) else len(text)
            found.append((title,start,end))
    if len(found)!=1:raise ValueError('条目不存在或不唯一：'+entry)
    return found[0]

def read_entry(root,document,entry):
    path=locate(root,document);raw=path.read_bytes();text=raw.decode('utf-8-sig')
    check_headings(path.name,text)
    title,start,end=section(text,entry)
    return {'entry':entry,'title':title,'revision':hashlib.sha256(raw).hexdigest(),'text':text[start:end].strip()}

def update_entry(root,document,entry,expected,patch):
    if not expected:raise ValueError('修改需要读取时返回的 revision')
    if not isinstance(patch,dict) or set(patch) not in ({'text'},{'fields'}):
        raise ValueError('提交 text 或 fields 中的一种')
    path=locate(root,document);lock=path.with_name('.'+path.name+'.edit-lock')
    fd=None;temp=None
    try:
        fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('文档已更新，请重新读取后修改；本次未写入')
        text=raw.decode('utf-8-sig');title,start,end=section(text,entry);body=text[start:end]
        if 'fields' in patch:
            replacement=patch_fields(body,patch['fields'],shot=path.name=='分镜.md' and entry.startswith('SHOT-'))
        else:
            value=patch['text']
            if not isinstance(value,str) or re.search(r'^##\s+',value,re.M):raise ValueError('text 应为当前条目正文')
            newline='\r\n' if '\r\n' in text else '\n'
            replacement=newline+value.replace('\r\n','\n').replace('\n',newline).strip()+newline+newline
        updated=text[:start]+replacement+text[end:];check_headings(path.name,updated)
        data=(b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b'')+updated.encode('utf8')
        handle,temp=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
        with os.fdopen(handle,'wb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
        if path.read_bytes()!=raw:raise ValueError('文档在修改期间发生变化，请重新读取')
        os.replace(temp,path);temp=None
        return read_entry(root,document,entry)
    except FileExistsError as error:
        raise ValueError('另一个条目修改正在执行，请稍后重试') from error
    finally:
        if temp:Path(temp).unlink(missing_ok=True)
        if fd is not None:os.close(fd);lock.unlink(missing_ok=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['read','update']);parser.add_argument('project')
    parser.add_argument('--document',required=True);parser.add_argument('--entry',required=True)
    parser.add_argument('--expected');args=parser.parse_args()
    try:
        result=read_entry(args.project,args.document,args.entry) if args.command=='read' else update_entry(args.project,args.document,args.entry,args.expected,json.load(sys.stdin))
        print(json.dumps({'ok':True,'data':result},ensure_ascii=False));return 0
    except (ValueError,OSError) as error:
        print(json.dumps({'ok':False,'message':str(error)},ensure_ascii=False));return 2

if __name__=='__main__':raise SystemExit(main())
