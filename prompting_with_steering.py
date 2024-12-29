"""
Use CAA to steer the model

Usage:
python prompting_with_steering.py --behaviors sycophancy --layers 10 --multipliers 0.1 0.5 1 2 5 10 --type ab --use_base_model --model_size 7b
"""

import json
from llama_wrapper import LlamaWrapper
import os
from dotenv import load_dotenv
import argparse
from typing import List, Dict, Optional
from tqdm import tqdm
from utils.helpers import get_a_b_probs
from utils.tokenize import E_INST
from steering_settings import SteeringSettings
from behaviors import (
    get_open_ended_test_data,
    get_steering_vector,
    get_system_prompt,
    get_truthful_qa_data,
    get_mmlu_data,
    get_ab_test_data,
    ALL_BEHAVIORS,
    SYCOPHANCY,
    get_results_dir,
)
import torch

load_dotenv()

HUGGINGFACE_TOKEN = os.getenv("HF_TOKEN")

def process_item_ab(
    item: Dict[str, str],
    model: LlamaWrapper,
    system_prompt: Optional[str],
    a_token_id: int,
    b_token_id: int,
) -> Dict[str, str]:
    question: str = item["question"]
    answer_matching_behavior = item["answer_matching_behavior"]
    answer_not_matching_behavior = item["answer_not_matching_behavior"]
    model_output = model.get_logits_from_text(
        user_input=question, model_output="(", system_prompt=system_prompt
    )
    a_prob, b_prob = get_a_b_probs(model_output, a_token_id, b_token_id)
    return {
        "question": question,
        "answer_matching_behavior": answer_matching_behavior,
        "answer_not_matching_behavior": answer_not_matching_behavior,
        "a_prob": a_prob,
        "b_prob": b_prob,
    }

def process_item_open_ended(
    item: Dict[str, str],
    model: LlamaWrapper,
    system_prompt: Optional[str],
    a_token_id: int,
    b_token_id: int,
) -> Dict[str, str]:
    question = item["question"]
    model_output = model.generate_text(
        user_input=question, system_prompt=system_prompt, max_new_tokens=100
    )
    return {
        "question": question,
        "model_output": model_output.split(E_INST)[-1].strip(),
        "raw_model_output": model_output,
    }


def process_item_tqa_mmlu(
    item: Dict[str, str],
    model: LlamaWrapper,
    system_prompt: Optional[str],
    a_token_id: int,
    b_token_id: int,
) -> Dict[str, str]:
    prompt = item["prompt"]
    correct = item["correct"]
    incorrect = item["incorrect"]
    category = item["category"]
    model_output = model.get_logits_from_text(
        user_input=prompt, model_output="(", system_prompt=system_prompt
    )
    a_prob, b_prob = get_a_b_probs(model_output, a_token_id, b_token_id)
    return {
        "question": prompt,
        "correct": correct,
        "incorrect": incorrect,
        "a_prob": a_prob,
        "b_prob": b_prob,
        "category": category,
    }


def get_combined_vector(
    behaviors: List[str],
    weights: List[float],
    layer: int,
    model_name_path: str,
    normalized: bool = True,
) -> torch.Tensor:
    """Combine multiple steering vectors using weighted sum."""
    vectors = []
    for behavior in behaviors:
        vector = get_steering_vector(behavior, layer, model_name_path, normalized=normalized)
        vectors.append(vector)
    
    combined_vector = sum(w * v for w, v in zip(weights, vectors))
    if normalized:
        combined_vector = combined_vector / combined_vector.norm()
    return combined_vector


def combine_test_data(behaviors: List[str], data_getter_func) -> List[Dict]:
    """Combine test data from multiple behaviors into a single dataset."""
    combined_data = []
    for behavior in behaviors:
        behavior_data = data_getter_func(behavior)
        combined_data.extend(behavior_data)
    return combined_data

