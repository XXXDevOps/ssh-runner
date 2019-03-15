import paramiko
import time
import io

class Connect:
	def __init__(self, host, user, port=22, pwd=None, pkey=None):
		self.host = host
		self.port = port
		self.user = user
		self.pwd = pwd
		self.ssh_client = paramiko.SSHClient()
		self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		if pkey is not None:
			self.pkey = paramiko.RSAKey.from_private_key(io.StringIO(pkey))
		else:
			self.pkey = None
		self.stdin = None
		self.stout = None
		self.stderr = None
		self.spliter = ""
		self.chan = None
		self.isclose = False

	def open(self):
		self.ssh_client.connect(
			hostname=self.host,
			username=self.user,
			port=self.port,
			pkey=self.pkey,
			password=self.pwd,
		)
		self.chan = self.ssh_client.invoke_shell(term='xterm', width=300)
		self.chan.set_combine_stderr(True)
		self.chan.set_environment_variable(name="PS1", value="[\\u@\\h \\W]\\$")

	def run(self, cmd):
		self.stdin, self.stdout, self.stderr = self.ssh_client.exec_command(cmd)

	def close(self):
		self.ssh_client.close()

	def read_result_until_done(self):
		stdout = self.stdout.readline()
		stderr = self.stderr.readline()
		while stdout or stderr:
			res = ""
			if stdout:
				res += stdout
			if stderr:
				res += stderr
			yield (res+self.spliter)
			stdout = self.stdout.readline()
			stderr = self.stderr.readline()

	def reciever(self):
		while not self.isclose:
			if not self.chan.closed:
				yield self.chan.recv(4096)
			else:
				break

	def close(self):
		self.isclose = True
		self.chan.close()
		self.ssh_client.close()


	def __del__(self):
		self.close()

