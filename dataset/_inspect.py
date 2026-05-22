import csv, os

csv_path = r"d:\Desktop\ASAAP\dataset\urban\UrbanSound8K.csv"
rows = list(csv.DictReader(open(csv_path)))
print("Columns:", list(rows[0].keys()))
print("Total samples:", len(rows))

classes = {}
for r in rows:
    c = r["class"]
    cid = r["classID"]
    classes[c] = (classes.get(c, (0, cid))[0] + 1, cid)

print("\nClass distribution:")
for name, (count, cid) in sorted(classes.items()):
    print(f"  classID={cid} | {name}: {count} samples")

# Check a fold
fold1 = os.listdir(r"d:\Desktop\ASAAP\dataset\urban\fold1")
print(f"\nFold1 files: {len(fold1)} (sample: {fold1[:3]})")
