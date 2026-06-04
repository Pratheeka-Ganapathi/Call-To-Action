"""Quick test — swap between Qwen and MiniCPM repeatedly."""

from model_manager import manager

print("=== First swap: load Qwen ===")
manager.ensure_model("qwen")
print(f"current: {manager.current_model}")

print("\n=== Second call: already Qwen, should be instant ===")
manager.ensure_model("qwen")
print(f"current: {manager.current_model}")

print("\n=== Swap to MiniCPM ===")
manager.ensure_model("minicpm")
print(f"current: {manager.current_model}")

print("\n=== Swap back to Qwen ===")
manager.ensure_model("qwen")
print(f"current: {manager.current_model}")

print("\n=== Shutdown ===")
manager.shutdown()
print("done.")