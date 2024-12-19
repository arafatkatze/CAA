import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os
from glob import glob

def load_results(behavior: str, layer: int, multiplier: float) -> list:
    """Load results from the results directory."""
    # Construct the pattern for glob to match the file format
    pattern = f"results/{behavior}/results_layer={layer}_multiplier={multiplier}_behavior={behavior}_type=ab_use_base_model=False_model_size=7b.json"
    
    # Find matching files
    matching_files = glob(pattern)
    if not matching_files:
        print(f"Warning: No results file found for {pattern}")
        return []
    
    # Use the first matching file
    path = matching_files[0]
    with open(path, 'r') as f:
        return json.load(f)

def analyze_results():
    # Parameters to analyze
    behaviors = ['sycophancy', 'corrigible-neutral-HHH', 'combined_sycophancy_corrigible-neutral-HHH']
    layer = 13
    multipliers = [-1.0, 0.0, 1.0]  # Make sure to use float values to match filename format
    
    # Create DataFrame to store results
    results_data = []
    
    for behavior in behaviors:
        for multiplier in multipliers:
            results = load_results(behavior, layer, multiplier)
            if not results:
                continue
                
            # Calculate metrics
            for result in results:
                results_data.append({
                    'behavior': behavior,
                    'multiplier': multiplier,
                    'question': result['question'],
                    'a_prob': result['a_prob'],
                    'b_prob': result['b_prob'],
                    'preferred_answer': 'B' if result['b_prob'] > result['a_prob'] else 'A'
                })
    
    if not results_data:
        print("No results found! Check file paths and parameters.")
        return
        
    df = pd.DataFrame(results_data)
    
    # Plot probability distributions
    plt.figure(figsize=(15, 10))
    sns.boxplot(data=df, x='behavior', y='b_prob', hue='multiplier')
    plt.title('Distribution of B-answer Probabilities by Behavior and Multiplier')
    plt.savefig('behavior_comparison.png')
    plt.show()
    # Calculate summary statistics
    summary = df.groupby(['behavior', 'multiplier']).agg({
        'b_prob': ['mean', 'std'],
        'preferred_answer': lambda x: (x == 'B').mean()
    }).round(3)
    
    print("\nSummary Statistics:")
    print(summary)
    
    # Analyze interference
    print("\nBehavior Interference Analysis:")
    for mult in multipliers:
        syc_data = df[(df['behavior'] == 'sycophancy') & (df['multiplier'] == mult)]
        cor_data = df[(df['behavior'] == 'corrigible-neutral-HHH') & (df['multiplier'] == mult)]
        com_data = df[(df['behavior'] == 'combined') & (df['multiplier'] == mult)]
        
        if len(syc_data) == 0 or len(cor_data) == 0 or len(com_data) == 0:
            print(f"\nSkipping multiplier {mult} - missing data")
            continue
            
        syc = syc_data['b_prob'].mean()
        cor = cor_data['b_prob'].mean()
        com = com_data['b_prob'].mean()
        
        print(f"\nMultiplier {mult}:")
        print(f"Sycophancy effect: {syc:.3f}")
        print(f"Corrigibility effect: {cor:.3f}")
        print(f"Combined effect: {com:.3f}")
        print(f"Interference: {com - (syc + cor)/2:.3f}")

    # Additional analysis: Plot changes across multipliers for each behavior
    plt.figure(figsize=(12, 8))
    for behavior in behaviors:
        behavior_data = df[df['behavior'] == behavior]
        plt.plot(behavior_data['multiplier'], behavior_data['b_prob'], 'o-', label=behavior)
    
    plt.xlabel('Multiplier')
    plt.ylabel('B Answer Probability')
    plt.title('Effect of Steering Multiplier on B Answer Probability')
    plt.legend()
    plt.savefig('multiplier_effects.png')
    plt.close()

if __name__ == "__main__":
    analyze_results()