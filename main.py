from math import cos as cos
from math import acos as acos
from math import sqrt as sqrt
from math import pi as pi
import json
import matplotlib.pyplot as plt
import os

################################################
##########  SFS MANEUVER CALCULATOR   ##########
################################################

from dotenv import dotenv_values
paths=dotenv_values('.env')
maneuver_path=paths['path_maneuver']
planet_pack_path=paths['path_planetpack']
plot_maneuver=True
'''
If you want to paste the path directly:
maneuver_path=\path\to\your\maneuver.txt
planet_pack_path=\path\to\your\planetpack
'''

################################################
################################################
################################################

planet_pack_path=planet_pack_path+'\\Planet Data'

deg2rad=pi/180

def planet_data_miner(planetpath):
    planets=os.listdir(planetpath)
    bodies={}

    for i in planets:
        #print(i)
        # g,r,atmoh,parent,sma,soim,e,argP
        # calculated: A,P,SOI,GM,rLO
        with open(planetpath+'\\'+i,'r+') as f:
            d=json.load(f)

            #g,r,twrp. calculated:GM
            g=d['BASE_DATA']['gravity']
            r=d['BASE_DATA']['radius']
            gm=g*r**2
            twrp=d['BASE_DATA']['timewarpHeight']
            tempdict={'g':g,'r':r ,'GM':gm}
            if 'ATMOSPHERE_PHYSICS_DATA' in d.keys():
                #atmospheric rLO
                atmoh=d['ATMOSPHERE_PHYSICS_DATA']['height']
                rLO=r+atmoh+2000
                tempdict.update({'atmoh':atmoh})
            else:
                #rLO for nonatmospheric
                rLO=r+twrp+2000
            tempdict.update({'rLO':rLO})
            if 'ORBIT_DATA' in d.keys():
                #not the sun
                #noncalculated: sma, e, soim, argP
                #calculated: A,P,SOI
                parent=d['ORBIT_DATA']['parent']
                sma=d['ORBIT_DATA']['semiMajorAxis']
                e=d['ORBIT_DATA']['eccentricity']
                soim=d['ORBIT_DATA']['multiplierSOI']
                argP=d['ORBIT_DATA']['argumentOfPeriapsis']
                tempdict.update({'parent':parent})
                tempdict.update({'sma':sma})
                tempdict.update({'e':e})
                tempdict.update({'soim':soim})
                tempdict.update({'argP':argP})
                A=sma*(1+e)
                P=sma*(1-e)
                tempdict.update({'A':A, 'P':P})
                if parent == 'Sun':
                    tempdict.update({'tier':2})
                else:
                    tempdict.update({'tier':3})
            else:
                #the sun
                tempdict.update({'tier':1})
        f.close()
        bodies.update({str(i[:-4]):tempdict})

    for i in bodies:
        if i != 'Sun':
            sma=bodies[i]['sma']
            gm1=bodies[i]['GM']
            gm2=bodies[bodies[i]['parent']]['GM']
            m=bodies[i]['soim']
            SOI=sma*(gm1/gm2)**.4*m
            bodies[str(i)].update({'soi':SOI})
    return bodies

def getorbit(A,P,argPd,parent,ref):
    if A=='LO':
        A=ref['rLO']
    if P=='LO':
        P=ref['rLO']
    if 'h' in str(A):
        A=float(A[:-1])+ref['r']
    if 'h' in str(P):
        P=float(P[:-1])+ref['r']
    if A=='SOI':
        A=ref['soi']
    if P=='SOI':
        P=ref['soi']
    A=float(A);P=float(P)
    sma=(A+P)/2
    e=((A-P)/sma)/2
    argPd=float(argPd)*deg2rad
    return orbit(sma,e,argPd,parent)
class orbit:
    def __init__(self,a,e,argP,parent):
        self.a=a
        self.l=a*(1-e**2)
        self.e=e
        self.argP=argP
        self.parent=parent
    def getP(self):
        return self.l/(1+self.e)
    def getA(self):
        return self.l/(1-self.e)
    def getRtheta(self,theta):
        return self.l/(1+self.e*cos(theta-self.argP))
    def getVtheta(self,theta,mu):
        spcE=mu*((self.e)**2-1)/(2*self.l)
        Rtheta=self.getRtheta(theta)
        return sqrt(2*(spcE+mu/Rtheta))
    def getVbyR(self,R,mu):
        if self.getP() <= R <= self.getA():
            return sqrt(mu*(2/R-1/self.a))
        else: return False

