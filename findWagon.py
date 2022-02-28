import ast
import glob
import os
from sys import argv

def main():
 
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
    else:
      code.append(x)
  code = tuple(code)

  # Find the most recent file
  filesList = glob.glob('wagonDict/*txt')
  latestFile = max(filesList,key=os.path.getctime)
  print('Reading from most recent wagon dictionary file:',latestFile)
  with open(latestFile) as f:
    wagonDict = f.read()
  wagonDict = ast.literal_eval(wagonDict)
 
  print('[layer,MB,wagon]:',wagonDict[code])

if __name__ == '__main__':
  main()
