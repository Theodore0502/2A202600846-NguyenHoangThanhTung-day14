import asyncio
import os
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# Đảm bảo có thể import được các module trong project
ROOT_PATH = Path(__file__).parent.resolve()
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from dotenv import load_dotenv

# Import các pipeline
from data.synthetic_gen import main as sdg_main
from main import main as benchmark_main

async def run_e2e_pipeline():
    """
    Luồng chạy End-to-End:
    1. Đọc cấu hình từ .env
    2. Chạy SDG Agent để sinh 50+ câu hỏi (Gọi Qwen API)
    3. Chạy Multi-Agent Benchmark (V1 vs V2, chấm bởi Strict & Semantic Judges)
    """
    print("=" * 80)
    print("🚀 BẮT ĐẦU E2E BENCHMARK PIPELINE: MULTI-MODEL ARCHITECTURE")
    print("=" * 80)
    
    # BƯỚC 1: NẠP CẤU HÌNH
    print("\n[1/3] Đang nạp cấu hình từ .env...")
    load_dotenv(override=True)
    print(f"  - SDG_MODEL: {os.environ.get('SDG_MODEL', 'Not set')}")
    print(f"  - AGENT_V1_MODEL: {os.environ.get('AGENT_V1_MODEL', 'Not set')}")
    print(f"  - AGENT_V2_MODEL: {os.environ.get('AGENT_V2_MODEL', 'Not set')}")
    print(f"  - JUDGE_STRICT_MODEL: {os.environ.get('JUDGE_STRICT_MODEL', 'Not set')}")
    print(f"  - JUDGE_SEMANTIC_MODEL: {os.environ.get('JUDGE_SEMANTIC_MODEL', 'Not set')}")
    
    # BƯỚC 2: CHẠY SDG AGENT
    print("\n" + "=" * 80)
    print("🤖 [2/3] KÍCH HOẠT SDG AGENT (SYNTHETIC DATA GENERATOR)")
    print("=" * 80)
    start_time = time.time()
    try:
        await sdg_main()
        print(f"\n✅ SDG hoàn tất trong {time.time() - start_time:.2f}s")
    except Exception as e:
        print(f"\n❌ Lỗi khi chạy SDG: {e}")
        return

    # BƯỚC 3: CHẠY BENCHMARK PIPELINE
    print("\n" + "=" * 80)
    print("⚔️ [3/3] KÍCH HOẠT EVALUATION BENCHMARK (V1 vs V2)")
    print("=" * 80)
    start_time = time.time()
    try:
        await benchmark_main()
        print(f"\n✅ Benchmark hoàn tất trong {time.time() - start_time:.2f}s")
    except Exception as e:
        print(f"\n❌ Lỗi khi chạy Benchmark: {e}")
        return

    print("\n" + "=" * 80)
    print("🎉 HOÀN TẤT E2E PIPELINE!")
    print("Bạn có thể xem báo cáo phân tích chi tiết tại thư mục 'reports/'.")
    print("=" * 80)

if __name__ == "__main__":
    os.environ.setdefault("PYTHONUTF8", "1")
    asyncio.run(run_e2e_pipeline())
