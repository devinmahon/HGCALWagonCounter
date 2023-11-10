import ast
import glob
import os
from sys import argv
from collections import Counter

def findCode(wagonDict,loc):

  for i,val in enumerate(wagonDict.values()):
    if loc in val:
      index = i

  return ''.join(str(i) for i in list(wagonDict.keys())[index])

def main():

  # Find the most recent file
  filesList = glob.glob('wagonDict/*txt')
  latestFile = max(filesList,key=os.path.getctime)
  print('Reading from most recent wagon dictionary file:',latestFile)
  with open(latestFile) as f:
    wagonDict = f.read()
  wagonDict = ast.literal_eval(wagonDict)

  if ',' in argv[1]: 

    arg = [int(i) for i in argv[1].split(',')] + [0]
    argPartner = [arg[0],arg[1],1]

    print(arg,'has code',findCode(wagonDict,arg))
    print(argPartner,'has code',findCode(wagonDict,argPartner))
    
  else: 

    arg = tuple([int(i) if i.isdigit() else i for i in list(argv[1])])

    isDash = 0
    code = []
    for i,x in enumerate(arg):
      if x == '-':
        isDash = 1
        continue
      if isDash:
        code.append(-1 * x)
        isDash = 0
      elif len(code) and isinstance(code[-1],str) and code[-1].isalpha() and isinstance(x,int) and not isinstance(code[-2],str):
        code.append(str(x))
      else:
        code.append(x)
    code = tuple(code)

    print('Wagon locations:')
    print('[layer,MB,wagon]:',sorted(wagonDict[code],key = lambda x: x[0]))

    # Print partners for LD
    if code[0] == 0:

      partnerCodes = []
      for loc in wagonDict[code]:
        partnerCodes.append(findCode(wagonDict,[loc[0],loc[1],int(not loc[2])]))

      print('Partner codes and counts:')
      print(Counter(partnerCodes))

if __name__ == '__main__':
  main()