def getRkmh(r,ref):
    #converts any r to height from surface
    if r=='LO':
        r=ref['rLO']-ref['r']
    elif r=='SOI':
        r=ref['soi']-ref['r']
    elif 'h' in str(r):
        r=float(r[:-1])
    else:
        r=float(r)-ref['r']
    r=float(r)/1000
    return str(r)

def marg(dv,f):
    if '+' in f: return dv+float(f[+1:])
    else: return dv*float(f)

def HohmannCalc(orbit1, orbit2, argstart,hohmann,argend):
    #Credits to Altair
    l1=orbit1.l; e1=orbit1.e; phi1=orbit1.argP
    l2=orbit2.l; e2=orbit2.e; phi2=orbit2.argP

    r1=orbit1.getRtheta(argstart);
    r2=orbit2.getRtheta(argstart);

    X=(1-e1*e2*cos(phi2-phi1))/(l1*l2)-.5*((1-e1**2)/l1**2+(1-e2**2)/l2**2)

    if (not(X<0.0) and abs(r1-r2)/min(r1,r2) < 0.0001):
        return False

    l3=1/(1/l1+X*r1*r2/(r2-r1))

    if l3<0:
        return False

    e3=l3*sqrt((1/l3-1/r1)**2+(e1/l1)**2-(1/l1-1/r1)**2)

    trueAno=argstart-phi1

    while trueAno>pi:trueAno-=2*pi
    while trueAno<-pi:trueAno+=2*pi

    trueAnosign=1;
    if trueAno<0:trueAnosign=-1

    if(1+e3>1):
        cosval=(l3/r1-1)/e3;
        if cosval<-1:cosval=-1
        if cosval>1:cosval=1
        phi3=argstart-trueAnosign*acos(cosval)

    a3=l3/(1-e3**2)
    hohmann.a=a3
    hohmann.l=a3*(1-e3**2)
    hohmann.e=e3
    hohmann.argP=phi3%(2*pi)

    r4=2*(1/l3-1/l2)/((1-e3**2)/l3**2-(1-e2**2)/l2**2)
    deltaPhi=phi3-phi2

    while deltaPhi>pi:deltaPhi-=2*pi
    while deltaPhi<-pi:deltaPhi+=2*pi

    sign2=1
    if deltaPhi<0:sign2=-sign2
    if 1/l2-1/l3<0:sign2=-sign2

    if 1+e3>1:
        cosval2=(l3/r4-1)/e3
        if cosval2>1:cosval2=1
        if cosval2<-1:cosval2=-1
        argend=(phi3+sign2*acos(cosval2))%(2*pi)
    elif 1+e2>1:
        cosval2=(l2/r4-1)/e2
        if cosval2>1:cosval2=1
        if cosval2<-1:cosval2=-1
        argend=(phi2+sign2*acos(cosval2))%(2*pi)
    return [hohmann,argend]

