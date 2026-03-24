def check_preceding_to(left_context_tokens, is_help_verb=True):
    """
    Checks if 'to' appears within the 2 words immediately preceding 'help'.

    Args:
        left_context_tokens (list): A list of word tokens BEFORE 'help'.
                                    Expected in normal reading order (e.g., ['I', 'want', 'to', 'never']).
        is_help_verb (bool): Boolean indicating if 'help' is functioning as a verb in this instance.
        
    Returns:
        str: 'YEStoBefore', 'NOtoBefore', or 'NA'
    """
    # If help does not function as a verb, code this as 'NA'
    if not is_help_verb:
        return 'NA'
        
    # Consider 2 words to the left of help
    # Grab the last 2 tokens from the left context
    window = left_context_tokens[-2:] if len(left_context_tokens) >= 2 else left_context_tokens

    # Convert to lowercase to ensure we catch 'To' or 'TO'
    window_lower = [word.lower() for word in window]

    if 'to' in window_lower:
        return 'YEStoBefore'
    else:
        return 'NOtoBefore'


    # USE THIS TEST TO VERIFY
# Text: "He decided to never help them."
left_tokens_1 = ["He", "decided", "to", "never"]
print(f"Preceding 'to': {check_preceding_to(left_tokens_1, is_help_verb=True)}") 
# Expected: YEStoBefore (because 'to' is within the last 2 words: ['to', 'never'])

# Text: "To start his business, his friend helped him."
left_tokens_2 = ["To", "start", "his", "business", "his", "friend"]
print(f"Preceding 'to': {check_preceding_to(left_tokens_2, is_help_verb=True)}") 
# Expected: NOtoBefore (because 'to' is not within the last 2 words: ['his', 'friend'])

# Text: "He wanted his help to be appreciated."
left_tokens_3 = ["He", "wanted", "his"]
print(f"Preceding 'to': {check_preceding_to(left_tokens_3, is_help_verb=False)}")
# Expected: NA (because 'help' is not functioning as a verb in this instance)