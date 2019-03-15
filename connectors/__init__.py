import paramiko
import invoke
import fabric
import os
import requests
import time
import logging
import json
from fabric import ThreadingGroup as FabGroup
import io
import logging
import threading
from fabric import SerialGroup as FabSerialGroup
HTTP_MODE = 0
LOCAL_MODE = 1
CMD_MODE = 2

PY_EXT = "py"
SHELL_EXT = "sh"

PY_PARSER = "python"
SHELL_PARSER = "sh"



class Connecter:
	_tmp_path = "/tmp/"

	def __init__(self, hosts, local_script=None, http_remote_script=None, user=None, pwd=None, port=None, script_parser=None, pkey=None, sudo=False, parallel=True):
		self.hosts = hosts
		self.parallel = parallel
		self.sudo = sudo
		self.hosts_failed = []
		self.hosts_success = []
		self.user = user
		self.conf = invoke.config.Config(system_prefix="/", user_prefix="/", runtime_path="/",project_location="/")
		if pkey:
			fatal = True
			try:
				self.connect_kwargs = dict(pkey=paramiko.RSAKey.from_private_key(io.StringIO(pkey)))
			except Exception as err:
				logging.warning("load key failed:%s" % str(err))
			else:
				fatal = False
			if fatal:
				raise KeyError("load key failed")
		self.pwd = pwd
		self.port = port
		self.run_time = 0
		self.done = False
		self.cmd = None
		self.local_script = local_script
		self.script_parser = script_parser
		self.http_remote_script = http_remote_script
		if self.local_script:
			self.run_mode = LOCAL_MODE
		elif self.http_remote_script:
			self.run_mode = HTTP_MODE
		else:
			self.run_mode = CMD_MODE

	@classmethod
	def __analyse_parser(cls, filename):
		ext = filename.split(".")[-1]
		if ext == PY_EXT:
			return PY_PARSER
		elif ext == SHELL_EXT:
			return SHELL_PARSER
		else:
			raise KeyError("unexpect script suffix")

	def __get_script_local_path(self):
		if self.run_mode == LOCAL_MODE:
			path = self.local_script
		elif self.run_mode == HTTP_MODE:
			path = self.http_remote_script
		else:
			raise KeyError("unexpect script mode")
		directory, script_name = os.path.split(path)
		if self.run_mode == HTTP_MODE:
			r = requests.get(path)
			if r.status_code >=400:
				raise KeyError("can't get script %s" % path)
			directory = self._tmp_path
			with open(self._tmp_path+script_name, 'wb') as code:
				code.write(r.content)
		return directory, script_name

	def __put_script_to_remote_genrate_cmd(self):
		directory, script_name = self.__get_script_local_path()
		for host in self.hosts:
			try:
				tmp_c = fabric.Connection(host, port=self.port, user=self.user, connect_kwargs=self.connect_kwargs, config=self.conf)
				r=tmp_c.put(os.path.join(directory, script_name), self._tmp_path)
			except Exception as err:
				self.hosts_failed.append({"host": host, "error": str(err)})
			else:
				self.hosts_success.append(host)
			finally:
				tmp_c.close()
		parser = ConnecterScriptRunner.__analyse_parser(script_name)
		self.cmd = "%s %s" % (parser, script_name)
		logging.debug(self.cmd)
		return self.cmd

	def init_remote_get_cmd(self,):
		return self.__put_script_to_remote_genrate_cmd()

	@classmethod
	def context(cls, method):
		def wrapper(self, if_script=True, cmd=None):
			if if_script:
				cmd = self.__put_script_to_remote_genrate_cmd()
			return method(self, cmd)
		return wrapper

	def close(self):
		pass

	def __del__(self):
		self.close()


class ConnecterScriptRunner(Connecter):
	def __init__(self, **kwargs):
		super(ConnecterScriptRunner, self).__init__(**kwargs)

	def open(self):
		self.ssh_client = FabGroup(port=self.port, user=self.user, config=self.conf, connect_kwargs=self.connect_kwargs, *self.hosts)

	@Connecter.context
	def run(self, cmd):
		s = time.time()
		rtd = {}

		def run_script(cc):
			with cc.cd(self._tmp_path):
				if self.sudo:
					r = cc.run("sudo "+ cmd, hide=True, pty=True)
				else:
					r = cc.run(cmd, hide=True)
			return r

		def tmp_tread_func(xx):
			try:
				result = run_script(xx)
			except Exception as err:
				rtd[xx.host] = {"error": str(err)}
			else:
				rtd[xx.host] = {"stdout": result.stdout,"stderr": result.stderr}
		if self.parallel:
			thread_pool = []
			for xx in self.ssh_client:
				tmp_t = threading.Thread(target=tmp_tread_func, args=(xx,))
				tmp_t.start()
				thread_pool.append(tmp_t)

			for t in thread_pool:
				t.join()
		else:
			for xx in self.ssh_client:
				tmp_tread_func(xx)

		e = time.time()
		self.done = True
		self.run_time = e - s
		return rtd

	def close(self):
		for xx in self.ssh_client:
			xx.close()


class ConnecterInteractive(Connecter):
	def __init__(self, **kwargs):
		super(ConnecterInteractive, self).__init__(**kwargs)
		self.spliter = "<br>"
		self.ssh_client = paramiko.SSHClient()
		self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		self.stdin = None
		self.stout = None
		self.stderr = None

	def open(self):
		self.ssh_client.connect(
			hostname=self.hosts[0],
			username=self.user,
			port=self.port,
			password=self.pwd,
		)

	def close(self):
		self.ssh_client.close()




	@Connecter.context
	def run_async(self, cmd):
		self.stdin, self.stdout, self.stderr = self.ssh_client.exec_command("cd %s &&  %s" % (self._tmp_path ,cmd))

	def read_result_until_done(self):
		stdout = self.stdout.readline()
		while stdout:
			yield (stdout+self.spliter)
			stdout = self.stdout.readline()

	def read_result(self):
		stdout = self.stdout.readline()
		stdout_store = ""
		st = time.time()
		while stdout:
			stdout_store += stdout
			yield ""
			stdout = self.stdout.readline()
		et = time.time()
		yield json.dumps({"stdout": stdout_store, "cost": et-st})



if __name__ == "__main__":
	c = ConnecterInteractive(host="venus-test.nioint.com", port=2222)
	c.open()
	c.run_command("sh 1.sh")
	for x in c.read_result_until_done():
		print(x)
	print("finish")
	# c=ConnecterScriptRunner(host="venus-test.nioint.com", port=2222, script="1.sh")
	# print(c.put_and_run_script())