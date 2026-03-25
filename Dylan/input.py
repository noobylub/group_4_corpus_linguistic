import os
import re
import pandas as pd
import xml.etree.ElementTree as ET

# This cell adds all the context of the word "help" from all Hansard files
# Directory containing all Hansard files
hansard_dir = "/Users/muhammadmushoffa/Desktop/corpus_linguistic/Hansard 2000 file sample"

def extract_from_all_files(directory, word_list):
    """Iterate through all .txt files in directory and extract word context"""
    output_file = f"/Users/muhammadmushoffa/Desktop/corpus_linguistic/help_complete_lubbil.csv"
    
    # Convert word list to lowercase once (moved outside loop)
    word_list_lower = [word.lower() for word in word_list]
    
    with open(output_file, 'w', encoding='utf-8') as outf:
        df = pd.DataFrame(columns=['left_context', 'target_word', 'right_context'])
        total_matches = 0
        
        for filename in sorted(os.listdir(directory)):
            if filename.endswith('.txt'):
                file_path = os.path.join(directory, filename)
                
                # Read the file 
                with open(file_path, 'r', encoding='utf-8') as f:
                    contents = f.read()
                
                parts = re.split(r"\n\s*\n", contents, maxsplit=1)
               
                
                contents = parts[1]
                metadata = parts[0]
                print(len(contents))
                print(len(metadata) == len(contents))

                
                

                # Extracing KWIC 
                contents = contents.replace('<speaker>', '')
                contents = contents.replace('</speaker>', '')
                # print(contents)
                contents = contents.split()
