import sys
import subprocess
import os
import shutil
import json

import patch_ng as patch

dirname = os.path.dirname(__file__)
config_path = os.path.join(dirname, "config.json")

argv = sys.argv

def print_help():
	print("Toolchain utility for the RL2 Mod Loader")
	print(f"Usage: {argv[0]} <command> [args...]")
	print()
	print("Allowed commands:")
	print(" - help - Display this message")
	print(" - configure - Configure the toolchain")
	print(" - reset-config - Reset the toolchain configuration")
	print(" - decompile - Decompile the game assembly")
	print(" - prepare-to-patch - Decompile the game assembly but stop after applying patches")
	print(" - cleanup - Remove all generated files")


def main():
	if len(argv) < 2:
		print_help()
		exit(1)
	match argv[1]:
		case "help":
			print_help()
		case "decompile":
			cmd_decompile()
		case "cleanup":
			cmd_cleanup()
		case "prepare-to-patch":
			cmd_decompile(True)
		case "reset-config":
			cmd_reset_config()
		case "configure":
			cmd_configure()
		case _:
			print_help()
			exit(1)


def ensure_dotnet():
	try:
		ver = subprocess.run(["dotnet", "--version"], capture_output=True)
		print("dotnet version:", ver.stdout.decode("utf-8").rstrip())
	except Exception as e:
		print("dotnet binary not available, please install it")
		print(str(e))
		exit(1)


def ensure_ilspycmd():
	try:
		ver = subprocess.run(["ilspycmd", "--version"], capture_output=True)
		print(
			"ilspy version",
			ver.stdout.decode("utf-8").rstrip().replace("\r", "").replace("\n", " | "),
		)
	except Exception as e:
		print(
			"ilspycmd binary not available, please install it using: dotnet tool install ilspycmd -g"
		)
		print(str(e))
		exit(1)

def get_config():
	if not os.path.exists(config_path):
		print("Configuration file doesn't exist, please run the \"configure\" command first")
		exit(1)
	with open(config_path, encoding="utf-8") as f:
		data = f.read()
		config = json.loads(data)
		return {
			"install_dir": config["install_dir"],
			"dll_folder": config["dll_folder"],
			"mod_dir": config["mod_dir"]
		}

def cmd_decompile(patch_only = False):
	ensure_dotnet()
	ensure_ilspycmd()
	config = get_config()
	managed_path = config["dll_folder"]
	assembly_orig_path = os.path.join(managed_path, "Assembly-CSharp-original.dll")
	assembly_path = os.path.join(managed_path, "Assembly-CSharp.dll")
	if os.path.exists(assembly_orig_path):
		print("Found Assembly-CSharp-original.dll, using it instead")
		assembly_path = assembly_orig_path
	if not os.path.exists(assembly_path):
		print("Assembly-CSharp.dll not found, aborting...")
		exit(1)
	if not os.path.exists(assembly_orig_path):
		print("Assembly-CSharp-original.dll doesn't exist, creating it")
		shutil.copy(assembly_path, assembly_orig_path)
	output_dir = os.path.join(dirname, "../RL2-Source")
	if os.path.exists(output_dir):
		shutil.rmtree(output_dir)
	os.mkdir(output_dir)
	cmd = ["ilspycmd", "--nested-directories", "-p", "-o", output_dir, assembly_path]
	print("Decompiling the game...", cmd)
	try:
		ilspy = subprocess.run(cmd)
	except:
		print("Failed to decompile the game, aborting...")
		exit(1)
	print("The game has been decompiled, applying patches...")
	patch_dir = os.path.join(dirname, "../Patches")
	for file in sorted(os.listdir(patch_dir)):
		patch_path = os.path.join(dirname, "../Patches", file)
		if not os.path.isfile(patch_path):
			continue
		print(f"- {file}")
		ptch = patch.fromfile(patch_path)
		if not ptch:
			print("Failed to parse patch, aborting...")
			exit(1)
		if not ptch.apply(1, output_dir):
			print("Failed to apply patch, aborting...")
			exit(1)
		
	print("Patches have been applied, copying the source code")
	if patch_only:
		print("Stopping decompilation process as patch-only mode has been requested")
		exit(0)
	target_dir = os.path.join(dirname, "../Assembly-CSharp")
	for file in os.listdir(target_dir):
		if file == "ModLoader" or file == "Assembly-CSharp.csproj":
			continue
		path = os.path.join(target_dir, file)
		if os.path.isfile(path):
			os.remove(path)
		if os.path.isdir(path):
			shutil.rmtree(path)
	for file in os.listdir(output_dir):
		if file == "Assembly-CSharp.csproj" or file == "Assembly-CSharp-original.csproj":
			continue
		shutil.move(os.path.join(output_dir, file), target_dir)
	shutil.rmtree(output_dir)
	print("Source code is ready, copying libs...")
	lib_dir = managed_path
	target_lib_dir = os.path.join(target_dir, "lib")
	if not os.path.exists(target_lib_dir):
		os.mkdir(target_lib_dir)
	for file in os.listdir(lib_dir):
		if file == "Assembly-CSharp.dll" or file == "Assembly-CSharp-original.dll":
			continue
		path = os.path.join(lib_dir, file)
		shutil.copyfile(path, os.path.join(target_lib_dir, file))
	print("The environment is ready")


def cmd_cleanup():
	output_dir = os.path.join(dirname, "../RL2-Source")
	target_dir = os.path.join(dirname, "../Assembly-CSharp")
	for file in os.listdir(target_dir):
		if file == "ModLoader" or file == "Assembly-CSharp.csproj":
			continue
		path = os.path.join(target_dir, file)
		if os.path.isfile(path):
			os.remove(path)
		if os.path.isdir(path):
			shutil.rmtree(path)
	if os.path.exists(output_dir):
		shutil.rmtree(output_dir)

def cmd_reset_config():
	if os.path.exists(config_path):
		os.remove(config_path)

def cmd_configure():
	print("Toolchain Configuration Utility")
	if os.path.exists(config_path):
		print("A configuration file already exists, if you want to continue run the \"reset-config\" command")
		exit(1)
	config = {}
	config["install_dir"] = input("Game installation directory: ")
	config["dll_folder"] = os.path.join(config["install_dir"], "Rogue Legacy 2_Data", "Managed")
	config["mod_dir"] = os.path.join(config["install_dir"], "Rogue Legacy 2_Data", "Mods")
	
	config_json = json.dumps(config)
	with open(config_path, "w+", encoding="utf-8") as f:
		f.write(config_json)

if __name__ == "__main__":
	main()