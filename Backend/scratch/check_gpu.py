from gpt4all import GPT4All
import torch

print("--- Torch Check ---")
print(f"CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"Device Name: {torch.cuda.get_device_name(0)}")
    print(f"Memory Allocated: {torch.cuda.memory_allocated(0)} bytes")
    print(f"Memory Reserved: {torch.cuda.memory_reserved(0)} bytes")

print("\n--- GPT4All Check ---")
try:
    gpus = GPT4All.list_gpus()
    print("Available GPUs for GPT4All:")
    for gpu in gpus:
        print(f"- {gpu}")
except Exception as e:
    print(f"Error listing GPUs: {e}")
