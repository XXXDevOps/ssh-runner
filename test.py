import fabric
from fabric import ThreadingGroup as FabGroup
import paramiko
import io
import invoke
# ik=invoke.config.Config(system_prefix="/", user_prefix="/", runtime_path="/")
# p="-----BEGIN RSA PRIVATE KEY-----\nMIIEqAIBAAKCAQEAqbnc/rF12NWbsIB4XyGUnoVOjZHEKipIF3+agVjE2W/cR7WK\nbrWjhATO8qTCZjU7Gk/cyIS9DpbjQ1pagKaGGEpkQYpJe6S5fyWI8lqtd84d8teq\nG2if0mcC1vHrPJWGt6+dHGxabt8fG8TBtFtjk2F25ScK9znYYZw3cZiyhAEUi/ZH\n7vi+DPtUF0W28Uv4IkTr6UbS9vTT9zxeTtqfdW/Bx2PEHXi3I71Og30fQez/GWcZ\n3TstvxxePOoNu8OysV0bZNPwTsP2xZFToR/QrCUF6CFXGKoFcyLT/G2bDaDJ0PnT\nMqO9jCpem9QGV94cBbp80Iv1L1Q7K+a20lCU2QIDAQABAoIBAHy+hpcLhzofhZZs\nVgxVeg4onFugzzTObr4Wo1B+FfBaLuTloSFNjyjw/8mHHvpQFWh5WiRmqy2V6OMP\n/YSg393qj1U8dlXR9CRnSggWbXionYpmyDfs5cqWu5ePpv2YSLOo9yh02uKySwL1\n0gjlQoKIGALEd2LNuSPE1VtAh7RMgzq97Hq/CxmNCMagDNn2LgcOWJ9ViTs5Ug3h\n7RlynvUldLVIA3HvummlQ+7ifsOZ8CeIYOUGSri5fKw+wTMspNNEnj2fBSZzpNcz\n11jHYL4rGnEqtYldLofIca6gs+lFa5EWNHECn1LRXPfxvWR2di3/2bEjBVfBuATF\nBB+8yIECggCBAL36faAiuW/9yW7T1rU6YN5ySHg7ZYladF3XnSUTWxqEJNsH/aKq\nEfov4G2VgwpWz/EmqUoDHWH8pJ5o9Q1+625kUGLopW9FToJyeK1NyQ6VffjBI41J\npBm1a/Hu2PWIhZUYMxHUZm9AKKHepdSPhN0C8PZXKJFKVu8yDzWX1GBtAoIAgQDk\ntZr4tKx1rs5kM8hcWhX1WXBmV0fsMhDotp/Njyy8IcgxDeeCNgf8NjwhqYgPsuay\nW2AD6F074ms4a69eyYFcPS7P26YXkEdY+HHRPngrSms5uxifvKQWfNZsaTyJPC5b\nFLDJaH3C2hkJxj5diwRzlO55lgUtwSbhZEeeoCP6nQKCAIEAiSsOf4vy5kiQo0Oy\n9+ExxgswBhekxVqZQJSIcxeZpPiaf8cyO7ueBU2CNr1IAzQRKeYnPzgmg/Rdi77u\niJMGPAuT+wZNRJz/BbLPLRpHvA72CKCzIbV1FdbnHKS+4/FxuefiH9KDL3pcnBtd\nEq+ZV9Zi0wq1UMojIMu9LY31mrUCggCAWiwb6LjbUh7Usv8TnQ3LoItd3IvHCKII\ntqfiQ5qSia5MDsMrptQEu/TqKl98DKx9do6+QWwo7kZr/be/UgDipupcfYldZ+bz\nqmlx/ozBtlfGBOH2aGxoyZD4vY+UVYtLv49d0FsJUnzI6GioCBuaarOqfneenRaN\nbMorzqfW56UCggCAcbVGfiHRBrz22w5VE9V87LzW1lBiTFTCCJ2pPSMqWgiRTDc2\nGcHgW1Sc21CzLQg5yUpundqSuSQzPVgqNu8GNL28xNLDIyH44F7nqCTjDlgG+TX5\nUwqVWeXKkci/vNJ22d3FVeO89EiDZd473JsXK8RNgKVcD+BiF1Qtq53iIkQ=\n-----END RSA PRIVATE KEY-----"
# pkey=paramiko.RSAKey.from_private_key(io.StringIO(p))
host = "venus-test.nioint.com"
# c = fabric.Connection(host, port=2222, user="bozhi.gu", connect_kwargs=dict(pkey=pkey), config=ik)
# r=c.put("/tmp/15382102672.sh","/tmp")
# print(r)

ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_client.connect(
			hostname=host,
			username="bozhi.gu",
			port=2222,
			# pkey=pkey,
		)
chan = ssh_client.invoke_shell()
chan.sendall("exit\n")
while 1:
	msg = chan.recv(4096)
	print(msg)
# stdin,stdout,stderr = ssh_client.exec_command("ls -al")
# print(stdout.read())