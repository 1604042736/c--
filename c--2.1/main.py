from Compiler import *
import sys
import argparse

parser = argparse.ArgumentParser(description='c--2.1')
parser.add_argument("filename")
parser.add_argument("-v", "--version", help="显示版本信息", action='store_true')
args=parser.parse_args()

def main():
    if args.version:
        print("c-- 2.1")
        return
    filename = args.filename
    compile(filename)

if __name__=='__main__':
    main()