import random
def shinchan():
    otp=''
    u_l=[chr(i) for i in range(ord('A'),ord('Z')+1)]
    s_l=[chr(i) for i in range(ord('a'),ord('z')+1)]
    for i in range(2):
        otp=otp+random.choice(u_l) #otp=''+''A' -- 'A'
        otp=otp+random.choice(s_l) #otp='A'+'K' -- 'AK',otp='AK9M'+'u'
        otp=otp+str(random.randint(0,9)) #otp='AK'+'9' -- 'AK9', otp='AK9Mu'+'8'-----
    return otp   #'AK9Mu8' 
    