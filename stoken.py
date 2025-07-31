from itsdangerous import URLSafeTimedSerializer
salt='otpverify'
def entoken(data):
    serializer=URLSafeTimedSerializer('code@1999')
    return serializer.dumps(data,salt=salt)
def dntoken(data):
    '''Function to decrypt encrypted token'''
    serializer=URLSafeTimedSerializer('code@1999')
    return serializer.loads(data,salt=salt)