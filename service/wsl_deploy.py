import subprocess

# Command you want to run inside WSL
command = "sudo systemctl restart flaskapp"

# Run it inside WSL
result = subprocess.run(
    ["wsl", "bash", "-c", command],
    capture_output=True,
    text=True
)

print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