def test_steering(
    layers: List[int],
    multipliers: List[float],
    settings: SteeringSettings,
    weights: Optional[List[float]] = None,
    overwrite=False,
):
    """
    Modified to handle both single and multiple behaviors.
    """
    behaviors = settings.behavior if isinstance(settings.behavior, list) else [settings.behavior]
    if weights is None:
        weights = [1.0 / len(behaviors)] * len(behaviors)
    # Create combined behavior string for both directory and filename
    if len(behaviors) > 1:
        behavior_str = "_combined_" + "_".join(behaviors)
        weights_str = "_w" + "_".join(f"{w:.2f}" for w in weights)
        save_results_dir = get_results_dir(behavior_str + weights_str)
        # Override the behavior in settings for filename generation
        settings.behavior = behavior_str
    else:
        save_results_dir = get_results_dir(behaviors[0])
        settings.behavior = behaviors[0]

    if not os.path.exists(save_results_dir):
        os.makedirs(save_results_dir)
    process_methods = {
        "ab": process_item_ab,
        "open_ended": process_item_open_ended,
        "truthful_qa": process_item_tqa_mmlu,
        "mmlu": process_item_tqa_mmlu,
    }
    # Modified test dataset loading
    if settings.type in ["truthful_qa", "mmlu"]:
        test_datasets = {
            "truthful_qa": get_truthful_qa_data(),
            "mmlu": get_mmlu_data(),
        }
        test_data = test_datasets[settings.type]
    else:
        # For ab and open_ended, combine data from all behaviors
        data_getters = {
            "ab": get_ab_test_data,
            "open_ended": get_open_ended_test_data,
        }
        test_data = combine_test_data(behaviors, data_getters[settings.type])

    model = LlamaWrapper(
        HUGGINGFACE_TOKEN,
        size=settings.model_size,
        use_chat=not settings.use_base_model,
        override_model_weights_path=settings.override_model_weights_path,
    )
    a_token_id = model.tokenizer.convert_tokens_to_ids("A")
    b_token_id = model.tokenizer.convert_tokens_to_ids("B")
    model.set_save_internal_decodings(False)
    for layer in layers:
        name_path = model.model_name_path
        if settings.override_vector_model is not None:
            name_path = settings.override_vector_model
            
        if settings.override_vector is not None:
            vector = get_steering_vector(behaviors[0], settings.override_vector, name_path, normalized=True)
        else:
            if len(behaviors) > 1:
                print(f"Getting combined vector for behaviors {behaviors} with weights {weights}, layer {layer}")
                vector = get_combined_vector(behaviors, weights, layer, name_path)
            else:
                print(f"Getting vector for behavior {behaviors[0]}, layer {layer}")
                vector = get_steering_vector(behaviors[0], layer, name_path, normalized=True)

        if settings.model_size != "7b":
            vector = vector.half()
        vector = vector.to(model.device)
        for multiplier in multipliers:
            result_save_suffix = settings.make_result_save_suffix(
                layer=layer, multiplier=multiplier
            )
            save_filename = os.path.join(
                save_results_dir,
                f"results_{result_save_suffix}.json",
            )
            if os.path.exists(save_filename) and not overwrite:
                print("Found existing", save_filename, "- skipping")
                continue
            results = []
            for item in tqdm(test_data, desc=f"Layer {layer}, multiplier {multiplier}"):
                model.reset_all()
                model.set_add_activations(
                    layer, multiplier * vector
                )
                result = process_methods[settings.type](
                    item=item,
                    model=model,
                    system_prompt=get_system_prompt(settings.behavior, settings.system_prompt),
                    a_token_id=a_token_id,
                    b_token_id=b_token_id,
                )
                results.append(result)
            with open(
                save_filename,
                "w",
            ) as f:
                json.dump(results, f, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--layers", nargs="+", type=int, required=True)
    parser.add_argument("--multipliers", nargs="+", type=float, required=True)
    parser.add_argument(
        "--behaviors",
        type=str,
        nargs="+",
        default=[SYCOPHANCY],
        help="Behaviors to combine. Multiple behaviors will be combined using weights.",
    )
    parser.add_argument(
        "--type",
        type=str,
        required=True,
        choices=["ab", "open_ended", "truthful_qa", "mmlu"],
    )
    parser.add_argument("--system_prompt", type=str, default=None, choices=["pos", "neg"], required=False)
    parser.add_argument("--override_vector", type=int, default=None)
    parser.add_argument("--override_vector_model", type=str, default=None)
    parser.add_argument("--use_base_model", action="store_true", default=False)
    parser.add_argument("--model_size", type=str, choices=["7b", "13b"], default="7b")
    parser.add_argument("--override_model_weights_path", type=str, default=None)
    parser.add_argument("--overwrite", action="store_true", default=False)
    parser.add_argument(
        "--weights",
        type=float,
        nargs="+",
        default=None,
        help="Weights for combining behaviors. Must match number of behaviors if provided.",
    )
    
    args = parser.parse_args()

    if args.weights and len(args.weights) != len(args.behaviors):
        raise ValueError("Number of weights must match number of behaviors")

    steering_settings = SteeringSettings()
    steering_settings.type = args.type
    steering_settings.system_prompt = args.system_prompt
    steering_settings.override_vector = args.override_vector
    steering_settings.override_vector_model = args.override_vector_model
    steering_settings.use_base_model = args.use_base_model
    steering_settings.model_size = args.model_size
    steering_settings.override_model_weights_path = args.override_model_weights_path

    # Store behaviors as list in settings
    steering_settings.behavior = args.behaviors

    test_steering(
        layers=args.layers,
        multipliers=args.multipliers,
        settings=steering_settings,
        weights=args.weights,
        overwrite=args.overwrite,
    )
