import docker
import platform

print(f"Platform: {platform.system()}")
print("="* 60)

# Try different connection methods
methods = [
    ("from_env()", lambda: docker.from_env()),
    ("TCP localhost", lambda: docker.DockerClient(base_url='tcp://localhost:2375')),
    ("npipe (default)", lambda: docker.DockerClient(base_url='npipe:////./pipe/docker_engine')),
    ("npipe (alt)", lambda: docker.DockerClient(base_url='npipe://' + '//' * 2 + '.' + '/pipe/docker_engine')),
]

for name, method in methods:
    try:
        print(f"\nTrying {name}...")
        client = method()
        client.ping()
        print(f"  ✅ SUCCESS! Connected with {name}")
        print(f"  Docker version: {client.version()['Version']}")
        break
    except Exception as e:
        print(f"  ❌ Failed: {str(e)[:100]}")
