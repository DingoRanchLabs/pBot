"""General dev tasks.
"""

import subprocess
from invoke import task
import docker


CUSTOM_DOCKER_IMAGES = [
	"pbot-bot",
	"pbot-transceiver",
]

client = docker.from_env()

# Tasks ------------------------------------------------------------------------

@task
def doc(ctx):
	pass


@task
def devbounce(ctx):
	"""
	Deletes any old artifacts and rebuids & runs from scratch.
	"""

	# Stop and remove pbot containers.
	for container in client.containers.list(all=True):
		print(container.name)
		if container.name in CUSTOM_DOCKER_IMAGES:
			if container.status == "running":
				container.kill()
			container.remove()

	# Delete pbot images.
	for image in client.images.list():
		for image_name in CUSTOM_DOCKER_IMAGES:
			if image_name in " ".join(image.tags):
				print(image_name)
				client.images.remove(image_name)

	# FIXME: change cwd.
	# Rebuild everything.
	subprocess.run(["docker-compose", "-ppbot", "-f./config/docker-compose.yml", "up", "--detach"])
