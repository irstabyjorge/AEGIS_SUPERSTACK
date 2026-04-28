#!/usr/bin/env python3
"""AEGIS GPU Benchmark — Tests PyTorch and TensorFlow compute performance."""
import time, sys

def benchmark_pytorch():
    try:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"PyTorch device: {device}")
        sizes = [1024, 2048, 4096, 8192]
        for n in sizes:
            try:
                a = torch.randn(n, n, device=device)
                torch.cuda.synchronize() if device == "cuda" else None
                t0 = time.perf_counter()
                for _ in range(10):
                    c = torch.matmul(a, a)
                torch.cuda.synchronize() if device == "cuda" else None
                elapsed = (time.perf_counter() - t0) / 10
                gflops = (2 * n**3) / elapsed / 1e9
                print(f"  matmul {n}x{n}: {elapsed*1000:.1f}ms ({gflops:.1f} GFLOPS)")
            except Exception as e:
                print(f"  matmul {n}x{n}: FAILED ({e})")
    except ImportError:
        print("PyTorch not installed")

def benchmark_tensorflow():
    try:
        import os
        os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
        import tensorflow as tf
        gpus = tf.config.list_physical_devices("GPU")
        device = "/GPU:0" if gpus else "/CPU:0"
        print(f"\nTensorFlow device: {device} ({len(gpus)} GPUs)")
        sizes = [1024, 2048, 4096]
        for n in sizes:
            try:
                with tf.device(device):
                    a = tf.random.normal([n, n])
                    _ = tf.matmul(a, a).numpy()
                    t0 = time.perf_counter()
                    for _ in range(10):
                        c = tf.matmul(a, a)
                    if gpus:
                        c.numpy()
                    elapsed = (time.perf_counter() - t0) / 10
                    gflops = (2 * n**3) / elapsed / 1e9
                    print(f"  matmul {n}x{n}: {elapsed*1000:.1f}ms ({gflops:.1f} GFLOPS)")
            except Exception as e:
                print(f"  matmul {n}x{n}: FAILED ({e})")
    except ImportError:
        print("TensorFlow not installed")

if __name__ == "__main__":
    print("AEGIS GPU BENCHMARK")
    print("=" * 50)
    benchmark_pytorch()
    benchmark_tensorflow()
    print("\nDone.")
