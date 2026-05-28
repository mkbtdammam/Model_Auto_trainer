from app.models import TaskType
from app.synthetic_generator import build_generation_prompt, parse_jsonl_candidates, validate_candidates


sample_jsonl = """
{"task_type":"dialect_generation","input_text":"നീ ഇന്ന് വീട്ടിലാണോ?","output_text":"ഇഞ്ഞി ഇന്ന് വീട്ടിലാണോ?","dialect":"Kannur / North Malabar","tone":"casual","domain":"daily_conversation"}
{"task_type":"translation_en","input_text":"ഇഞ്ഞി ചായ കുടിച്ചോ?","output_text":"Did you drink tea?","dialect":"Kannur / North Malabar","tone":"casual","domain":"daily_conversation"}
""".strip()


def main() -> None:
    prompt = build_generation_prompt(TaskType.dialect_generation, "നീ ഇന്ന് വീട്ടിലാണോ?", 5)
    print("PROMPT:")
    print(prompt)
    print("\nVALIDATION:")
    candidates = parse_jsonl_candidates(sample_jsonl)
    results = validate_candidates(candidates)
    for result in results:
        print(result["quality_score"], result["validation_errors"], result["ready_for_review"])


if __name__ == "__main__":
    main()