def calculationType(body1,body2,manType):
    #criterion mess up 2025 03 31
    manType=manType*100
    if manType//100 == 2: print('Escape Calculation. ')
    elif manType//100 == 3: print('Capture Calculation. ')
    elif manType//100 == 4: print('Full Hohmann Calculation. ')
    if body1==body2:
        print('Transfer Type 1: Orbit within a same body')
        return 1+manType #ss
    elif body[body1]['tier']==2 and body[body2]['tier']==2 and \
         body[body1]['parent']==body[body2]['parent'] and body1!=body2:
        print('Transfer Type 2: Planet to another planet')
        return 2+manType #pp'
    elif body[body1]['tier']==3 and body[body2]['tier']==3 and \
         body[body1]['parent']==body[body2]['parent'] and body1!=body2:
        print('Transfer Type 3: Moon to another moon of the same planet')
        return 3+manType #mm'
    elif body[body1]['tier']==1 and body[body2]['tier']==2:
        print('Transfer Type 4: Sun orbit to planet')
        return 4+manType #sp
    elif body[body1]['tier']==2 and body[body2]['tier']==3 and\
         body1==body[body2]['parent']:
        print('Transfer Type 5: Planet to its moon')
        return 5+manType #pm
    elif  body[body1]['tier']==2 and body[body2]['tier']==1:
        print('Transfer Type 6: Planet to Sun orbit')
        return 6+manType #ps
    elif body[body1]['tier']==3 and body[body2]['tier']==2 and \
         body[body1]['parent']==body2 :
        print('Transfer Type 7: Moon to its planet')
        return 7+manType #mp
    elif body[body1]['tier']==1 and body[body2]['tier']==3:
        print('Transfer Type 8: Sun orbit to moon')
        return 8+manType #sm
    elif body[body1]['tier']==3 and body[body2]['tier']==1:
        print('Transfer Type 9: Moon to Sun orbit')
        return 9+manType #ms
    elif (body[body1]['tier']==2 and body[body2]['tier']==3) and \
         body1!=body[body2]['parent']:
        print('Transfer Type 10: Planet to another planet''s moon')
        return 10+manType #pm'
    elif (body[body1]['tier']==3 and body[body2]['tier']==2) and \
         body2!=body[body1]['parent']:
        print('Transfer Type 11: Moon to another planet')
        return 11+manType #mp'
    elif (body[body1]['tier']==3 and body[body2]['tier']==3) and \
         body[body1]['parent']!=body[body2]['parent']:
        print('Transfer Type 12: Moon to another planet''s moon')
        return 12+manType #mm''

