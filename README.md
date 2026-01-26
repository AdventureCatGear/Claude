# FinOps Best Practices Slide Animations

This repository provides tools to add click-triggered animations to a FinOps Best Practices PowerPoint slide, highlighting each of the four sections in sequence:

1. **Visibility** (Click 1)
2. **Optimize** (Click 2)
3. **Collaborate** (Click 3)
4. **Automate** (Click 4)

## Animation Effect

Each click highlights the corresponding section with:
- Color fill change (white to blue)
- Subtle scale/grow emphasis
- Text color change for the label

## Options

### Option 1: Python Script (Generate New Slide)

Use `create_finops_slide.py` to generate a complete PowerPoint file with animations pre-configured.

```bash
# Install dependencies
pip install -r requirements.txt

# Generate the slide
python create_finops_slide.py
```

This creates `finops_best_practices.pptx` with all animations ready.

### Option 2: VBA Macro (Modify Existing Slide)

Use `add_animations.vba` to add animations to an existing PowerPoint slide.

**Steps:**
1. Open your PowerPoint presentation
2. Press `Alt+F11` to open VBA Editor
3. Insert > Module
4. Paste the code from `add_animations.vba`
5. Select your FinOps slide
6. Run `AddFinOpsAnimations` macro

**Available macros:**
- `AddFinOpsAnimations` - Finds shapes by name and adds animations
- `AddAnimationsToSelectedShapes` - Select shapes in order, then run
- `AddSimpleHighlightAnimations` - Quick fade-in for all shapes

### Option 3: Manual Animation in PowerPoint

1. Select the **Visibility** cloud/icon shape
2. Go to **Animations** tab
3. Add **Emphasis > Pulse** or **Emphasis > Grow/Shrink**
4. Set trigger to **On Click**
5. Repeat for Optimize, Collaborate, Automate in order

**Pro tip:** Use the Animation Pane (`Alt+Shift+F5`) to reorder and fine-tune.

## Animation Sequence

| Click | Section | Effect |
|-------|---------|--------|
| 1 | Visibility | Highlight with blue fill, scale up |
| 2 | Optimize | Highlight with blue fill, scale up |
| 3 | Collaborate | Highlight with blue fill, scale up |
| 4 | Automate | Highlight with blue fill, scale up |

## Files

- `create_finops_slide.py` - Python script to generate complete PPTX
- `add_animations.vba` - VBA macros for existing presentations
- `requirements.txt` - Python dependencies
