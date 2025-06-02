# text cutoff fix

fixed the issue where dialogue text was getting cut off in bubbles

## what got fixed

- better text size calculation using PIL
- bubbles now resize automatically to fit text
- added safety margins so text doesn't touch edges
- improved text wrapping for long dialogue
- debug overlays to see what's happening

## testing

tested with short, medium, and long dialogue. text cutoff issues are mostly fixed now.

## usage

```bash
# test the fix
python scripts/test_dialogue_patch.py
```

the debug overlays show green boxes for bubbles and blue for text areas so you can see if things fit properly.
