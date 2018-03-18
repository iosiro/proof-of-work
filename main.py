import tornado.ioloop
import tornado.web
import json
import base64
import hashlib
import os
import subprocess
from subprocess import PIPE

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        verification_stringb64 = self.get_argument("verification", None)
        if verification_stringb64:
            try:
                decoded = base64.b64decode(verification_stringb64)
                checkpgp = verify_pgp_signature(decoded)
                if checkpgp:
                    msg = extract_message_from_signed_pgp(decoded.decode())
                    verification_values = json.loads(msg)
                    self.render("html/success.html", client_name = verification_values['client_name'],
                    description= verification_values['description'], date_signed=verification_values['date_signed'], nature_of_work=verification_values['nature_of_work'] )
                else:
                    self.render("html/error.html", error_message="The signature on the image is incorrect.")
            except Exception as e:
                print (e)
                #print("here")
                self.render("html/error.html", error_message="Something went wrong, that's all we know.")
        else:
            self.render("html/error.html", error_message="Hmmmm. That badge wasn't configured correctly. Please let the website know!")

def extract_message_from_signed_pgp(text):
    start = '''-----BEGIN PGP SIGNED MESSAGE-----
Hash: SHA512
'''
    end = "-----BEGIN PGP SIGNATURE-----"
    msg = text.split(start)[1].split(end)[0]
    return msg

def verify_pgp_signature(text):
    print ("verifying {}".format(text))
    md5_of_text = hashlib.md5(text).hexdigest()
    filepath = '/tmp/{}'.format(str(md5_of_text))

    if os.path.exists(filepath):
        sig_check = check_file_signature(filepath)
    else:
        data_file = open(filepath, 'w')
        data_file.write(text.decode())
        data_file.close()
        sig_check = check_file_signature(filepath)
    return sig_check

def check_file_signature(filepath):
    #subprocess.call(["gpg", "--verify-file", filepath])
    print(filepath)
    print(type(filepath))
    #proc = subprocess.Popen(["gpg", "--verify-file", str("{}".format(filepath))], stdout=PIPE , stderr=PIPE)
    proc = subprocess.Popen(["gpg", "--verify-file", filepath], stdout=PIPE , stderr=PIPE)

    #stdout = proc.stdout.read()
    output = proc.stderr.read().decode()
    for i in output.splitlines():
        if '''gpg: Good signature from "iosiro <security@iosiro.com>"''' in i:
            print ("[+] Good signature found...")
            return True
    print ("[!] Signature is BAD!")
    return False

    '''try:
        outs, errs = proc.communicate(timeout=15)
    except TimeoutExpired:
        proc.kill()
        outs, errs = proc.communicate()
    print(outs, errs)
    '''

def make_app():
    return tornado.web.Application([
        (r"/verify", MainHandler),
    ])

if __name__ == "__main__":
    #Import public key...
    os.system("gpg --import public_key.pub")
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()