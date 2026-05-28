import json
import requests

BASE = "http://127.0.0.1:8000"

sample_jsonl = """
{"task_type":"dialect_generation","input_text":"നീ ഇന്ന് വീട്ടിലാണോ?","output_text":"ഇഞ്ഞി ഇന്ന് വീട്ടിലാണോ?","dialect":"Kannur / North Malabar","tone":"casual","domain":"daily_conversation"}
{"task_type":"dialect_normalization","input_text":"ഇഞ്ഞി എവിടെയാ പോണേ?","output_text":"നീ എവിടേക്ക് പോകുകയാണ്?","dialect":"Kannur / North Malabar","tone":"casual","domain":"daily_conversation"}
""".strip()


def main() -> None:
    r = requests.post(
        f"{BASE}/synthetic/ingest-jsonl",
        json={"jsonl_text": sample_jsonl, "store_invalid": False},
        timeout=30,
    )
    print(r.status_code)
    print(json.dumps(r.json(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