def WorstBestDV(maneuv,calcType,ifplot=False):

    body1=maneuv['b1']
    body2=maneuv['b2']
    manType=maneuv['type']
    scena=maneuv['scenario']

    print('Start: '+body1+' '+\
          getRkmh(maneuv['A1'],body[body1])+' km height x '+\
          getRkmh(maneuv['P1'],body[body1])+' km height')
    print('End: '+body2+' '+\
          getRkmh(maneuv['A2'],body[body2])+' km height x '+\
          getRkmh(maneuv['P2'],body[body2])+' km height')
    print(f'Scenario: {'Maximum DV' if scena=='max' else 'Minimum DV'}')

    #orbit creation. 1 departure, 2 arrival

    ship1orbit=getorbit(maneuv['A1'],maneuv['P1'],maneuv['argP1'],body1,\
                        body[body1])
    ship2orbit=getorbit(maneuv['A2'],maneuv['P2'],maneuv['argP2'],body2,\
                        body[body2])
    if calcType%100 in [2,6,9,10,11,12]:
        #create departure planet orbit
        if body[body1]['tier']==2: #if b1 is a planet
            planet1=body[maneuv['b1']]
        elif body[body1]['tier']==3: #if b1 is a moon
            planet1=body[body[maneuv['b1']]['parent']]
        planet1orbit=getorbit(planet1['A'],planet1['P'],planet1['argP'],\
                                  planet1['parent'],planet1)

    if calcType%100 in [3,7,9,11,12]:
        #create departure moon orbit
        moon1=body[maneuv['b1']]
        moon1orbit=getorbit(moon1['A'],moon1['P'],moon1['argP'],\
                            moon1['parent'],moon1)

    if calcType%100 in [2,4,8,10,11,12]:
        #create arrival planet orbit
        if body[body2]['tier']==2: #if b2 is a planet
            planet2=body[maneuv['b2']]
        elif body[body2]['tier']==3: #if b2 is a moon
            planet2=body[body[maneuv['b2']]['parent']]
        planet2orbit=getorbit(planet2['A'],planet2['P'],planet2['argP'],\
                                  planet2['parent'],planet2)

    if calcType%100 in [3,5,8,10,12]:
        #create arrival moon orbit
        moon2=body[maneuv['b2']]
        moon2orbit=getorbit(moon2['A'],moon2['P'],moon2['argP'],\
                            moon2['parent'],moon2)


    #orbit1 and orbit2 determination
    if calcType%100 == 1:
        orbit1=ship1orbit; orbit2=ship2orbit
    elif calcType%100 in [2,10,11,12]:
        orbit1=planet1orbit; orbit2=planet2orbit
    elif calcType%100 in [4,8]:
        orbit1=ship1orbit; orbit2=planet2orbit
    elif calcType%100 in [6,9]:
        orbit1=planet1orbit; orbit2=ship2orbit
    elif calcType%100 == 3:
        orbit1=moon1orbit; orbit2=moon2orbit
    elif calcType%100 == 5:
        orbit1=ship1orbit; orbit2=moon2orbit
    elif calcType%100 == 7:
        orbit1=moon1orbit; orbit2=ship2orbit

    #hohmann parent determination
    if calcType%100 == 1:
        hohmannPar=body1
    elif calcType%100 in [2,4,6,8,9,10,11,12]:
        hohmannPar='Sun'
    elif calcType%100 in [3,5,7]:
        if body[body1]['tier']==2: hohmannPar=body1
        elif body[body1]['tier']==3: hohmannPar=body[body1]['parent']


    argP1=orbit1.argP; argP2=orbit2.argP
    #hohmann best-worst case
    if orbit1.e+orbit2.e==0 and orbit1.e*orbit2.e==0: #argP1+argP2==0 and argP1*argP2==0 and
        print('\tCircular orbit to Circular orbit')
        argstart=0
        hohmannTrf=orbit(0,0,0,hohmannPar)
        argend=0
        ok=HohmannCalc(orbit1, orbit2, argstart, hohmannTrf, argend)
        if ok != False:
            hohmannTrf=ok[0]; argend=ok[1]
            totaldV=transferDVcalc(orbit1,orbit2,hohmannTrf,argstart,argend,\
                                   ship1orbit,ship2orbit,calcType,scena)
            if ifplot:
                theta=list(map(lambda x:x/180*pi,range(0,360,1)))
                rorb1=[orbit1.getRtheta(i) for i in theta]
                rorb2=[orbit2.getRtheta(i) for i in theta]
                rorb3=[hohmannTrf.getRtheta(i) for i in theta]
                fig,ax=plt.subplots(subplot_kw={'projection': 'polar'})
                ax.plot(theta,rorb1,'.')
                ax.plot(theta,rorb2,'.')
                ax.plot(theta,rorb3)
                ax.legend(['Origin','Destination','Transfer'],loc='upper right')
                plt.title('Maneuver from '+maneuv['b1']+' to '+maneuv['b2'])
                plt.show()
            return totaldV
        else:
            return 'Calculation Failed'
        #transferDVcalc function
        #return its value

    elif orbit1.e+orbit2.e!=0 and orbit1.e*orbit2.e==0:#argP1+argP2!=0 and argP1*argP2==0
        print('\tElliptic orbit to Circular orbit, or vice-versa')
        hohmannTrf1=orbit(0,0,0,hohmannPar)
        hohmannTrf2=orbit(0,0,0,hohmannPar)
        argend1=0; argend2=0
        argstart=max(argP1,argP2)
        argstart=[argstart,(argstart+pi)%(2*pi)]
        #error here. can't figure out why 2025 04 01
        #mutability problems
        ok1=HohmannCalc(orbit1, orbit2, argstart[0], hohmannTrf1, argend1)
        ok2=HohmannCalc(orbit1, orbit2, argstart[1], hohmannTrf2, argend2)
        if ok1 != False and ok2 != False:
            hohmannTrf1=ok1[0]; argend1=ok1[1]
            hohmannTrf2=ok2[0]; argend2=ok2[1]
            totaldV1=transferDVcalc(orbit1,orbit2,hohmannTrf1,argstart[0],argend1,\
                                   ship1orbit,ship2orbit,calcType,scena)
            totaldV2=transferDVcalc(orbit1,orbit2,hohmannTrf2,argstart[1],argend2,\
                                   ship1orbit,ship2orbit,calcType,scena)
            if scena=='max':
                max1=sum(totaldV1)
                max2=sum(totaldV2)
                if max1>max2: return totaldV1
                else: return totaldV2
                #return max(totaldV1,totaldV2)
            elif scena=='min':
                min1=sum(totaldV1)
                min2=sum(totaldV2)
                if min1>min2: return totaldV2
                else: return totaldV1
                #return min(totaldV1,totaldV2)

            if ifplot:
                theta=list(map(lambda x:x/180*pi,range(0,360,1)))
                rorb1=[orbit1.getRtheta(i) for i in theta]
                rorb2=[orbit2.getRtheta(i) for i in theta]
                rorb3=[hohmannTrf1.getRtheta(i) for i in theta]
                rorb4=[hohmannTrf2.getRtheta(i) for i in theta]
                fig,ax=plt.subplots(subplot_kw={'projection': 'polar'})
                ax.plot(theta,rorb1,'.')
                ax.plot(theta,rorb2,'.')
                ax.plot(theta,rorb3)
                ax.plot(theta,rorb4)
                ax.legend(['Origin','Destination',
                           'Transfer1',
                           'Transfer2'],
                           loc='upper right')
                plt.title('Maneuver from '+maneuv['b1']+' to '+maneuv['b2'])
                plt.show()

        elif ok1 != False and ok2 ==False:
            hohmannTrf=ok1[0]; argend=ok1[1]
            totaldV=transferDVcalc(orbit1,orbit2,hohmannTrf,argstart,argend,\
                                   ship1orbit,ship2orbit,calcType,scena)
            if ifplot:
                theta=list(map(lambda x:x/180*pi,range(0,360,1)))
                rorb1=[orbit1.getRtheta(i) for i in theta]
                rorb2=[orbit2.getRtheta(i) for i in theta]
                rorb3=[hohmannTrf.getRtheta(i) for i in theta]
                fig,ax=plt.subplots(subplot_kw={'projection': 'polar'})
                ax.plot(theta,rorb1,'.')
                ax.plot(theta,rorb2,'.')
                ax.plot(theta,rorb3)
                ax.legend(['Origin','Destination','Transfer'],loc='upper right')
                plt.title('Maneuver from '+maneuv['b1']+' to '+maneuv['b2'])
                plt.show()


            return totaldV
        elif ok1 == False and ok2 !=False:
            hohmannTrf=ok2[0]; argend=ok2[1]
            totaldV=transferDVcalc(orbit1,orbit2,hohmannTrf,argstart,argend,\
                                   ship1orbit,ship2orbit,calcType,scena)

            if ifplot:
                theta=list(map(lambda x:x/180*pi,range(0,360,1)))
                rorb1=[orbit1.getRtheta(i) for i in theta]
                rorb2=[orbit2.getRtheta(i) for i in theta]
                rorb3=[hohmannTrf.getRtheta(i) for i in theta]
                fig,ax=plt.subplots(subplot_kw={'projection': 'polar'})
                ax.plot(theta,rorb1,'.')
                ax.plot(theta,rorb2,'.')
                ax.plot(theta,rorb3)
                ax.legend(['Origin','Destination','Transfer'],loc='upper right')
                plt.title('Maneuver from '+maneuv['b1']+' to '+maneuv['b2'])
                plt.show()

            return totaldV
        else:
            return 'Calculation Failed'
    else:
        print('\tElliptic orbit to Elliptic orbit')
        err=0
        argstart=[]
        div=9
        inid=0
        find=360
        errlim=0.00001
        argend=0
        for i in range(div):
            #argstart.append(2*pi*i/(div-1))
            argstart.append(inid*deg2rad+i*(find-inid)*deg2rad/(div-1))

        minmax=0

        while err<1-errlim or err>1+errlim:
            if ifplot:
                theta=list(map(lambda x:x/180*pi,range(0,360,1)))
                rorb1=[orbit1.getRtheta(i) for i in theta]
                rorb2=[orbit2.getRtheta(i) for i in theta]
                rorb3=[]
                fig,ax=plt.subplots(subplot_kw={'projection': 'polar'})
                ax.plot(theta,rorb1,'.')
                ax.plot(theta,rorb2,'.')

            totaldVlist=[]
            totaldVsum=[]
            step=0
            for i in argstart:
                hohmannTrf=orbit(0,0,0,hohmannPar)
                argend=0
                ok=HohmannCalc(orbit1, orbit2, i, hohmannTrf, argend)
                if ok != False:
                    hohmannTrf=ok[0]; argend=ok[1]
                    totaldVlist.append(transferDVcalc(orbit1,orbit2,hohmannTrf,i,argend,\
                                           ship1orbit,ship2orbit,calcType,scena))
                    totaldVsum.append(sum(totaldVlist[step]))
                    step+=1

                if ifplot:
                    rorb3.append([hohmannTrf.getRtheta(j) for j in theta])
                    ax.plot(theta,rorb3[step-1])



            if ifplot:
                ax.legend(['Origin','Destination'],loc='upper right')
                plt.title('Maneuver from '+maneuv['b1']+' to '+maneuv['b2'])
                plt.show()

            if scena=='max':
                idx=totaldVsum.index(max(totaldVsum))
            elif scena=='min':
                idx=totaldVsum.index(min(totaldVsum))

            if err==0 and minmax==0: minmax=totaldVsum[idx]
            else: err=minmax/totaldVsum[idx]; minmax=totaldVsum[idx]

            idxprev=(idx-1+div-1)%(div-1)
            idxnext=(idx+1)%(div-1)
            inid=argstart[idxprev]; find=argstart[idxnext]
            argstart=[]
            for i in range(div):
                argstart.append(inid+i*(find-inid)/(div-1))

            print('\terror:', str(err))
        return totaldVlist[idx]

