from jenkinsapi.jenkins import Jenkins
from jenkinsapi.job import Job
from jenkinsapi.exceptions import JenkinsAPIException
from jenkinsapi.exceptions import UnknownJob

import os
import sys

from twitter.common import app
from twitter.common import log
from twitter.common import dirutil

from twitter.common.log.options import LogOptions


app.set_usage("jenkins --[server|outdir|config]  [--job=[jobname]] [create|delete|show|enable|disable]")
app.add_option(
  "--server",
  default="ci.makewhat.is:8080",
  dest="server",
  help="jenkins server"
)
app.add_option(
  "--job",
  default=None,
  dest="job",
  help="job name"
)
app.add_option(
  "--config",
  default=None,
  dest="config",
  help="config path"
)
app.add_option(
  "--config_dir",
  default=None,
  dest="config_dir",
  help="config directory"
)
app.add_option(
  "--outdir",
  default=None,
  dest="outdir",
  help="config dump output path"
)
app.add_option(
  "--verbose",
  default=None,
  dest="verbose",
  help="print more things"
)


def parse_arguments(args):
  """
  Parse the positional args
  """
  avail = {
    'create': create,
    'delete': delete,
    'enable': enable,
    'disable': disable,
    'show': show,
    'dump': dump,
    'restore': restore,
  }

  return avail[args[0]]  


def read_config(config_path):
  """
r
  read config from file
  """
  with open(config_path, 'r') as c:
    text = c.read()
  return text


def show(j, name):
  config = app.get_options().config  
  if config != None: 
    print(read_config(config))
  else:
    print("could not find")


def create(j, name):
  """
  create a job

  j - jenkins object
  name - of job
  """
  job_xml = read_config(app.get_options().config)
  if job_xml == None:
    job_xml = """
<project>
<actions/>
<description/>
<keepDependencies>false</keepDependencies>
<properties/>
<scm class="hudson.scm.NullSCM"/>
<canRoam>true</canRoam>
<disabled>false</disabled>
<blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
<blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
<triggers/>
<concurrentBuild>false</concurrentBuild>
<builders>
<hudson.tasks.Shell>
<command>sleep 60</command>
</hudson.tasks.Shell>
</builders>
<publishers/>
<buildWrappers/>
</project>"""

  log.info("creating %s" % name)

  try:
    j.create_job(name, job_xml)
  except JenkinsAPIException as e:
    log.error("Error creating job %s:" % name)


def delete(j, name):
  """
  delete job
  """
  try:
    j.delete_job(name)
  except JenkinsAPIException as e:
    log.error("error deleting job: %s" % e)

def enable(j, name):
  """
  enable a job
  """
  job_url = "%s/job/%s" % (j.baseurl, name)
  job = Job(job_url, name, j)
  result = job.enable()  
  print("result: %s" % result.status_code)

def restore(j, target):
  """
  Restore jobs from a config directory
  """
  config_dir = app.get_options().config_dir

  if config_dir is None:
    log.error("no config_dir defined.")
    sys.exit()

  if not os.path.exists(os.path.realpath(config_dir)):
    log.error("config path does not exist")
    sys.exit()

  for job in os.listdir(config_dir):
    # here we need to:
    # check for config.xml
    # check for job on target server
    # if job exists, update it
    # if not create it. 
    config_file = "%s/%s/config.xml" % (config_dir, job)
    if not os.path.exists(config_file):
      log.error("config file does not exist: %s" %config_file)
      sys.exit()

    job_xml = read_config(config_file)

    try:
      jobj = j.get_job(job)
      if not jobj.get_config() == job_xml:
        log.info("Updating %s" % job)
        jobj.update_config(job_xml)
    except UnknownJob as e:
      log.error("job doesnt exist. creating")
      j.create_job(job, job_xml)


def disable(j, name):
  """
  disabled a job
  """
  job_url = "%s/job/%s" % (j.baseurl, name)
  job = Job(job_url, name, j)
  result = job.disable()  
  print("result: %s" % result.status_code)


def dump(j, name):
  """
  """
  job_list = j.get_jobs_list()
  if app.get_options().outdir is None:
    outdir = "/tmp/"
  else:
    outdir = app.get_options().outdir

  outpath = os.path.join(outdir, j.server)
  
  if not os.path.exists(outpath):
    try:
      mkdir_p(outpath)
    except OSError as e:
      log.error("Problem making dir: %s " % e)

  if name is None:
    for job in job_list:
      write_config(j, outpath, job)
  else:
    write_config(j, outpath, name) 

  return True

def write_config(j, path, job):
  jobj = j.get_job(job)
  outfile = os.path.join(path, job + ".xml")
  log.info("Dumping job %s to %s" % (job, outfile))
  try:
    with open(outfile, 'w') as f:
      f.write(jobj.get_config())
      if app.get_options().verbose:
        print(jobj.get_config())
  except Exception as e:
    log.error("Error writing configs: %s " % e)

def mkdir_p(path):
  '''Stolen from: http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python'''
  try:
    os.makedirs(path)
  except OSError as exc: # Python >2.5
    if exc.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else: raise


def main(args, options):

  server = 'ci.makewhat.is:8080'

  if app.get_options().server is not None:
    server = app.get_options().server

  j = Jenkins("http://%s" % server)
  j.server = server
  cmd = parse_arguments(args)

  if cmd.__name__ == restore:
    target = app.get_options().master
  else:
    target = app.get_options().job

  cmd(j, target) 

app.main()
