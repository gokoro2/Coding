import pandas as pd
import numpy as np
from scipy.stats import spearmanr
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import rcParams

# Global font properties for plots
rcParams['font.family'] = 'Times New Roman'

# File paths and load data
file_path = r'C:\(file).xlsx'
data = pd.read_excel(file_path, sheet_name="Sheet3")

# Define Thresholds
cov_threshold = 10  # Coefficient of Variation (CoV) threshold in percentage
spearman_threshold = 0.30  # Weak Spearman's rank correlation threshold
iqr_threshold = 0.10  # Interquartile Range (IQR) threshold
lvi_threshold = 0.05  # Longitudinal Variability Index (LVI) threshold in percentage

# Calculate IQR
def calculate_iqr(values):
    return np.percentile(values, 75) - np.percentile(values, 25)

# Visualization with highlighted qualified features
def plot_step(data, qualified_features, title, xlabel, ylabel, threshold=None,
              title_fontsize=16, label_fontsize=16, tick_fontsize=10):
    plt.figure(figsize=(12, 8))
    bar_colors = ['green' if feature in qualified_features else 'skyblue' for feature in data['Feature']]
    sns.barplot(data=data, x='Feature', y='Value', palette=bar_colors)
    
    # Plot threshold line 
    if threshold is not None:
        plt.axhline(y=threshold, color='red', linestyle='--', label='Threshold')
    
    plt.title(title, fontsize=title_fontsize)
    plt.xlabel(xlabel, fontsize=label_fontsize)
    plt.ylabel(ylabel, fontsize=label_fontsize)
    plt.xticks(rotation=90, fontsize=tick_fontsize)
    plt.yticks(fontsize=tick_fontsize)
    plt.legend(fontsize=label_fontsize)
    plt.tight_layout()
    plt.show()

# Normalization, threshold checks, and LVI calculation
def normalize_check_and_lvi(alpha):
    normalized_columns = {}
    stats = {
        'Feature': [], 'Original CoV': [], 'Normalized CoV': [],
        'Original Spearman': [], 'Normalized Spearman': [],
        'Original IQR': [], 'Normalized IQR': [], 'LVI': []
    }
    qualified_features = []

    # Normalize features by Tumor Volume raised to power alpha
    for col in data.columns[2:]:
        normalized_columns[col] = data[col] / (data['Tumor Volume'] ** alpha)
    normalized_features = pd.DataFrame(normalized_columns)

    # Analyze each feature
    for feature in normalized_features.columns:
        original_cov = (data[feature].std() / data[feature].mean()) * 100
        normalized_cov = (normalized_features[feature].std() / normalized_features[feature].mean()) * 100
        original_corr, _ = spearmanr(data[feature], data['Tumor Volume'])
        normalized_corr, _ = spearmanr(normalized_features[feature], data['Tumor Volume'])
        original_iqr = calculate_iqr(data[feature])
        normalized_iqr = calculate_iqr(normalized_features[feature])
        
        stats['Feature'].append(feature)
        stats['Original CoV'].append(original_cov)
        stats['Normalized CoV'].append(normalized_cov)
        stats['Original Spearman'].append(abs(original_corr))
        stats['Normalized Spearman'].append(abs(normalized_corr))
        stats['Original IQR'].append(original_iqr)
        stats['Normalized IQR'].append(normalized_iqr)
        stats['LVI'].append(None)  # Placeholder for LVI

        # Check if feature meets all thresholds
        if (normalized_cov <= cov_threshold and 
            abs(normalized_corr) <= spearman_threshold and 
            normalized_iqr <= iqr_threshold):
            qualified_features.append(feature)
    
    # Calculate LVI for qualified features
    final_features = []
    for feature in qualified_features:
        lvi = (normalized_features[feature].std() / normalized_features[feature].mean()) * 100
        stats['LVI'][stats['Feature'].index(feature)] = lvi
        if lvi <= lvi_threshold * 100:
            final_features.append(feature)
    
    return final_features, normalized_features, pd.DataFrame(stats)

# Iterate over alpha values to find optimal normalization
for alpha in np.arange(0.01, 100.01, 0.01):
    final_features, normalized_features, stats = normalize_check_and_lvi(alpha)
    if final_features:
        print(f"\nOptimal alpha found: {alpha}")
        print(f"Features meeting all criteria:\n{final_features}")

        # Visualization of metrics
        metrics = {
            'CoV': ('Normalized CoV', cov_threshold),
            'Spearman': ('Normalized Spearman', spearman_threshold),
            'IQR': ('Normalized IQR', iqr_threshold),
            'LVI': ('LVI', lvi_threshold * 100)
        }
        for metric, (col, threshold) in metrics.items():
            plot_step(stats[['Feature', col]].rename(columns={col: 'Value'}),
                      qualified_features=final_features,
                      title=f'{metric} for All Features',
                      xlabel='Feature', ylabel=metric,
                      threshold=threshold)

        # Save qualified features to Excel
        output_data = pd.DataFrame({
            'Tumor ID': data['Tumor ID'],
            'Tumor Volume': data['Tumor Volume']
        })
        for feature in final_features:
            output_data[f'{feature}_Original'] = data[feature]
            output_data[f'{feature}_Normalized'] = normalized_features[feature]
        
        output_data.to_excel(r'C:\Users\Admin\Desktop\test code\Qualified_Features.xlsx', index=False)
        stats.to_excel(r'C:\Users\Admin\Desktop\test code\Feature_Stats.xlsx', index=False)
        break

# Combine and save all features
original_features = data.iloc[:, 2:].add_suffix('_Original')
normalized_features_renamed = normalized_features.add_suffix('_Normalized')
output_all_features = pd.concat([data[['Tumor ID', 'Tumor Volume']],
                                  original_features,
                                  normalized_features_renamed], axis=1)
output_all_features.to_excel(r'C:\Users\Admin\Desktop\test code\All_Features.xlsx', index=False)

# Plot correlations of selected features
correlation_data = {
    'Feature': final_features,
    'Original Correlation': [spearmanr(data['Tumor Volume'], data[feature])[0] for feature in final_features],
    'Normalized Correlation': [spearmanr(data['Tumor Volume'], normalized_features[feature])[0] for feature in final_features]
}
correlation_df = pd.DataFrame(correlation_data)
correlation_df.set_index('Feature').plot(kind='bar', colormap='Dark2', alpha=0.8, figsize=(12, 6))
plt.title('Tumor Volume/Feature Correlation', fontsize=14)
plt.xlabel('Feature', fontsize=12)
plt.ylabel('Spearman Correlation Coefficient', fontsize=12)
plt.xticks(rotation=90, fontsize=10)
plt.tight_layout()
plt.show()