def transferDVcalc(orbit1, orbit2, hohmann, argstart, argend, deptorbit, destorbit, \
                   calcType, scena):

    maneuv=calcType//100

    #escape calculation
    if maneuv in [2,4]:
        V1orbit=orbit1.getVtheta(argstart,body[orbit1.parent]['GM'])
        V1hohmann=hohmann.getVtheta(argstart,body[hohmann.parent]['GM'])
        #print('\t\tV1orb: %.3f V1hohmann: %.3f' %(V1orbit,V1hohmann))

        VSOI1=abs(V1orbit-V1hohmann)
##        if calcType%100 in [1,4,5,8]:
##            print('\t\tFirst Burn: %.3f' %(VSOI1))
##        elif calcType%100 in [2,3,6,7,9,10,11,12]:
##            print('\t\tVelocity at SOI 1: %.3f' %(VSOI1))
        #dv1 for type 1,4,5,8
        #vsoi1 for type 2,3,6,7,9,10,11,12
        #MANUV 2,4

        if calcType%100 in [2,3,6,7,9,10,11,12]:

            if calcType%100 in [2,3,6,7,10]:
                if scena=='max': pos=deptorbit.getA()
                elif scena=='min': pos=deptorbit.getP()
                bod=body[deptorbit.parent]
                sma=deptorbit.a

            elif calcType%100 in [9,11,12]:
                pos=body[deptorbit.parent][scena]
                bod=body[deptorbit.parent]['parent']
                sma=body[deptorbit.parent]['sma']

            VP1=sqrt(VSOI1**2+2*bod['GM']*(1/pos+1/bod['soi']))

            VP1LO=abs(VP1-sqrt(bod['GM']*(2/pos-1/sma)))
            #print('\t\tVP1: %.3f, VP1LO: %.3f' %(VP1,VP1LO))
            #dv1 for type 2,3,6,7,10
            #vsoi11 for type 9,11,12
            #MANUV 2,4

        if calcType%100 in [9,11,12]:

            VSOI11=VP1LO
            print('\t\tVSOI11: %.3f,' %(VSOI11))

            if scena=='max': pos=deptorbit.getA()
            elif scena=='min': pos=deptorbit.getP()

            VP11=sqrt(VSOI11**2+2*body[deptorbit.parent]['GM']*\
                      (1/pos+1/body[deptorbit.parent]['soi']))

            VP11LO=abs(VP11-sqrt(body[deptorbit.parent]['GM']*\
                                 (2/pos-1/deptorbit.a)))
            #print('\t\tVP11: %.3f, VP11LO: %.3f' %(VP11,V11LO))
            #dv1 for 9,11,12
            #MANUV 2,4
    else:
        VSOI1=0; VP1LO=0; VP11LO=0


    #capture calculation
    if maneuv in [3,4]:
        V2hohmann=hohmann.getVtheta(argend,body[hohmann.parent]['GM'])
        V2orbit=orbit2.getVtheta(argend,body[orbit2.parent]['GM'])
        #print('\t\tV2orb: %.3f V2hohmann:%.3f' %(V2orbit,V2hohmann))

        VSOI2=abs(V2orbit-V2hohmann)
        #dv2 for type 1,6,7,9
        #vsoi2 for type 2,3,4,5,8,10,11,12
        #MANUV 3,4

        if calcType%100 in [2,3,4,5,8,10,11,12]:

            if calcType%100 in [2,3,4,5,11]:
                if scena=='max': pos=destorbit.getA()
                elif scena=='min': pos=destorbit.getP()
                bod=body[destorbit.parent]
                sma=destorbit.a
            #VP1=sqrt(VSOI1**2+2*GMorbit1*(1/rorbit+1/rsoi))

            elif calcType%100 in [8,10,12]:
                pos=body[destorbit.parent][scena]
                bod=body[destorbit.parent]['parent']
                sma=body[destorbit.parent]['sma']


            VP2=sqrt(VSOI2**2+2*bod['GM']*(1/pos+1/bod['soi']))

            VP2LO=abs(VP2-sqrt(bod['GM']*(2/pos-1/sma)))
            #print('\t\tVP2: %.3f, VP2LO: %.3f' %(VP2,VP2LO))
            #dv2 for type 2,3,4,5,11
            #vsoi22 for type 8,10,12
            #MANUV 3,4

        if calcType%100 in [8,10,12]:

            VSOI22=VP2LO
            print('\t\tVSOI22: %.3f,' %(VSOI22))

            if scena=='max': pos=destorbit.getA()
            elif scena=='min': pos=destorbit.getP()

            VP22=sqrt(VSOI22**2+2*body[destorbit.parent]['GM']*\
                      (1/pos+1/body[destorbit.parent]['soi']))

            VP22LO=abs(VP22-sqrt(body[destorbit.parent]['GM']*\
                                 (2/pos-1/destorbit.a)))
            #print('\t\tV22: %.3f, VP22LO: %.3f' %(V22,V22LO))
            #dv2 for 8,10,12
            #MANUV 3,4
    else:
        VSOI2=0; VP2LO=0; VP22LO=0


    print(f'\t\t{argstart:.3f},',end="")
    if maneuv in [2,4]:
        #burn1
        #VP11LO
        if calcType%100 in [9,11,12]:
            print(' Burn 1: %.3f,' %(VP11LO),end="")
        #VP1LO
        if calcType%100 in [2,3,6,7,10]:
            print(' Burn 1: %.3f,' %(VP1LO),end="")
        elif calcType%100 in [9,11,12]:
            print(' V at SOI 11: %.3f,' %(VP1LO),end="")
        #VSOI1
        if calcType%100 in [1,4,5,8]:
            print(' Burn 1: %.3f,' %(VSOI1),end="")
        elif calcType%100 in [2,3,6,7,9,10,11,12]:
            print(' V at SOI 1: %.3f,' %(VSOI1),end="")

    if maneuv in [3,4]:
        #VSOI2
        if calcType%100 in [1,6,7,9]:
            print(' Burn 2: %.3f,' %(VSOI2),end="")
        elif calcType%100 in [2,3,4,5,8,10,11,12]:
            print(' V at SOI 2: %.3f,' %(VSOI2),end="")
        #VP2LO
        if calcType%100 in [2,3,4,5,11]:
            print(' Burn 2: %.3f,' %(VP2LO),end="")
        elif calcType%100 in [8,10,12]:
            print(' V at SOI 22: %.3f,' %(VP2LO),end="")
        #VP22LO
        if calcType%100 in [8,10,12]:
            w=''
            print(' Burn 2: %.3f,' %(VP22LO),end="")
        #burn2

    if calcType%100 == 1:
        print(' Total DV: %.3f,' %(VSOI1+VSOI2))
        return [VSOI1,VSOI2]
    if calcType%100 in [2,3]:
        print(' Total DV: %.3f,' %(VP1LO+VP2LO))
        return [VP1LO,VP2LO]
    if calcType%100 in [4,5]:
        print(' Total DV: %.3f,' %(VSOI1+VP2LO))
        return [VSOI1,VP2LO]
    if calcType%100 in [6,7]:
        print(' Total DV: %.3f,' %(VP1LO+VSOI2))
        return [VP1LO,VSOI2]
    if calcType%100==8:
        print(' Total DV: %.3f,' %(VSOI1+VP22LO))
        return [VSOI1,VP22LO]
    if calcType%100==9:
        print(' Total DV: %.3f,' %(VP11LO+VSOI2))
        return [VP11LO,VSOI2]
    if calcType%100==10:
        print(' Total DV: %.3f,' %(VP1LO+VP22LO))
        return [VP1LO,VP22LO]
    if calcType%100==11:
        print(' Total DV: %.3f,' %(VP11LO+VP2LO))
        return [VP11LO,VP2LO]
    if calcType%100==12:
        print(' Total DV: %.3f,' %(VP11LO+VP22LO))
        return [VP11LO,VP22LO]

