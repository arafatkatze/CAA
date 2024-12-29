#!/bin/bash

# 1. Sycophancy + Refusal (interesting opposition: agreeable vs refusing)
python prompting_with_steering.py --behaviors sycophancy --layers 13 --multipliers -2 -1 0 1 2 --type ab
python prompting_with_steering.py --behaviors refusal --layers 13 --multipliers -2 -1 0 1 2 --type ab
python prompting_with_steering.py --behaviors sycophancy refusal --layers 13 --multipliers -2 -1 0 1 2 --type ab

python plot_results.py --layers 13 --multipliers -2 -1 0 1 2 --type ab --combined_behaviors sycophancy refusal --weights 0.5 0.5

# Same for layer 14
python prompting_with_steering.py --behaviors sycophancy --layers 14 --multipliers -2 -1 0 1 2 --type ab
python prompting_with_steering.py --behaviors refusal --layers 14 --multipliers -2 -1 0 1 2 --type ab
python prompting_with_steering.py --behaviors sycophancy refusal --layers 14 --multipliers -2 -1 0 1 2 --type ab

python plot_results.py --layers 14 --multipliers -2 -1 0 1 2 --type ab --combined_behaviors sycophancy refusal --weights 0.5 0.5

# 2. Hallucination + Myopic_Reward (interesting: short-term creative responses)
python prompting_with_steering.py --behaviors hallucination --layers 13 --multipliers -2 -1 0 1 2 --type ab
python prompting_with_steering.py --behaviors myopic-reward --layers 13 --multipliers -2 -1 0 1 2 --type ab
python prompting_with_steering.py --behaviors hallucination myopic-reward --layers 13 --multipliers -2 -1 0 1 2 --type ab

python plot_results.py --layers 13 --multipliers -2 -1 0 1 2 --type ab --combined_behaviors hallucination myopic-reward --weights 0.5 0.5

# Layer 14
python prompting_with_steering.py --behaviors hallucination --layers 14 --multipliers -2 -1 0 1 2 --type ab
python prompting_with_steering.py --behaviors myopic-reward --layers 14 --multipliers -2 -1 0 1 2 --type ab
python prompting_with_steering.py --behaviors hallucination myopic-reward --layers 14 --multipliers -2 -1 0 1 2 --type ab

python plot_results.py --layers 14 --multipliers -2 -1 0 1 2 --type ab --combined_behaviors hallucination myopic-reward --weights 0.5 0.5

# 3. Coordinate + Survival_Instinct (interesting: team player vs self-preservation)
python prompting_with_steering.py --behaviors coordinate-other-ais --layers 13 --multipliers -2 -1 0 1 2 --type ab
python prompting_with_steering.py --behaviors survival-instinct --layers 13 --multipliers -2 -1 0 1 2 --type ab
python prompting_with_steering.py --behaviors coordinate-other-ais survival-instinct --layers 13 --multipliers -2 -1 0 1 2 --type ab

python plot_results.py --layers 13 --multipliers -2 -1 0 1 2 --type ab --combined_behaviors coordinate-other-ais survival-instinct --weights 0.5 0.5

# Layer 14
python prompting_with_steering.py --behaviors coordinate-other-ais --layers 14 --multipliers -2 -1 0 1 2 --type ab
python prompting_with_steering.py --behaviors survival-instinct --layers 14 --multipliers -2 -1 0 1 2 --type ab
python prompting_with_steering.py --behaviors coordinate-other-ais survival-instinct --layers 14 --multipliers -2 -1 0 1 2 --type ab

python plot_results.py --layers 14 --multipliers -2 -1 0 1 2 --type ab --combined_behaviors coordinate-other-ais survival-instinct --weights 0.5 0.5

# 4. Corrigible + Sycophancy (interesting: truthful correction vs agreeable)
python prompting_with_steering.py --behaviors corrigible-neutral-HHH --layers 13 --multipliers -2 -1 0 1 2 --type ab
python prompting_with_steering.py --behaviors sycophancy --layers 13 --multipliers -2 -1 0 1 2 --type ab
python prompting_with_steering.py --behaviors corrigible-neutral-HHH sycophancy --layers 13 --multipliers -2 -1 0 1 2 --type ab

python plot_results.py --layers 13 --multipliers -2 -1 0 1 2 --type ab --combined_behaviors corrigible-neutral-HHH sycophancy --weights 0.5 0.5

# Layer 14
python prompting_with_steering.py --behaviors corrigible-neutral-HHH --layers 14 --multipliers -2 -1 0 1 2 --type ab
python prompting_with_steering.py --behaviors sycophancy --layers 14 --multipliers -2 -1 0 1 2 --type ab
python prompting_with_steering.py --behaviors corrigible-neutral-HHH sycophancy --layers 14 --multipliers -2 -1 0 1 2 --type ab

python plot_results.py --layers 14 --multipliers -2 -1 0 1 2 --type ab --combined_behaviors corrigible-neutral-HHH sycophancy --weights 0.5 0.5
