import pandas as pd

# Example annotation functions
def polarity_annotator(text):
    """Annotate polarity based on text patterns"""
    text_lower = text.lower()
    if any(p in text_lower for p in ['cannot help','help thinking','help feeling']):
        return 'neutral'
    elif any(p in text_lower for p in ['help the poor','help them','help to evolve','done much to help']):
        return 'positive'
    elif any(p in text_lower for p in ['help themselves','help him','helped themselves']):
        return 'negative'
    elif any(w in text_lower for w in ['helpful','helping']):
        return 'positive'
    else:
        return 'neutral'

def urgency_annotator(text):
    """Annotate urgency based on text patterns"""
    text_lower = text.lower()
    if any(u in text_lower for u in ['must','urgent','immediately','essential']):
        return 'high'
    elif any(u in text_lower for u in ['should','would','hope','ought']):
        return 'medium'
    else:
        return 'low'

def speaker_annotator(text):
    """Annotate speaker role based on text patterns"""
    text_lower = text.lower()
    if any(g in text_lower for g in ['government','her majesty','lord advocate','minister']):
        return 'government'
    elif any(o in text_lower for o in ['opposition','noble earl','hon. member','motion']):
        return 'opposition'
    else:
        return 'other'

def create_and_annotate_table(input_file, output_file, polarity_func, urgency_func, speaker_func):
    """Create and auto-annotate help instances table"""
    
    # Read and extract contexts
    with open(input_file, 'r', encoding='utf-8') as f:
        contexts = [line.strip().replace('...', '') 
                   for line in f.readlines()[3:] 
                   if line.strip().startswith('...')]
    
    # Create DataFrame
    df = pd.DataFrame({
        'instance_id': range(1, len(contexts) + 1),
        'context': contexts,
        'target_word': [next((w for w in ['help','helpful','helping','helped'] 
                            if w in ctx.lower().split()), 'unknown') for ctx in contexts]
    })
    
    # Auto-annotate using passed functions
    df['polarity'] = df['context'].apply(polarity_func)
    df['urgency'] = df['context'].apply(urgency_func)
    df['speaker_role'] = df['context'].apply(speaker_func)
    
    # Save and show stats
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"Auto-annotated table with {len(df)} instances saved to: {output_file}")
    
    print("\nAnnotation Statistics:")
    print(f"Polarity: {df['polarity'].value_counts().to_dict()}")
    print(f"Urgency: {df['urgency'].value_counts().to_dict()}")
    print(f"Speaker: {df['speaker_role'].value_counts().to_dict()}")
    
    return df

if __name__ == "__main__":
    create_and_annotate_table(
        "/Users/muhammadmushoffa/Desktop/corpus_linguistic/help_all_files.txt",
        "/Users/muhammadmushoffa/Desktop/corpus_linguistic/help_annotation_auto.csv",
        polarity_annotator,
        urgency_annotator,
        speaker_annotator
    )