def ManeuverCalc(trip,ifplot):
    step=1
    totalDVlist=[]
    for i in trip:
        print('Maneuver #%d: %s' %(step,i))
        man=trip[i]
        if man['type']==0: #correction burn

            print('Quick Burn')
            print('DV: %.3f' %man['DV'])
            print('Margin: %s' %man['margin'])
            print('totalDV: %.3f\n' %marg(man['DV'],man['margin']))
            totalDVlist.append([marg(man['DV'],man['margin'])])

        elif man['type']==1: #change apo/peri burn

            print('Apsis increase / decrease')
            print('Start: '+man['b']+' '+\
                getRkmh(man['A1'],body[man['b']])+' km height x '+\
                getRkmh(man['A21'],body[man['b']])+' km height')
            print('End: '+man['b']+' '+\
                getRkmh(man['A1'],body[man['b']])+' km height x '+\
                getRkmh(man['A22'],body[man['b']])+' km height')
            orbit1=getorbit(man['A1'],man['A21'],0,man['b'],body[man['b']])
            orbit2=getorbit(man['A1'],man['A22'],0,man['b'],body[man['b']])
            DV=abs(orbit1.getVbyR(orbit1.getA(),body[man['b']]['GM'])-\
                orbit2.getVbyR(orbit2.getA(),body[man['b']]['GM']))

            print('DV: %.3f' %DV)
            print('Margin: %s' %man['margin'])
            print('totalDV: %.3f\n' %marg(DV,man['margin']))
            totalDVlist.append([marg(DV,man['margin'])])

        elif man['type'] in [2,3,4]:
            calcType=calculationType(man['b1'],man['b2'],man['type'])
            totaldv=WorstBestDV(man,calcType,ifplot)
            totaldvsum=sum(totaldv)

            print('Burn 1: %.3f, Burn 2: %.3f, total DV: %.3f' \
                %(totaldv[0],totaldv[1],totaldvsum))

            burn1marg=0; burn2marg=0
            if man['type'] in [2,4]:
                burn1marg=marg(totaldv[0],man['margin1'])
            if man['type'] in [3,4]:
                burn2marg=marg(totaldv[1],man['margin2'])

            totaldvsummarg=burn1marg+burn2marg

            if man['type'] == 2:
                print('Margin 1: %s' %(man['margin1']))
            elif man['type'] == 3:
                print('\t\tMargin 2: %s' %(man['margin2']))
            elif man['type'] == 4:
                print('Margin 1: %s\tMargin 2: %s' %(man['margin1'],man['margin2']))

            print('Burn 1: %.3f, Burn 2: %.3f, total DV: %.3f\n' \
                %(burn1marg,burn2marg,totaldvsummarg))
            totalDVlist.append([burn1marg,burn2marg,totaldvsummarg])
        print(70*'#')
        print(70*'#'+'\n')
        step+=1
    return totalDVlist

def Summarizer(totalDVlist,trip):
    step=0
    ultDV=0
    print('Summary\n')
    for i in trip:
        print('Maneuver #%d: %s' %(step+1,i))
        if len(totalDVlist[step])==1:
            print('\t\tDV: %.3f m/s\n' %totalDVlist[step][0])
            ultDV=ultDV+totalDVlist[step][0]
        elif len(totalDVlist[step])==3:
            print('\t\tBurn 1: %.3f m/s' %totalDVlist[step][0])
            print('\t\tBurn 2: %.3f m/s' %totalDVlist[step][1])
            print('\t\tDV: %.3f m/s\n' %totalDVlist[step][2])
            ultDV=ultDV+totalDVlist[step][2]
        step+=1
    print('Total DV: %.3f m/s' %ultDV)

with open(maneuver_path,'r+') as f:
    trip=json.load(f)
    trip=trip['maneuver']

body=planet_data_miner(planet_pack_path)

totalDVlist=ManeuverCalc(trip,plot_maneuver)
Summarizer(totalDVlist,trip)
