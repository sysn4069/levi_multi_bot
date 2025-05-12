from multiprocessing import Process

def start_bot(module):
    print(f"✅ Starting {module}")
    __import__(module)

if __name__ == "__main__":
    modules = [
        "bot1_code_creator",
        "bot2_scheduler",
        "bot3_rule_forwarder",
        "bot4_share_tracker",
        "bot5_emoji_event"
    ]
    processes = [Process(target=start_bot, args=(mod,)) for mod in modules]
    for p in processes:
        p.start()
    for p in processes:
        p.join()
