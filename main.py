from multiprocessing import Process
import importlib

def run_bot(module_name):
    print(f"✅ Starting {module_name}")
    module = importlib.import_module(module_name)
    module.safe_main()

if __name__ == "__main__":
    modules = [
        "bot1_code_creator",
        "bot2_scheduler",
        "bot3_rule_forwarder",
        "bot4_share_tracker",
        "bot5_emoji_event"
    ]
    processes = [Process(target=run_bot, args=(m,)) for m in modules]
    for p in processes:
        p.start()
    for p in processes:
        p.join()
