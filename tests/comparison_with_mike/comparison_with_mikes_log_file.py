#!/usr/bin/python2

# note: python3 pickle doesn't seem to like python2 pickles

import pickle
import gzip
import dieke
import numpy as np




try:
    FileNotFoundError
except NameError:
    #py2
    FileNotFoundError = IOError

EPS = 3e-5


#get sebastians matricies
sebmats = pickle.load(gzip.open('f11cf_matel.p.gz', 'rb'))

nf = 11  # 2 f-electrons means we're dealing with Er

# This object contains the matricies we need for the
# calculations all in the dictionary "FreeIonMatrix"
# or via the function "Cmatrix"



#cache my version of the matrix elements to make stuff faster
try:
    f = gzip.open('erbium.dat.gz', 'rb')
    print("Loading Er object")
    Er = pickle.load(f)
except FileNotFoundError:
    print("Making Er ojbect")
    Er = dieke.RareEarthIon(nf)
    pickle.dump(Er, gzip.open('erbium.dat.gz', 'wb'))

#Er = dieke.RareEarthIon(nf)
#pickle.dump(Er, gzip.open('erbium.dat.gz', 'wb'))


jevmats = Er.FreeIonMatrix
# Add the crystal field matricies to my dict
for k in [2, 4, 6]:
    for q in range(k+1):
        jevmats['C%d%d' % (k, q)] = Er.Cmatrix(k, q)


statedict = {}
for i in range(364):
    statedict[Er.LSJmJstateLabels[i]] = i


def mikelabel_to_jevon_label(statelabel):
    mult = statelabel[0]
    lchar = statelabel[1]
    sen = statelabel[2]
    if sen == ' ':
        sen = '1'
    twiceJ = statelabel[3:5]
    twicemJ = statelabel[5:8]
    jevonlabel = '%s %s%s %s/2 %s/2' % (sen, mult, lchar, twiceJ, twicemJ)
    return jevonlabel

# for mname in jevmats:
#     print('Matrix: %s'%(mname))
#     m = jevmats[mname]
#     for i in range(Er.numstates()):
#         for j in range(Er.numstates()):
#             if (np.abs(m[i, j]) > EPS):
#                 print("< %s | %s | %s > = %+.8e %+.8ej" % (Er.LSJmJstateLabels[i],
#                                                 mname,
#                                                 Er.LSJmJstateLabels[j],
#                                                           np.real(m[i,j]),np.imag(m[i,j])))

f =  open('375.cfit.log.txt', 'r')

# Read header
for k in range(26):
    f.readline()

mikemats = {}
count = 1


while True:
    ln = f.readline()
    if ln.strip()=='':
        ln = f.readline()
    if ln.strip()=='':
        ln = f.readline()
    if ln.strip().split()[0]=='NPARAMS':
        break
    (ctr, name, _, _) = ln.split()
    assert(int(ctr) == count)
    count += 1
    assert(f.readline().strip() == '')
    m = np.zeros((364, 364))
    matrixallread = False
    while not(matrixallread):
        matels = f.readline().strip().split('    ')
        for matel in matels:
            if matel == '':
                matrixallread = True
                break
            (expr, value) = matel.split('=')
            state1 = mikelabel_to_jevon_label(expr[1:9])
            state2 = mikelabel_to_jevon_label(expr[11:19])
            m[statedict[state1], statedict[state2]] = float(value)
            if state1 != state2:
                m[statedict[state2], statedict[state1]] = float(value)
    mikemats[name] = m


matnames = set(jevmats.keys())
matnames.update(mikemats.keys())
matnames = list(matnames)
matnames.sort()

for m in matnames:
    if not(m in jevmats):
        print("Jev missing %s"%(m))
    if not(m in mikemats):
        print("Mike missing %s"%(m))
    if (m in jevmats) and (m in mikemats):
        ms = np.matrix(mikemats[m])
        mj = np.matrix(jevmats[m])
        assert(np.linalg.norm(ms-ms.H) < EPS)
#        assert(np.linalg.norm(mj-mj.H) < EPS)
        normofdiff = np.linalg.norm(ms-mj)/np.linalg.norm(mj)
        if (normofdiff > EPS):
            # print("Matricies differ for %s, norm of diff = %g" % (m,
            #                                                      normofdiff))
            (evalss, _) = np.linalg.eig(ms)
            (evalsj, _) = np.linalg.eig(mj)
            #make sure evals are real
            assert(np.linalg.norm(np.imag(evalss)) < EPS)
            assert(np.linalg.norm(np.imag(evalsj)) < EPS)
            evalss = np.real(evalss)
            evalsj = np.real(evalsj)
            evalss.sort()
            evalsj.sort()
            normofdiff = np.linalg.norm(evalss-evalsj)/np.linalg.norm(evalsj)
            if (normofdiff > EPS):
                print("Eigenvalues differ for %s norm of diff = %g" % (m,
                                                                       normofdiff))
            else:
                pass#print("Eigenvalues agree for %s, norm of diff  < %g" %(m,
#                                                                      EPS))
        else:
            pass#print("!!!! Matricies agree for %s, norm of diff = %g !!!!" % (m,
 #                                                                normofdiff))


##  TESTING CMatrix C20
ckey = 'C20'
print('Testing %s' %ckey)
for ii in range(len(jevmats[ckey])):
    if not np.allclose(jevmats[ckey][ii],mikemats[ckey][ii]):
            print('False for row %s' %(ii))


# Scanning row 187
rowscan = 186
for ii in range(len(jevmats[ckey])):
    if not np.allclose(jevmats[ckey][rowscan,ii],mikemats[ckey][rowscan,ii]):
            print('False for %s, %s' %(rowscan, ii))

# Testing Hermitian stuff
ckeys = ['C20', 'C21', 'C22', 'C40', 'C41', 'C42', 'C43', 'C44', 'C60', 'C61', 'C62', 'C63', 'C64', 'C65', 'C66']  
for ckey in ckeys:
    mike_test = np.matrix(mikemats[ckey])
    if np.linalg.norm(herm_test-herm_test.H) < EPS:
        print("Mikes %s is Hermitian"% ckey)
    else:
        print("Mikes %s is not Hermitian"% ckey)



# Read in a a set of crystal field parameters from Er:LaF3
# dieke reads these from (incomplete) carnall89params.xls
cfparams = dieke.readLaF3params(nf)

#change most of the parameters to those in eryso_cf paper
#leave some from carnall89

cfparams['E0'] = 35503.5 #this is ignored
cfparams['ZETA'] = 2362.9
cfparams['F2'] = 96029.6
cfparams['F4'] = 67670.6
cfparams['F6'] = 53167.1

cfparams['B20'] = -149.8
cfparams['B21'] = 420.6+396.0j
cfparams['B22'] = -228.5+27.6j
cfparams['B40'] = 1131.2
cfparams['B41'] = 985.7+34.2j
cfparams['B42'] = 296.8+145.0j
cfparams['B43'] = -402.3-381.7j
cfparams['B44'] = -282.3+1114.3j
cfparams['B60'] = -263.2
cfparams['B61'] = 111.9+222.9j
cfparams['B62'] = 124.7+195.9j
cfparams['B63'] = -97.9+139.7j
cfparams['B64'] = -93.7-145.0j
cfparams['B65'] = 13.9+109.5j
cfparams['B66'] = 3.0-108.6j
cfparams['A'] = 0.005466 #this is ignored
cfparams['Q'] = 0.0716 #this is ignored
