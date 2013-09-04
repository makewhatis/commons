python_binary(
  name = "jenkins",
  source = "jenkins.py",
  dependencies = [
    pants("src/python/twitter/common/app"),
    pants("src/python/twitter/common/log"),
    pants("3rdparty/python:jenkinsapi-0.2.12"),
  ]
)
