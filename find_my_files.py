import os

print("\n--- FILE DETECTIVE ---")
# 1. Where are we running from?
current_dir = os.getcwd()
print(f"1. Python is running inside: {current_dir}")

# 2. Does the templates folder exist?
templates_path = os.path.join(current_dir, 'templates')
if os.path.exists(templates_path):
    print("2. ✅ 'templates' folder FOUND.")
    
    # 3. Does index.html exist inside it?
    index_path = os.path.join(templates_path, 'index.html')
    if os.path.exists(index_path):
        print("3. ✅ 'index.html' FOUND inside templates.")
    else:
        print("3. ❌ 'index.html' is MISSING from the templates folder.")
        print(f"   (Python looked here: {index_path})")
        print("   -> Did you accidentally name it 'index.html.txt'?")
        print("   -> Did you put it in the main folder instead?")

    # 4. Check for layout.html
    layout_path = os.path.join(templates_path, 'layout.html')
    if os.path.exists(layout_path):
        print("4. ✅ 'layout.html' FOUND.")
    else:
        print("4. ❌ 'layout.html' is MISSING.")
else:
    print("2. ❌ 'templates' folder NOT found. Flask has nowhere to look!")

print("----------------------\n")