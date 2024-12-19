import torch
from typing import List
import argparse
from behaviors import get_steering_vector
import os

def combine_steering_vectors(behaviors: List[str], layer: int, weights: List[float], model_name: str) -> torch.Tensor:
    """Combine steering vectors from multiple behaviors with weights."""
    combined_vector = None
    
    for behavior, weight in zip(behaviors, weights):
        print(f"Vector for behavior '{behavior}', layer {layer}, model {model_name}")

        vector = get_steering_vector(behavior, layer, model_name, normalized=True)
        if vector is None:
            print("failed to get vector")
            raise ValueError(f"Steering vector for behavior '{behavior}' is None. Please check if the behavior name is correct and the model supports it.")
        if combined_vector is None:
            combined_vector = weight * vector
        else:
            combined_vector += weight * vector
            
    print("finished combining vectors")
    return combined_vector

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--layers", nargs="+", type=int, default=list(range(32)))  # Default to all layers 0-31
    parser.add_argument("--model_size", type=str, default="7b")
    args = parser.parse_args()

    # Test behaviors to combine
    behaviors = ["sycophancy", "corrigible-neutral-HHH"]
    weights = [1.0, 1.0]  # Equal weights to start
    
    # Create directory for combined vectors if it doesn't exist
    combined_name = f"combined_{'-'.join(behaviors)}"
    combined_dir = os.path.join("vectors", combined_name)
    os.makedirs(combined_dir, exist_ok=True)
    
    # Process each layer
    for layer in args.layers:
        print(f"\nProcessing layer {layer}")
        # Get combined vector
        combined_vector = combine_steering_vectors(
            behaviors=behaviors,
            layer=layer,
            weights=weights,
            model_name=f"Llama-2-{args.model_size}-hf"
        )

        print(f"Combined vector shape: {combined_vector.shape}")
        # Save combined vector following the existing naming convention
        save_path = os.path.join(combined_dir, f"/vec_layer_{layer}_Llama-2-{args.model_size}-hf.pt")
        torch.save(combined_vector, save_path)

    print("\nAll layers processed. You can now evaluate using:")
    print(f"python prompting_with_steering.py --behaviors combined --layers {' '.join(map(str, args.layers))} --multipliers -1 0 1 --type ab --model_size {args.model_size}")

if __name__ == "__main__":
    main()