import pandas as pd
import os
import re


import time  # Add this import
 
# Start timer
start_time = time.time()

hansard_dir = "./Hansard100kSample"
file_rewrite = "Further_analysis/Hansard_done.csv"
help_analysed = pd.read_csv("Further_analysis/Hansard_Complete_100k(in).csv", encoding="latin1")  # Go up one level

# Build a dictionary mapping
file_mapping = {}
for file in os.listdir(hansard_dir):
    if file.endswith('.txt'):
        file_id = file.split('_')[0]  # Extract numeric part before first underscore
        file_mapping[file_id] = file



for index,row in help_analysed.iterrows():
    file_id = str(row["FileId"]).zfill(7)
    left_context = row['LeftContext']
    with open(hansard_dir + "/" + file_mapping[file_id]) as f:
        content = f"{f.read()}" 
        content = content.split('\n')
        text_content = left_context
        for line in content:
            if text_content in line:
                # Extract speaker name (text before the first colon)
                speaker_match = re.search(r'<speaker>(.*?)</speaker>', line)
                if speaker_match:
                    help_analysed.at[index, 'Speaker'] = speaker_match.group(1)
                break

# Save results
help_analysed.to_csv(file_rewrite, index=False, encoding='utf-8')
 
# Calculate and display elapsed time
end_time = time.time()
elapsed_time = end_time - start_time
print(f"Processing completed in {elapsed_time:.2f} seconds")
print(f"Processed {len(help_analysed)} rows")
print(f"Average time per row: {elapsed_time/len(help_analysed):.4f} seconds")