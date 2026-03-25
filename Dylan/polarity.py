def check_help_polarity(left_context_tokens, window_size=5):
    """
    Checks if 'help' is negated based on a specific list of negative polarity indicators.
    
    Args:
        left_context_tokens (list): A list of word tokens BEFORE 'help'.
        window_size (int): How many words back to check for negation (defaulting to 5).
        
    Returns:
        str: 'NEG' or 'POS'
    """
    # List of negative polarity indicators from the project instructions; FEEL FREE TO ADD MORE!!!
    negation_words = {
        'not', "n't", 'nor', 'never', 'hardly', 
        'scarcely', 'barely', 'no', 'nobody', 
        'nothing', 'nowhere'
    }
    
    # Isolate the immediate left context based on the window size
    window = left_context_tokens[-window_size:] if len(left_context_tokens) >= window_size else left_context_tokens
    window_lower = [word.lower() for word in window]
    
    # Check if any negation word exists in our target window
    for word in window_lower:
        if word in negation_words:
            return 'NEG'
            
    return 'POS'

# USE THIS TEST TO VERIFY
# Text: "He decided to never help them."
left_tokens_1 = ["He", "decided", "to", "never"]
print(f"Polarity: {check_help_polarity(left_tokens_1)}") 
# Expected: NEG (because 'never' is in the context)

# Text: "But still he decided to help them."
left_tokens_2 = ["But", "still", "he", "decided", "to"]
print(f"Polarity: {check_help_polarity(left_tokens_2)}") 
# Expected: POS (because there are no negation words in the context)